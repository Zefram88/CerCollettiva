# energy/services/measurement_service.py

import logging
# from datetime import datetime
from typing import Any, Dict, Optional

from django.core.cache import cache
from django.db import transaction
from django.utils import timezone

from ..models import DeviceConfiguration, DeviceMeasurement, DeviceMeasurementDetail
from ..mqtt.router import MessageContext

logger = logging.getLogger("energy.services")


class MeasurementService:
    """
    Servizio per la gestione delle misurazioni energetiche
    Separa la logica di business dalla gestione MQTT
    """

    def __init__(self):
        self._last_energy_values = {}
        self._cache_timeout = 300  # 5 minuti

    def process_power_measurement(self, context: MessageContext) -> bool:
        """
        Processa una misurazione di potenza
        """
        try:
            # Trova la configurazione del dispositivo
            device_config = self._find_device_config(context)
            if not device_config:
                logger.warning(f"No device config found for topic: {context.topic}")
                return False

            # Verifica duplicati
            if self._is_duplicate_message(context, device_config):
                return True

            # Estrai i valori dal payload
            measurement_data = self._extract_power_data(context.payload)
            if not measurement_data:
                return False

            # Salva la misurazione
            success = self._save_power_measurement(
                device_config, measurement_data, context
            )

            if success:
                # Aggiorna last_seen
                self._update_device_last_seen(device_config)

                # Cache del messaggio processato
                self._cache_processed_message(context, device_config)

            return success

        except Exception as e:
            logger.error(f"Error processing power measurement: {e}")
            return False

    def process_energy_measurement(self, context: MessageContext) -> bool:
        """
        Processa una misurazione di energia
        """
        try:
            # Trova la configurazione del dispositivo
            device_config = self._find_device_config(context)
            if not device_config:
                logger.warning(f"No device config found for topic: {context.topic}")
                return False

            # Estrai il valore di energia totale
            current_energy_total = self._extract_energy_data(context.payload)
            if current_energy_total is None:
                return False

            # Calcola il delta rispetto all'ultima lettura
            energy_delta = self._calculate_energy_delta(
                device_config.device_id, current_energy_total
            )

            if energy_delta is not None:
                # Salva la misurazione con il delta
                success = self._save_energy_measurement(
                    device_config, energy_delta, context
                )

                if success:
                    # Aggiorna last_seen
                    self._update_device_last_seen(device_config)

                return success

            return True  # Prima lettura, non c'è delta da salvare

        except Exception as e:
            logger.error(f"Error processing energy measurement: {e}")
            return False

    def _find_device_config(
        self, context: MessageContext
    ) -> Optional[DeviceConfiguration]:
        """
        Trova la configurazione del dispositivo basata sul contesto del messaggio
        """
        try:
            if not context.device_id:
                return None

            # Cerca per device_id
            device_config = (
                DeviceConfiguration.objects.select_related("plant")
                .filter(device_id=context.device_id, is_active=True)
                .first()
            )

            if device_config:
                return device_config

            # Se non trovato per device_id, prova a cercare per pattern del topic
            return self._find_device_by_topic_pattern(context.topic)

        except Exception as e:
            logger.error(f"Error finding device config: {e}")
            return None

    def _find_device_by_topic_pattern(
        self, topic: str
    ) -> Optional[DeviceConfiguration]:
        """
        Trova la configurazione del dispositivo basata sul pattern del topic
        """
        try:
            # Cerca tra tutti i dispositivi attivi
            devices = DeviceConfiguration.objects.filter(is_active=True).select_related(
                "plant"
            )

            for device in devices:
                if not device.mqtt_topic_template:
                    continue

                # Costruisci i topic possibili per questo dispositivo
                base_topic = device.mqtt_topic_template.replace("/status/em:0", "")
                device_topics = [
                    f"{base_topic}/status/em:0",
                    f"{base_topic}/status/emdata:0",
                ]

                # Verifica se il topic ricevuto corrisponde
                if topic in device_topics:
                    return device

            return None

        except Exception as e:
            logger.error(f"Error finding device by topic pattern: {e}")
            return None

    def _extract_power_data(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Estrae i dati di potenza dal payload
        """
        try:
            required_fields = ["total_act_power", "a_voltage", "a_current"]
            if not all(field in payload for field in required_fields):
                logger.warning("Missing required power measurement fields")
                return None

            return {
                "power": float(payload.get("total_act_power", 0)),
                "voltage": float(payload.get("a_voltage", 0)),
                "current": float(payload.get("a_current", 0)),
                "power_factor": float(payload.get("total_pf", 1.0)),
                "energy_total": float(payload.get("total_act", 0)),
                "phase_data": self._extract_phase_data(payload),
            }

        except (ValueError, TypeError) as e:
            logger.error(f"Error extracting power data: {e}")
            return None

    def _extract_energy_data(self, payload: Dict[str, Any]) -> Optional[float]:
        """
        Estrae il valore di energia totale dal payload
        """
        try:
            energy_value = payload.get("total_act", 0)
            return float(energy_value) if energy_value is not None else None
        except (ValueError, TypeError) as e:
            logger.error(f"Error extracting energy data: {e}")
            return None

    def _extract_phase_data(
        self, payload: Dict[str, Any]
    ) -> Dict[str, Dict[str, float]]:
        """
        Estrae i dati delle fasi dal payload
        """
        phase_data = {}
        phases = ["a", "b", "c"]

        for phase in phases:
            phase_fields = [
                f"{phase}_voltage",
                f"{phase}_current",
                f"{phase}_act_power",
            ]
            if all(field in payload for field in phase_fields):
                try:
                    phase_data[phase] = {
                        "voltage": float(payload.get(f"{phase}_voltage", 0)),
                        "current": float(payload.get(f"{phase}_current", 0)),
                        "power": float(payload.get(f"{phase}_act_power", 0)),
                        "power_factor": float(payload.get(f"{phase}_pf", 1.0)),
                        "frequency": float(payload.get(f"{phase}_freq", 50.0)),
                    }
                except (ValueError, TypeError):
                    continue

        return phase_data

    def _calculate_energy_delta(
        self, device_id: str, current_energy: float
    ) -> Optional[float]:
        """
        Calcola il delta di energia rispetto all'ultima lettura
        """
        try:
            last_energy = self._last_energy_values.get(device_id)

            if last_energy is not None:
                energy_delta = current_energy - last_energy

                # Verifica che il delta sia ragionevole (max 100 kWh in 15 min)
                if 0 <= energy_delta <= 100000:
                    return energy_delta
                else:
                    logger.warning(
                        f"Invalid energy delta for device {device_id}: "
                        f"{energy_delta} Wh (previous: {last_energy}, "
                        f"current: {current_energy})"
                    )
                    return None
            else:
                logger.info(
                    f"First energy reading for device {device_id}: {current_energy} Wh"
                )
                return None

        except Exception as e:
            logger.error(f"Error calculating energy delta: {e}")
            return None
        finally:
            # Aggiorna l'ultimo valore per la prossima lettura
            self._last_energy_values[device_id] = current_energy

    def _save_power_measurement(
        self,
        device_config: DeviceConfiguration,
        measurement_data: Dict[str, Any],
        context: MessageContext,
    ) -> bool:
        """
        Salva una misurazione di potenza nel database
        """
        try:
            with transaction.atomic():
                # Crea la misurazione principale
                measurement = DeviceMeasurement.objects.create(
                    device=device_config,
                    plant=device_config.plant,
                    timestamp=context.timestamp,
                    power=measurement_data["power"],
                    voltage=measurement_data["voltage"],
                    current=measurement_data["current"],
                    power_factor=measurement_data["power_factor"],
                    energy_total=measurement_data["energy_total"],
                    measurement_type="POWER",
                    quality="GOOD",
                )

                # Salva i dettagli delle fasi
                if measurement_data["phase_data"]:
                    self._save_phase_details(
                        measurement, measurement_data["phase_data"]
                    )

                logger.debug(
                    f"Power measurement saved - Device: {device_config.device_id} "
                    f"Power: {measurement_data['power']:.1f}W"
                )

                return True

        except Exception as e:
            logger.error(f"Error saving power measurement: {e}")
            return False

    def _save_energy_measurement(
        self,
        device_config: DeviceConfiguration,
        energy_delta: float,
        context: MessageContext,
    ) -> bool:
        """
        Salva una misurazione di energia nel database
        """
        try:
            with transaction.atomic():
                DeviceMeasurement.objects.create(
                    device=device_config,
                    plant=device_config.plant,
                    timestamp=context.timestamp,
                    power=0,  # Per i messaggi di energia, la potenza
                    # istantanea non è disponibile
                    voltage=0,
                    current=0,
                    energy_total=energy_delta / 1000.0,  # Converti da Wh a kWh
                    measurement_type="ENERGY",
                    quality="GOOD",
                )

                logger.debug(
                    f"Energy measurement saved - Device: {device_config.device_id} "
                    f"Delta: {energy_delta:.3f} Wh ({energy_delta/1000.0:.3f} kWh)"
                )

                return True

        except Exception as e:
            logger.error(f"Error saving energy measurement: {e}")
            return False

    def _save_phase_details(
        self, measurement: DeviceMeasurement, phase_data: Dict[str, Dict[str, float]]
    ) -> None:
        """
        Salva i dettagli delle fasi
        """
        try:
            details = []
            for phase, data in phase_data.items():
                detail = DeviceMeasurementDetail(
                    measurement=measurement,
                    phase=phase,
                    voltage=data["voltage"],
                    current=data["current"],
                    power=data["power"],
                    power_factor=data["power_factor"],
                    frequency=data["frequency"],
                )
                details.append(detail)

            if details:
                DeviceMeasurementDetail.objects.bulk_create(details)

        except Exception as e:
            logger.error(f"Error saving phase details: {e}")

    def _update_device_last_seen(self, device_config: DeviceConfiguration) -> None:
        """
        Aggiorna il timestamp dell'ultimo contatto del dispositivo
        """
        try:
            device_config.last_seen = timezone.now()
            device_config.save(update_fields=["last_seen"])
        except Exception as e:
            logger.error(f"Error updating device last_seen: {e}")

    def _is_duplicate_message(
        self, context: MessageContext, device_config: DeviceConfiguration
    ) -> bool:
        """
        Verifica se il messaggio è un duplicato
        """
        try:
            msg_key = (
                f"{context.topic}_{device_config.device_id}_"
                f"{hash(str(context.payload))}"
            )
            return bool(cache.get(msg_key))
        except Exception as e:
            logger.error(f"Error checking duplicate message: {e}")
            return False

    def _cache_processed_message(
        self, context: MessageContext, device_config: DeviceConfiguration
    ) -> None:
        """
        Cache del messaggio processato per evitare duplicati
        """
        try:
            msg_key = (
                f"{context.topic}_{device_config.device_id}_"
                f"{hash(str(context.payload))}"
            )
            cache.set(msg_key, True, timeout=self._cache_timeout)
        except Exception as e:
            logger.error(f"Error caching processed message: {e}")

    def get_measurement_stats(self) -> Dict[str, Any]:
        """
        Restituisce le statistiche delle misurazioni
        """
        return {
            "last_energy_values": len(self._last_energy_values),
            "cache_timeout": self._cache_timeout,
        }
