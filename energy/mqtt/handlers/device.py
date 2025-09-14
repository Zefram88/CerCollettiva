# energy/mqtt/handlers/device.py
import logging
from typing import Any, Dict, Optional

from django.db import transaction

from ...devices.base.device import MeasurementData
from ...models import DeviceMeasurement, DeviceMeasurementDetail, EnergyMeasurement
from ...services.device_service import DeviceService
from ...services.measurement_service import MeasurementService
from ...validators import MEASUREMENT_VALIDATOR, MQTT_VALIDATOR
from .base import BaseHandler

logger = logging.getLogger(__name__)


class DeviceHandler(BaseHandler):
    """Handler per la gestione dei dispositivi - Decoupled from business logic"""

    def __init__(self):
        super().__init__()
        self._cached_pod_masks = {}
        self._device_service = DeviceService()
        self._measurement_service = MeasurementService()

    @transaction.atomic
    def save_measurement(self, device_config: Any, data: MeasurementData) -> bool:
        """Salva una misurazione nel database"""
        try:
            # Validazione device config usando validator unificato
            MQTT_VALIDATOR.validate_device_config(device_config)

            # Validazione dati misurazione usando validator unificato
            measurement_data = {
                "power": data.power,
                "voltage": data.voltage,
                "current": data.current,
                "power_factor": data.power_factor,
                "energy_total": data.energy,
                "timestamp": data.timestamp,
                "phase_data": data.phase_data,
                "quality": data.quality,
                "measurement_type": "POWER",
            }
            MEASUREMENT_VALIDATOR.validate(measurement_data)

            # Crea la misurazione principale
            measurement = self._create_measurement(device_config, data)

            # Salva i dettagli delle fasi
            if data.phase_data:
                self._save_phase_details(measurement, data.phase_data)

            # Crea record energia per potenze non zero
            if abs(data.power) > 0:
                self._create_energy_measurement(measurement, device_config, data)

            # Log con POD mascherato
            self._log_measurement(device_config, data)

            return True

        except Exception as e:
            logger.error(f"Error saving measurement: {e}")
            return False

    def _create_measurement(
        self, device_config: Any, data: MeasurementData
    ) -> DeviceMeasurement:
        """Crea il record principale di misurazione"""
        return DeviceMeasurement.objects.create(
            plant=device_config.plant,
            device=device_config,
            timestamp=data.timestamp,
            power=data.power,
            voltage=data.voltage,
            current=data.current,
            energy_total=data.energy,
            power_factor=data.power_factor,
            quality=data.quality,
        )

    def _save_phase_details(
        self, measurement: DeviceMeasurement, phase_data: Dict[str, Dict[str, float]]
    ) -> None:
        """Salva i dettagli delle fasi"""
        # Validazione phase data usando validator unificato
        MEASUREMENT_VALIDATOR.validate_phase_data(phase_data)

        details = []
        for phase, data in phase_data.items():
            if all(key in data for key in ["voltage", "current", "power"]):
                detail = DeviceMeasurementDetail(
                    measurement=measurement,
                    phase=phase,
                    voltage=data["voltage"],
                    current=data["current"],
                    power=data["power"],
                    power_factor=data.get("power_factor", 1.0),
                    frequency=data.get("frequency", 50.0),
                )
                details.append(detail)

        if details:
            DeviceMeasurementDetail.objects.bulk_create(details)

    def _create_energy_measurement(
        self, measurement: DeviceMeasurement, device_config: Any, data: MeasurementData
    ) -> None:
        """Crea il record di misurazione energetica"""
        EnergyMeasurement.objects.create(
            measurement_type="POWER_DRAW" if data.power >= 0 else "POWER_IN",
            value=abs(data.power),
            unit="W",
            topic=device_config.mqtt_topic_template,
            device_measurement=measurement,
            quality=data.quality,
        )

    def _log_measurement(self, device_config: Any, data: MeasurementData) -> None:
        """Log della misurazione con POD mascherato"""
        try:
            pod = getattr(device_config.plant, "pod", "N/A")

            # Usa cache per POD mascherati
            if pod not in self._cached_pod_masks:
                self._cached_pod_masks[pod] = (
                    f"{pod[:3]}...{pod[-3:]}" if len(pod) > 6 else "***"
                )

            # masked_pod = self._cached_pod_masks[pod]  # Unused variable

            # logger.info(
            #    f"Measurement saved - Device: {device_config.device_id} "
            #    f"[{masked_pod}] Power: {data.power:.1f}W"
            # )

        except Exception as e:
            logger.error(f"Error logging measurement: {e}")

    def handle_device_status(self, event) -> bool:
        """
        Gestisce lo status del dispositivo - Event-driven
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

            # Processa il payload come misurazione
            measurement_data = self._parse_measurement_from_event(event)
            if not measurement_data:
                logger.error("Failed to parse measurement from event")
                return False

            # Salva la misurazione usando il metodo esistente
            return self.save_measurement(device_config, measurement_data)

        except Exception as e:
            logger.error(f"Error handling device status: {e}")
            return False

    def _parse_measurement_from_event(self, event) -> Optional[MeasurementData]:
        """Converte evento in MeasurementData"""
        try:
            payload = event.payload

            # Estrae i valori dal payload
            power = float(payload.get("total_act_power", 0))
            voltage = float(payload.get("a_voltage", 0))
            current = float(payload.get("a_current", 0))
            energy = float(payload.get("total_act", 0))
            power_factor = float(payload.get("total_pf", 1.0))

            # Crea MeasurementData
            return MeasurementData(
                timestamp=event.timestamp,
                power=power,
                voltage=voltage,
                current=current,
                energy=energy,
                power_factor=power_factor,
                quality="GOOD",
                phase_data=self._extract_phase_data(payload),
                extra_data=payload,
            )

        except Exception as e:
            logger.error(f"Error parsing measurement from event: {e}")
            return None

    def _extract_phase_data(
        self, payload: Dict[str, Any]
    ) -> Dict[str, Dict[str, float]]:
        """Estrae i dati delle fasi dal payload"""
        phase_data = {}
        phases = ["a", "b", "c"]

        for phase in phases:
            phase_data[phase] = {
                "voltage": float(payload.get(f"{phase}_voltage", 0)),
                "current": float(payload.get(f"{phase}_current", 0)),
                "power": float(payload.get(f"{phase}_act_power", 0)),
                "power_factor": float(payload.get(f"{phase}_pf", 1.0)),
                "frequency": float(payload.get(f"{phase}_freq", 50.0)),
            }

        return phase_data

    def get_device_info(self, device_config: Any) -> Dict[str, Any]:
        """Recupera informazioni sul dispositivo"""
        try:
            return {
                "id": device_config.device_id,
                "type": device_config.device_type,
                "plant": getattr(device_config.plant, "name", "Unknown"),
                "location": getattr(device_config.plant, "location", "Unknown"),
                "last_seen": device_config.last_seen,
            }
        except Exception:
            return {}
