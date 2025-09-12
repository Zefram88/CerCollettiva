# energy/devices/base/meter.py
from datetime import datetime
from typing import Any, Dict, Optional

from .device import BaseDevice, MeasurementData


class BaseMeter(BaseDevice):
    """Classe base per dispositivi di misurazione energetica"""

    def __init__(self):
        super().__init__()
        self.measurement_types = {
            "power": "W",
            "voltage": "V",
            "current": "A",
            "energy": "kWh",
            "power_factor": None,
        }

    def parse_measurement(
        self, topic: str, data: Dict[str, Any]
    ) -> Optional[MeasurementData]:
        """
        Converte i dati raw in una struttura MeasurementData standardizzata

        Args:
            topic (str): Topic MQTT del messaggio
            data (dict): Dati ricevuti dal dispositivo

        Returns:
            Optional[MeasurementData]: Dati di misurazione formattati o None se non validi
        """
        try:
            # Estrai i valori base richiesti
            power = self.extract_value(data, "power", float)
            voltage = self.extract_value(data, "voltage", float)
            current = self.extract_value(data, "current", float)

            # Valori opzionali
            energy = self.extract_value(data, "energy", float, default=0.0)
            power_factor = self.extract_value(data, "power_factor", float, default=None)
            timestamp = self.extract_timestamp(data)

            # Dati per fase (se disponibili)
            phase_data = self.extract_phase_data(data)

            return MeasurementData(
                timestamp=timestamp,
                power=power,
                voltage=voltage,
                current=current,
                energy=energy,
                power_factor=power_factor,
                phase_data=phase_data,
                quality="GOOD" if all([power, voltage, current]) else "UNCERTAIN",
            )

        except Exception as e:
            self.logger.error(f"Error parsing measurement data: {e}")
            return None

    def extract_value(
        self, data: Dict[str, Any], key: str, type_func: callable, default: Any = None
    ) -> Any:
        """
        Estrae un valore dal dizionario dati con conversione di tipo

        Args:
            data (dict): Dizionario dati
            key (str): Chiave da estrarre
            type_func (callable): Funzione di conversione tipo (es. float, int)
            default: Valore di default se non presente o non valido

        Returns:
            Valore convertito o default
        """
        try:
            value = data.get(key)
            if value is not None:
                return type_func(value)
            return default
        except (ValueError, TypeError):
            return default

    def extract_timestamp(self, data: Dict[str, Any]) -> datetime:
        """
        Estrae il timestamp dai dati, con fallback al timestamp corrente
        """
        try:
            ts = data.get("timestamp")
            if isinstance(ts, (int, float)):
                return datetime.fromtimestamp(ts)
            elif isinstance(ts, str):
                return datetime.fromisoformat(ts.replace("Z", "+00:00"))
            return datetime.now()
        except Exception:
            return datetime.now()

    def extract_phase_data(
        self, data: Dict[str, Any]
    ) -> Optional[Dict[str, Dict[str, float]]]:
        """
        Estrae i dati per fase se disponibili
        """
        try:
            if "phases" not in data:
                return None

            phase_data = {}
            for phase, values in data["phases"].items():
                phase_data[phase] = {
                    "voltage": self.extract_value(values, "voltage", float, 0),
                    "current": self.extract_value(values, "current", float, 0),
                    "power": self.extract_value(values, "power", float, 0),
                    "power_factor": self.extract_value(values, "power_factor", float),
                    "frequency": self.extract_value(values, "frequency", float, 50),
                }
            return phase_data

        except Exception as e:
            self.logger.error(f"Error extracting phase data: {e}")
            return None

    def validate_measurement(self, measurement: MeasurementData) -> bool:
        """
        Valida i dati di misurazione
        """
        try:
            if not all(
                [
                    isinstance(measurement.power, (int, float)),
                    isinstance(measurement.voltage, (int, float)),
                    isinstance(measurement.current, (int, float)),
                ]
            ):
                return False

            # Validazioni di range
            if not (
                -1000000 <= measurement.power <= 1000000  # ±1MW
                and 0 <= measurement.voltage <= 500  # 0-500V
                and -1000 <= measurement.current <= 1000  # ±1000A
            ):
                return False

            # Se presente, valida il power factor
            if measurement.power_factor is not None:
                if not -1 <= measurement.power_factor <= 1:
                    return False

            return True

        except Exception:
            return False

    def get_topics(self, base_topic: str) -> list:
        """
        Restituisce la lista dei topic da sottoscrivere per questo dispositivo
        """
        return [f"{base_topic}/+/value"]

    @property
    def vendor(self) -> str:
        return "generic"

    @property
    def model(self) -> str:
        return "meter"
