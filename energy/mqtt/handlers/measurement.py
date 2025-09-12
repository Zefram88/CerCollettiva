# energy/mqtt/handlers/measurement.py
import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from django.utils import timezone

from ...devices.base.device import MeasurementData
from ...mqtt.router import MessageContext
from ...services.measurement_service import MeasurementService
from .base import BaseHandler

logger = logging.getLogger(__name__)


class MeasurementHandler(BaseHandler):
    """Handler specializzato per messaggi di misurazione - Decoupled from business logic"""

    def __init__(self):
        super().__init__()
        self._measurement_service = MeasurementService()

    def _validate_message(self, topic: str, payload: Any) -> bool:
        """Validazione specifica per misurazioni"""
        if not topic or not payload:
            return False

        # Verifica che il topic sia nella forma corretta
        try:
            parts = topic.split("/")
            return len(parts) >= 3
        except Exception:
            return False

    def _parse_payload(self, payload: Any) -> Optional[Dict[str, Any]]:
        """Parse specializzato per dati di misurazione"""
        try:
            # Gestione diversi tipi di payload
            if isinstance(payload, bytes):
                try:
                    return json.loads(payload.decode("utf-8"))
                except UnicodeDecodeError:
                    return None
            elif isinstance(payload, str):
                return json.loads(payload)
            elif isinstance(payload, dict):
                return payload
            return None

        except json.JSONDecodeError:
            return None
        except Exception as e:
            error_key = f"parse_{str(e)}"
            if error_key not in self._logged_errors:
                logger.error(f"Payload parse error: {e}")
                self._logged_errors.add(error_key)
            return None

    def _process_measurement(self, data: Dict[str, Any]) -> Optional[MeasurementData]:
        """Processa i dati di misurazione"""
        try:
            # Verifica campi minimi richiesti
            if not all(key in data for key in ["power", "voltage", "current"]):
                return None

            # Crea oggetto MeasurementData
            measurement = MeasurementData(
                timestamp=datetime.now(),
                power=self._safe_float(data["power"]),
                voltage=self._safe_float(data["voltage"]),
                current=self._safe_float(data["current"]),
                energy=self._safe_float(data.get("energy", 0)),
                power_factor=self._safe_float(data.get("power_factor", 1.0)),
                frequency=self._safe_float(data.get("frequency", 50.0)),
                quality=data.get("quality", "GOOD"),
                phase_data=data.get("phase_data", {}),
                extra_data=data.get("extra_data", {}),
            )

            return measurement

        except Exception as e:
            logger.error(f"Error processing measurement: {e}")
            return None

    def _validate_measurement(self, data: MeasurementData) -> bool:
        """Validazione dei dati di misurazione"""
        try:
            return (
                data.power is not None
                and data.voltage is not None
                and data.current is not None
                and data.power_factor >= 0
                and data.power_factor <= 1
            )
        except Exception:
            return False

    def handle_power_measurement(self, event) -> bool:
        """
        Gestisce una misurazione di potenza usando il service layer - Event-driven
        """
        try:
            # Converte Event in MessageContext per compatibilità con service layer
            from ..router import MessageContext

            context = MessageContext(
                topic=event.topic,
                payload=event.payload,
                qos=0,  # Default QoS
                retain=False,  # Default retain
                timestamp=event.timestamp,
            )

            return self._measurement_service.process_power_measurement(context)
        except Exception as e:
            logger.error(f"Error handling power measurement: {e}")
            return False

    def handle_energy_measurement(self, event) -> bool:
        """
        Gestisce una misurazione di energia - Event-driven
        """
        try:
            # Estrae device_id dal metadata dell'evento
            device_id = event.metadata.get("device_id")
            if not device_id:
                logger.error("Device ID not found in event metadata")
                return False

            # Trova la configurazione del dispositivo
            from ...models import DeviceConfiguration

            try:
                device_config = DeviceConfiguration.objects.get(
                    device_id=device_id, is_active=True
                )
            except DeviceConfiguration.DoesNotExist:
                logger.error(f"Device configuration not found: {device_id}")
                return False

            # Processa il calcolo del delta energia
            return self._process_energy_delta(event, device_config)

        except Exception as e:
            logger.error(f"Error handling energy measurement: {e}")
            return False

    def _process_energy_delta(self, event, device_config) -> bool:
        """Processa il calcolo del delta energia"""
        try:
            from django.db import transaction
            from django.utils import timezone

            from ...models import DeviceMeasurement

            current_timestamp = event.timestamp
            payload = event.payload

            # Estrae il valore di energia totale dal payload (in Wh)
            current_energy_total = float(payload.get("total_act", 0))

            # Recupera l'ultimo valore di energia per questo dispositivo
            last_energy = event.metadata.get("last_energy_value")

            # Calcola il delta solo se abbiamo un valore precedente
            if last_energy is not None:
                energy_delta = current_energy_total - last_energy

                # Verifica che il delta sia positivo e ragionevole
                if 0 <= energy_delta <= 100000:  # max 100 kWh in 15 min
                    # Crea la misurazione con il delta calcolato
                    with transaction.atomic():
                        measurement = DeviceMeasurement.objects.create(
                            device=device_config,
                            plant=device_config.plant,
                            timestamp=current_timestamp,
                            power=0,  # Per i messaggi di energia, la potenza istantanea non è disponibile
                            voltage=0,  # Valore di default
                            current=0,  # Valore di default
                            energy_total=energy_delta
                            / 1000.0,  # Convertiamo da Wh a kWh
                            measurement_type="ENERGY",
                            quality="GOOD",
                        )

                        # Aggiorna last_seen
                        device_config.last_seen = current_timestamp
                        device_config.save(update_fields=["last_seen"])

                        logger.info(
                            f"""
                            Energy delta calculated for device {device_config.device_id}:
                            - Previous reading: {last_energy:.3f} Wh
                            - Current reading: {current_energy_total:.3f} Wh
                            - Delta: {energy_delta:.3f} Wh ({energy_delta/1000.0:.3f} kWh)
                        """
                        )
                else:
                    logger.warning(
                        f"""
                        Invalid energy delta for device {device_config.device_id}:
                        - Previous reading: {last_energy:.3f} Wh
                        - Current reading: {current_energy_total:.3f} Wh
                        - Delta: {energy_delta:.3f} Wh
                    """
                    )
            else:
                logger.info(
                    f"First energy reading for device {device_config.device_id}: {current_energy_total:.3f} Wh"
                )

            return True

        except Exception as e:
            logger.error(f"Error processing energy delta: {e}")
            return False
