#energy/mqtt/core.py
import logging
import threading
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from django.utils import timezone
import paho.mqtt.client as mqtt
from django.conf import settings
from django.core.cache import cache
from ..models import DeviceConfiguration, DeviceMeasurement, MQTTAuditLog

from ..devices.registry import DeviceRegistry
from typing import Dict, Optional, List, Any
import json
from ..models.device import DeviceConfiguration, DeviceMeasurementDetail
import re

logger = logging.getLogger('energy.mqtt')

@dataclass
class MQTTMessage:
    """Classe per standardizzare i messaggi MQTT"""
    topic: str
    payload: Dict[str, Any]
    qos: int
    timestamp: datetime
    device_type: Optional[str] = None
    
    @property
    def vendor(self) -> Optional[str]:
        """Estrae il vendor dal topic"""
        parts = self.topic.split('/')
        return parts[0] if len(parts) > 0 else None
    
class TopicMatcher:
    """Gestione avanzata dei topic MQTT"""
    @staticmethod
    def match(pattern: str, topic: str) -> bool:
        return mqtt.topic_matches_sub(pattern, topic)
    
    @staticmethod
    def extract_device_info(topic: str) -> Optional[Dict[str, str]]:
        """Estrae un identificatore dal topic per la ricerca nel DB."""
        try:
            # Esempio pattern per estrarre il device_id (o una sua parte)
            match = re.match(r'^cercollettiva/(?P<device_id_part>[-\w]+)/status/.*$', topic)
            if match:
                return {"device_id_part": match.group('device_id_part')}

            # Pattern di esempio per VePro
            match = re.match(r'^VePro/(?P<pod_code>[-\w]+)/(?P<device_id_part>[-\w]+)/status/.*$', topic)
            if match:
                return {"pod_code": match.group('pod_code'), "device_id_part": match.group('device_id_part')}
            
            logger.warning(f"Topic {topic} does not match any known pattern")
            return None
        except Exception as e:
            logger.error(f"Error extracting identifier from topic {topic}: {e}")
            logger.exception(e)
            return None

