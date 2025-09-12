# energy/mqtt/manager.py
import json
import logging
import threading
import time
from collections import deque
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from django.core.cache import cache
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from core.main_models import Plant

from ..devices.base.device import BaseDevice, MeasurementData
from ..devices.registry import DeviceRegistry
from ..models import DeviceConfiguration, DeviceMeasurement, DeviceMeasurementDetail
from .core import MQTTMessage, TopicMatcher, get_mqtt_service
from .event_bus import Event, get_event_bus
from .handlers.device import DeviceHandler
from .handlers.measurement import MeasurementHandler
from .router import get_mqtt_router

logger = logging.getLogger("energy.mqtt")


class DeviceManager:
    """Gestore dei dispositivi e delle loro misurazioni - Event-driven architecture"""

    def __init__(self):
        # Inizializzazione thread safety
        self._lock = threading.Lock()

        # Inizializzazione stati
        self._configs_loaded = False
        self._topic_stats = {}
        self._active_topics = set()

        # Servizi e registry
        self._mqtt_service = get_mqtt_service()
        self._device_registry = DeviceRegistry()
        self._event_bus = get_event_bus()

        # Event-driven handlers
        self._device_handler = DeviceHandler()
        self._measurement_handler = MeasurementHandler()

        # Collections e cache
        self._devices = {}
        self._configs = {}
        self._last_energy_values = {}
        self._message_buffer = deque(maxlen=1000)
        self._cache_timeout = 3600

        # Caricamento configurazioni e setup event-driven handlers
        with self._lock:
            self._load_configurations()
            self._setup_event_handlers()

    def _is_duplicate(self, device_id: str, timestamp: datetime) -> bool:
        """Verifica duplicati con cache"""
        cache_key = f"last_msg_{device_id}"
        last_timestamp = cache.get(cache_key)

        if last_timestamp:
            time_diff = (timestamp - last_timestamp).total_seconds()
            if time_diff < 1:  # Configurabile in base alle esigenze
                logger.debug(f"Duplicate message detected for device {device_id}")
                return True

        cache.set(cache_key, timestamp, timeout=self._cache_timeout)
        return False

    def _setup_event_handlers(self):
        """Configura gli event handlers per l'Event Bus"""
        # Registra handlers per eventi di potenza
        self._event_bus.register_handler(
            "power_measurement", self._device_handler.handle_device_status
        )

        # Registra handlers per eventi di energia
        self._event_bus.register_handler(
            "energy_measurement", self._measurement_handler.handle_energy_measurement
        )

        # Registra handlers per eventi di status dispositivo
        self._event_bus.register_handler(
            "device_status", self._device_handler.handle_device_status
        )

        # Setup MQTT handlers che pubblicano eventi
        self._setup_mqtt_to_event_bridge()

    def _setup_mqtt_to_event_bridge(self):
        """Configura il bridge MQTT -> Event Bus per compatibilità"""
        # Handler per messaggi di potenza - pubblica eventi
        self._mqtt_service.register_handler(
            "cercollettiva/+/+/status/em:0", self._bridge_power_message_to_event
        )
        self._mqtt_service.register_handler(
            "VePro/+/+/status/em:0", self._bridge_power_message_to_event
        )

        # Handler per messaggi di energia - pubblica eventi
        self._mqtt_service.register_handler(
            "cercollettiva/+/+/status/emdata:0", self._bridge_energy_message_to_event
        )
        self._mqtt_service.register_handler(
            "VePro/+/+/status/emdata:0", self._bridge_energy_message_to_event
        )

    def _setup_cache_policy(self):
        """Configura policy di retention dati per GDPR"""
        self._cache_timeout = getattr(settings, "MQTT_CACHE_TIMEOUT", 3600)
        self._data_retention = getattr(settings, "MQTT_DATA_RETENTION_DAYS", 30)

    def _load_configurations(self) -> None:
        """Carica le configurazioni dei dispositivi dal database"""
        try:
            # Verifica se le configurazioni sono già caricate
            if self._configs_loaded:
                logger.debug("Configurations already loaded, skipping")
                return

            logger.info("Loading configurations...")
            configs = DeviceConfiguration.objects.filter(is_active=True).select_related(
                "plant"
            )

            print("\n=== Configurazioni Dispositivi Trovate ===")
            print(f" |   Trovate {configs.count()} configurazioni attive   |")
            print("==========================================\n")

            # Reset delle configurazioni
            self._devices.clear()
            self._configs.clear()
            self._topic_stats.clear()
            self._active_topics.clear()

            for config in configs:
                self._load_single_config(config)

            print("\n============= Riepilogo ==================")
            print(f" |   Dispositivi caricati: {list(self._devices.keys())}")
            print("==========================================\n")

            # Marca le configurazioni come caricate
            self._configs_loaded = True

        except Exception as e:
            logger.error(f"Error loading configurations: {e}")
            raise

    def _load_single_config(self, config: DeviceConfiguration) -> None:
        """Carica una singola configurazione dispositivo"""
        try:
            # Log con dati mascherati per GDPR
            device_id_masked = f"{config.device_id[:3]}...{config.device_id[-3:]}"
            logger.debug(f"Caricamento dispositivo: {device_id_masked}")

            device = self._device_registry.get_device_by_vendor_model(
                config.vendor, config.model
            )

            if device and config.mqtt_topic_template:
                self._devices[config.device_id] = device
                self._configs[config.device_id] = config
                self._last_energy_values[config.device_id] = (
                    None  # inizializzo il valore
                )
                # logger.info(f"Dispositivo {device_id_masked} caricato con successo")
            else:
                self._log_config_errors(config, device)

        except Exception as e:
            logger.error(f"Errore caricamento dispositivo {config.device_id}: {e}")

    def _bridge_power_message_to_event(self, device_config, payload, topic):
        """Bridge: converte messaggio MQTT potenza in evento Event Bus"""
        try:
            # Crea evento per Event Bus
            event = Event(
                event_type="power_measurement",
                topic=topic,
                payload=payload,
                timestamp=timezone.now(),
                source="mqtt_bridge",
                metadata={
                    "device_id": device_config.device_id,
                    "plant_id": device_config.plant.id if device_config.plant else None,
                    "device_type": device_config.device_type,
                },
            )

            # Pubblica evento asincrono
            self._event_bus.publish_event(event)

            logger.debug(f"Power message bridged to event: {device_config.device_id}")
            return True

        except Exception as e:
            logger.error(f"Error bridging power message to event: {e}")
            return False

    def _bridge_energy_message_to_event(self, device_config, payload, topic):
        """Bridge: converte messaggio MQTT energia in evento Event Bus"""
        try:
            # Crea evento per Event Bus
            event = Event(
                event_type="energy_measurement",
                topic=topic,
                payload=payload,
                timestamp=timezone.now(),
                source="mqtt_bridge",
                metadata={
                    "device_id": device_config.device_id,
                    "plant_id": device_config.plant.id if device_config.plant else None,
                    "device_type": device_config.device_type,
                    "last_energy_value": self._last_energy_values.get(
                        device_config.device_id
                    ),
                },
            )

            # Pubblica evento asincrono
            self._event_bus.publish_event(event)

            logger.debug(f"Energy message bridged to event: {device_config.device_id}")
            return True

        except Exception as e:
            logger.error(f"Error bridging energy message to event: {e}")
            return False

    def _create_phase_details(
        self, measurement: DeviceMeasurement, payload: Dict[str, Any]
    ):
        """Crea i dettagli delle misurazioni per fase"""
        phases = ["a", "b", "c"]
        for phase in phases:
            if all(
                key in payload
                for key in [
                    f"{phase}_voltage",
                    f"{phase}_current",
                    f"{phase}_act_power",
                ]
            ):
                DeviceMeasurementDetail.objects.create(
                    measurement=measurement,
                    phase=phase,
                    voltage=payload.get(f"{phase}_voltage", 0),
                    current=payload.get(f"{phase}_current", 0),
                    power=payload.get(f"{phase}_act_power", 0),
                    power_factor=payload.get(f"{phase}_pf", 1.0),
                    frequency=payload.get(f"{phase}_freq", 50.0),
                )

    def _log_config_errors(
        self, config: DeviceConfiguration, device: Optional[BaseDevice]
    ):
        """Registra gli errori di configurazione in modo sicuro"""
        device_id_masked = f"{config.device_id[:3]}...{config.device_id[-3:]}"
        if not device:
            logger.warning(
                f"Dispositivo {device_id_masked}: vendor/model non supportato"
            )
        if not config.mqtt_topic_template:
            logger.warning(f"Dispositivo {device_id_masked}: template MQTT mancante")

    def get_subscription_topics(self) -> List[str]:
        """Ottiene tutti i topic da sottoscrivere"""
        topics = []
        for device_id, config in self._configs.items():
            device = self._devices.get(device_id)
            if device and config.mqtt_topic_template:
                base_topic = "/".join(config.mqtt_topic_template.split("/")[:3])
                device_topics = device.get_topics(base_topic)
                topics.extend(device_topics)
        return list(set(topics))

    def refresh_configurations(self) -> None:
        """Aggiorna le configurazioni dei dispositivi e ri-registra event handlers"""
        with self._lock:
            self._configs_loaded = False  # Force reload
            self._load_configurations()
            self._setup_event_handlers()  # Re-register event handlers

        logger.info("Device configurations refreshed and event handlers re-registered")

    def _find_device_for_topic(self, topic: str) -> Optional[DeviceConfiguration]:
        try:
            # logger.info(f"Processing topic: {topic}")

            # Cerca tra tutti i device configurati nel database
            devices = DeviceConfiguration.objects.filter(is_active=True)
            # logger.info(f"Found {devices.count()} active devices in DB")

            for device in devices:
                # logger.info(f"\nChecking device: {device.device_id}")
                # logger.info(f"MQTT template: {device.mqtt_topic_template}")

                if not device.mqtt_topic_template:
                    logger.warning(f"Device {device.device_id} has no MQTT template")
                    continue

                # Ottieni il topic base rimuovendo il suffisso
                base_topic = device.mqtt_topic_template.replace("/status/em:0", "")

                # Costruisci i topic possibili per questo device
                device_topics = [
                    f"{base_topic}/status/em:0",
                    f"{base_topic}/status/emdata:0",
                ]

                # logger.info(f"Possible topics for device {device.device_id}:")
                for dt in device_topics:
                    logger.info(f"  - {dt}")

                # Confronta il topic ricevuto con i topic possibili del device
                if topic in device_topics:
                    # logger.info(f"Match found! Device: {device.device_id}, Plant: {device.plant.name}")
                    return device

            logger.warning(f"No device found for topic: {topic}")
            return None

        except Exception as e:
            logger.error(
                f"Error searching device for topic {topic}: {str(e)}", exc_info=True
            )
            return None

    def process_message(self, topic: str, data: Any) -> bool:
        """
        Processa un messaggio MQTT usando Event Bus (event-driven)
        """
        try:
            # Trova il dispositivo per il topic
            device_config = self._find_device_for_topic(topic)
            if not device_config:
                logger.warning(f"No device found for topic: {topic}")
                return False

            # Parse del payload
            payload = self._parse_payload(data)
            if not payload:
                logger.error(f"Invalid payload for topic: {topic}")
                return False

            # Determina il tipo di messaggio e pubblica evento appropriato
            if "/status/em:0" in topic:
                return self._bridge_power_message_to_event(
                    device_config, payload, topic
                )
            elif "/status/emdata:0" in topic:
                return self._bridge_energy_message_to_event(
                    device_config, payload, topic
                )
            else:
                # Evento generico di status dispositivo
                event = Event(
                    event_type="device_status",
                    topic=topic,
                    payload=payload,
                    timestamp=timezone.now(),
                    source="mqtt_manager",
                    metadata={
                        "device_id": device_config.device_id,
                        "plant_id": (
                            device_config.plant.id if device_config.plant else None
                        ),
                    },
                )
                self._event_bus.publish(event)
                return True

        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", exc_info=True)
            return False

    def _parse_payload(self, data: Any) -> Optional[Dict]:
        """Decodifica il payload JSON in modo sicuro"""
        try:
            if isinstance(data, bytes):
                return json.loads(data.decode("utf-8"))
            elif isinstance(data, str):
                return json.loads(data)
            elif isinstance(data, dict):
                return data
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return None

    def _anonymize_topic(self, topic: str) -> str:
        """Anonimizza i dati sensibili nel topic per GDPR"""
        parts = topic.split("/")
        if len(parts) >= 3:
            # Maschera l'identificativo del dispositivo/POD
            parts[2] = f"{parts[2][:3]}...{parts[2][-3:]}"
        return "/".join(parts)

    def get_event_bus_stats(self) -> Dict[str, Any]:
        """Ottiene statistiche dell'Event Bus per monitoring"""
        try:
            return {
                "event_bus_stats": self._event_bus.get_stats(),
                "active_handlers": len(self._event_bus._handlers),
                "devices_loaded": len(self._devices),
                "configs_loaded": len(self._configs),
                "last_energy_values": len(self._last_energy_values),
                "message_buffer_size": len(self._message_buffer),
            }
        except Exception as e:
            logger.error(f"Error getting event bus stats: {e}")
            return {}

    def shutdown(self) -> None:
        """Shutdown graceful dell'Event Bus e cleanup"""
        try:
            logger.info("Shutting down DeviceManager...")
            # Event Bus si chiude automaticamente
            self._message_buffer.clear()
            self._devices.clear()
            self._configs.clear()
            self._last_energy_values.clear()
            logger.info("DeviceManager shutdown completed")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
