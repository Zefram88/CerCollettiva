# energy/devices/base/device.py
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class MeasurementData:
    """Struttura dati per le misurazioni standardizzate"""

    timestamp: datetime
    power: float
    voltage: float
    current: float
    energy: float
    power_factor: Optional[float] = None
    frequency: float = 50.0
    quality: str = "GOOD"
    phase_data: Optional[Dict[str, Dict[str, float]]] = None
    extra_data: Optional[Dict[str, Any]] = None


class BaseDevice(ABC):
    """Classe base per tutti i dispositivi"""

    def __init__(self):
        self.logger = logging.getLogger(f"energy.devices.{self.__class__.__name__}")

    def _safe_float(self, value: Any, default: float = 0.0) -> float:
        """Converte un valore in float in modo sicuro"""
        try:
            if value is None:
                return default
            return float(value)
        except (ValueError, TypeError):
            return default

    @abstractmethod
    def parse_message(
        self, topic: str, payload: Dict[str, Any]
    ) -> Optional[MeasurementData]:
        """
        Elabora un messaggio MQTT e restituisce i dati di misurazione standardizzati.
        Da implementare nelle classi figlie.
        """
        pass

    @abstractmethod
    def get_topics(self, base_topic: str) -> List[str]:
        """
        Restituisce la lista dei topic MQTT da sottoscrivere.
        Da implementare nelle classi figlie.
        """
        pass

    def validate_config(self) -> bool:
        """
        Valida la configurazione del dispositivo.
        Può essere sovrascritto dalle classi figlie per validazioni specifiche.
        """
        return True

    @property
    @abstractmethod
    def vendor(self) -> str:
        """Il nome del produttore del dispositivo."""
        pass

    @property
    @abstractmethod
    def model(self) -> str:
        """Il modello del dispositivo."""
        pass

    def get_device_type(self) -> str:
        """Restituisce il device_type standardizzato per questo dispositivo"""
        return f"{self.vendor}_{self.model}".upper().replace(" ", "_")

    def get_display_name(self) -> str:
        """Restituisce il nome visualizzato del dispositivo"""
        return f"{self.vendor} {self.model}"

    def validate_measurement(self, measurement: MeasurementData) -> bool:
        """
        Valida i dati di una misurazione.
        Può essere sovrascritto dalle classi figlie per validazioni specifiche.
        """
        if not measurement:
            self.logger.warning("Measurement validation failed: Empty measurement")
            return False

        try:
            # Validazioni base
            if not all(
                [
                    isinstance(measurement.power, (int, float)),
                    isinstance(measurement.voltage, (int, float)),
                    isinstance(measurement.current, (int, float)),
                    isinstance(measurement.energy, (int, float)),
                ]
            ):
                self.logger.warning(
                    "Measurement validation failed: Invalid type for required fields"
                )
                return False

            # Validazione timestamp
            if not isinstance(measurement.timestamp, datetime):
                self.logger.warning("Measurement validation failed: Invalid timestamp")
                return False

            # Validazioni range
            if not (
                -1000000 <= measurement.power <= 1000000  # ±1MW
                and 0 <= measurement.voltage <= 500  # 0-500V
                and -1000 <= measurement.current <= 1000  # ±1000A
            ):
                self.logger.warning(
                    "Measurement validation failed: Values out of range"
                )
                return False

            return True

        except Exception as e:
            self.logger.error(f"Error validating measurement: {str(e)}", exc_info=True)
            return False

    def log_measurement(self, measurement: MeasurementData) -> None:
        """Logga i dettagli di una misurazione per debug"""
        if measurement:
            self.logger.debug(
                f"Measurement from {self.get_display_name()}: "
                f"Power={measurement.power}W, "
                f"Voltage={measurement.voltage}V, "
                f"Current={measurement.current}A, "
                f"Energy={measurement.energy}kWh"
            )