class CircuitBreaker:
    """Implementazione del pattern Circuit Breaker"""
    def __init__(self, failure_threshold: int = 3, reset_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failures = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF-OPEN
        self._lock = threading.Lock()

    def record_failure(self):
        with self._lock:
            self.failures += 1
            self.last_failure_time = timezone.now()
            if self.failures >= self.failure_threshold:
                self.state = "OPEN"

    def record_success(self):
        with self._lock:
            self.failures = 0
            self.state = "CLOSED"

    def can_execute(self) -> bool:
        if self.state == "CLOSED":
            return True

        if self.state == "OPEN":
            if (timezone.now() - self.last_failure_time).total_seconds() > self.reset_timeout:
                self.state = "HALF-OPEN"
                return True
            return False

        return True  # HALF-OPEN state

class MQTTService:
    """Servizio unificato per la gestione MQTT con integrazione DeviceRegistry"""
    
    def __init__(self):
        self._client = None
        self._connected = False
        self._subscribed_topics = set()
        self._lock = threading.Lock()
        self._message_handlers = {}
        self._device_registry = DeviceRegistry()
        self._circuit_breaker = CircuitBreaker()
        self._retry_count = 0
        self._max_retries = 3
        self._retry_delay = 5  # secondi
        self._messages_received = 0
        self._last_error = None
        self._initialize_default_handlers()
        
    def _initialize_default_handlers(self):
        """Inizializza gli handler predefiniti basati sul device registry"""
        self.register_handler(
            "cercollettiva/+/+/status/em:0",
            self._handle_power_measurement
        )
        self.register_handler(
            "cercollettiva/+/+/status/emdata:0", 
            self._handle_energy_measurement
        )

    def configure(self, host: str, port: int, username: Optional[str] = None, 
                 password: Optional[str] = None, use_tls: bool = False) -> None:
        """Configura il client MQTT con retry"""
        try:
            with self._lock:
                client_id = f"CerCollettiva-{timezone.now().timestamp()}"
                self._client = mqtt.Client(client_id=client_id)
                
                # Callbacks
                self._client.on_connect = self._on_connect
                self._client.on_disconnect = self._on_disconnect
                self._client.on_message = self._on_message
                
                # Configurazione
                if username:
                    self._client.username_pw_set(username, password)
                if use_tls:
                    self._client.tls_set()
                
                # Imposta LWT
                self._client.will_set(
                    "CerCollettiva/status",
                    json.dumps({"status": "offline", "timestamp": timezone.now().isoformat()}),
                    qos=1,
                    retain=True
                )
                
                # Connessione con retry
                self._connect_with_retry(host, port)
                
        except Exception as e:
            logger.error(f"Errore configurazione MQTT: {str(e)}")
            self._circuit_breaker.record_failure()
            raise

    def _connect_with_retry(self, host: str, port: int) -> None:
        """Implementa la logica di retry per la connessione"""
        while self._retry_count < self._max_retries:
            try:
                if self._circuit_breaker.can_execute():
                    self._client.connect(host, port, keepalive=60)
                    self._client.loop_start()
                    self._retry_count = 0
                    self._circuit_breaker.record_success()
                    return
                else:
                    logger.warning("Circuit breaker aperto, attendere reset")
                    return
                    
            except Exception as e:
                self._retry_count += 1
                self._circuit_breaker.record_failure()
                logger.error(f"Tentativo {self._retry_count} fallito: {str(e)}")
                if self._retry_count < self._max_retries:
                    time.sleep(self._retry_delay)
                else:
                    raise Exception("Numero massimo di tentativi raggiunto")

    def _on_connect(self, client, userdata, flags, rc):
        """Callback per la connessione MQTT"""
        try:
            if rc == 0:
                with self._lock:
                    self._connected = True
                    # Ripristina le sottoscrizioni
                    self._restore_subscriptions()
                    # Pubblica stato online
                    self._publish_status("online")
                logger.info("Connesso al broker MQTT")
            else:
                error_msgs = {
                    1: "Versione protocollo non corretta",
                    2: "Identificatore client non valido",
                    3: "Server non disponibile",
                    4: "Credenziali non valide",
                    5: "Non autorizzato"
                }
                logger.error(f"Connessione fallita: {error_msgs.get(rc, f'Errore sconosciuto {rc}')}")
                self._circuit_breaker.record_failure()
        except Exception as e:
            logger.error(f"Errore in _on_connect: {str(e)}")

    def _on_disconnect(self, client, userdata, rc):
        """Callback per la disconnessione MQTT"""
        with self._lock:
            self._connected = False
        if rc != 0:
            logger.warning(f"Disconnessione inaspettata dal broker MQTT (rc={rc})")
            self._circuit_breaker.record_failure()

    def _on_message(self, client, userdata, msg):
        """Gestione centralizzata dei messaggi MQTT"""
        try:
            # aggiorna contatore
            with self._lock:
                self._messages_received += 1
            #logger.info(f"\n=== MQTT Message Received ===")
            #logger.info(f"Topic: {msg.topic}")
            #logger.info(f"Payload: {msg.payload}")
            
            payload = json.loads(msg.payload.decode())
            
            # Gestione diretta dei messaggi di potenza ed energia
            if 'em:0' in msg.topic:
                logger.info("Processing power message")
                device_config = self._find_device_for_topic(msg.topic)
                if device_config:
                    self._handle_power_measurement(payload, device_config, msg.topic)
                    
            elif 'emdata:0' in msg.topic:
                #logger.info("Processing energy message")
                device_config = self._find_device_for_topic(msg.topic)
                if device_config:
                    self._handle_energy_measurement(payload, device_config, msg.topic)
                    
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from {msg.topic}: {e}")
            with self._lock:
                self._last_error = str(e)
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            logger.exception(e)
            with self._lock:
                self._last_error = str(e)

    def _handle_power_measurement(self, message: MQTTMessage):
        """Gestisce le misurazioni di potenza"""
        try:
            device_info = TopicMatcher.extract_device_info(message.topic)
            if not device_info:
                return
                
            device = DeviceConfiguration.objects.select_related('plant').get(
                device_id=device_info['device_id'],
                is_active=True
            )
            
            device_instance = self._device_registry.get_device_by_vendor_model(
                device.vendor,
                device.model
            )
            
            if device_instance:
                # Crea misurazione principale
                measurement = DeviceMeasurement.objects.create(
                    device=device,
                    plant=device.plant,
                    timestamp=message.timestamp,
                    power=message.payload.get('total_act_power', 0),
                    voltage=message.payload.get('a_voltage', 0),
                    current=message.payload.get('a_current', 0),
                    power_factor=message.payload.get('total_pf', 1.0),
                    energy_total=message.payload.get('total_act', 0),
                    quality='GOOD'
                )
                
                # Crea dettagli per fase se disponibili
                phases = ['a', 'b', 'c']
                for phase in phases:
                    if all(key in message.payload for key in [f'{phase}_voltage', f'{phase}_current', f'{phase}_act_power']):
                        DeviceMeasurementDetail.objects.create(
                            measurement=measurement,
                            phase=phase,
                            voltage=message.payload.get(f'{phase}_voltage', 0),
                            current=message.payload.get(f'{phase}_current', 0),
                            power=message.payload.get(f'{phase}_act_power', 0),
                            power_factor=message.payload.get(f'{phase}_pf', 1.0),
                            frequency=message.payload.get(f'{phase}_freq', 50.0)
                        )
                
                # Aggiorna timestamp ultimo contatto
                device.update_last_seen()
                
        except Exception as e:
            logger.error(f"Errore nella gestione della misurazione di potenza: {str(e)}")

    def _handle_energy_measurement(self, message: MQTTMessage):
        """Gestisce le misurazioni di energia"""
        try:
            device_info = TopicMatcher.extract_device_info(message.topic)
            if not device_info:
                return
                
            device = DeviceConfiguration.objects.select_related('plant').get(
                device_id=device_info['device_id'],
                is_active=True
            )
            
            DeviceMeasurement.objects.create(
                device=device,
                plant=device.plant,
                timestamp=message.timestamp,
                energy_total=message.payload.get('total_act', 0),
                measurement_type='DRAWN_ENERGY',
                quality='GOOD'
            )
            
            device.update_last_seen()
            
        except Exception as e:
            logger.error(f"Errore nella gestione della misurazione di energia: {str(e)}")

    def _handle_state_transition(self, from_state: str, to_state: str) -> None:
        """Gestisce in modo atomico le transizioni di stato"""
        with self._lock:
            if self._circuit_breaker.state == from_state:
                self._circuit_breaker.state = to_state
                #logger.info(f"Transizione stato: {from_state} -> {to_state}")

    def register_handler(self, topic_pattern: str, handler_func: callable) -> None:
        """Registra un handler per un pattern di topic"""
        with self._lock:
            self._message_handlers[topic_pattern] = handler_func
            if self._connected:
                self._client.subscribe(topic_pattern, qos=1)
                self._subscribed_topics.add(topic_pattern)

    def _restore_subscriptions(self) -> None:
        """Ripristina tutte le sottoscrizioni"""
        with self._lock:
            for topic in self._subscribed_topics:
                self._client.subscribe(topic, qos=1)

    def _publish_status(self, status: str) -> None:
        """Pubblica lo stato del client"""
        try:
            message = {
                "status": status,
                "timestamp": timezone.now().isoformat(),
                "topics": list(self._subscribed_topics)
            }
            
            self._client.publish(
                "CerCollettiva/status",
                json.dumps(message),
                qos=1,
                retain=True
            )
            
        except Exception as e:
            logger.error(f"Errore pubblicazione stato: {str(e)}")

    # --- Compat layer for direct subscribe/unsubscribe ---
    def subscribe(self, topic: str, qos: int = 1) -> bool:
        """Sottoscrive direttamente ad un topic specifico (compatibilità legacy)."""
        try:
            with self._lock:
                if self._client:
                    self._client.subscribe(topic, qos=qos)
                    self._subscribed_topics.add(topic)
                    return True
            return False
        except Exception as e:
            logger.error(f"Errore subscribe({topic}): {e}")
            return False

    def unsubscribe(self, topic: str) -> bool:
        """Annulla la sottoscrizione ad un topic specifico (compatibilità legacy)."""
        try:
            with self._lock:
                if self._client:
                    self._client.unsubscribe(topic)
                    self._subscribed_topics.discard(topic)
                    return True
            return False
        except Exception as e:
            logger.error(f"Errore unsubscribe({topic}): {e}")
            return False

    def _anonymize_topic(self, topic: str) -> str:
        """Anonimizza dati sensibili nel topic per GDPR"""
        parts = topic.split('/')
        if len(parts) >= 3:
            # Maschera POD code
            parts[2] = f"{parts[2][:3]}...{parts[2][-3:]}"
        return '/'.join(parts)

    def _get_device_type(self, device_info: Dict[str, str]) -> Optional[str]:
        """Determina il tipo di dispositivo dai dati del topic"""
        try:
            device = DeviceConfiguration.objects.get(
                device_id=device_info['device_id']
            )
            return device.device_type
        except DeviceConfiguration.DoesNotExist:
            return None

    def _update_metrics(self, message: MQTTMessage):
        """Aggiorna metriche per monitoring"""
        cache.incr('mqtt_messages_received')
        cache.incr(f'mqtt_messages_{message.device_type}')

    @property
    def is_connected(self) -> bool:
        """Verifica lo stato della connessione"""
        return self._connected and self._circuit_breaker.state != "OPEN"

    @property
    def messages_received(self) -> int:
        with self._lock:
            return int(self._messages_received)

    @property
    def last_error(self) -> str | None:
        with self._lock:
            return self._last_error

    def stop(self) -> None:
        """Arresto controllato del servizio MQTT"""
        try:
            if self._client:
                # Pubblica lo stato di arresto
                self._publish_status("shutting_down")
                
                # Pulizia sottoscrizioni in modo thread-safe
                with self._lock:
                    for topic in self._subscribed_topics:
                        self._client.unsubscribe(topic)
                    self._subscribed_topics.clear()
                    self._connected = False  # Dal tuo codice originale
                
                # Arresto del client
                self._client.loop_stop()
                self._client.disconnect()
                
                # Pubblica stato finale
                self._publish_status("offline")
                
                logger.info("Servizio MQTT arrestato correttamente")
                
        except Exception as e:
            logger.error(f"Errore durante l'arresto del client MQTT: {str(e)}")
            # In caso di errore, forza lo stato a disconnesso
            with self._lock:
                self._connected = False
                self._subscribed_topics.clear()


# Singleton instance
_mqtt_service = None

def get_mqtt_service() -> MQTTService:
    """Ottiene l'istanza singleton del servizio MQTT"""
    global _mqtt_service
    if _mqtt_service is None:
        _mqtt_service = MQTTService()
    return _mqtt_service
