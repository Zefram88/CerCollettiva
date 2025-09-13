# energy/devices/vendors/shelly/pro_3em.py
import logging

# from datetime import datetime
from typing import Any, List, Optional

from django.utils import timezone

from ...base.device import MeasurementData
from .base import BaseShellyMeter

# from typing import Dict


# Configurazione del logger
logger = logging.getLogger(__name__)


class ShellyPro3EM(BaseShellyMeter):
    """
    Implementazione specifica per Shelly Pro 3EM.
    Misuratore trifase professionale con supporto per misurazioni avanzate
    di potenza, energia e parametri elettrici su tre fasi.
    """

    _vendor = "SHELLY"
    _model = "PRO_3EM"

    @property
    def vendor(self) -> str:
        """
        Restituisce il vendor del dispositivo.
        """
        return self._vendor

    @property
    def model(self) -> str:
        """
        Restituisce il modello del dispositivo.
        """
        return self._model

    @classmethod
    def get_device_type(cls) -> str:
        """
        Restituisce il tipo di dispositivo per identificazione nel sistema.
        """
        return "SHELLY_PRO_3EM"

    def get_topics(self, base_topic: str) -> List[str]:
        """
        Definisce i topic MQTT specifici per il Pro 3EM.

        Args:
            base_topic (str): Il topic base del dispositivo

        Returns:
            List[str]: Lista dei topic da sottoscrivere
        """
        return [
            f"{base_topic}/status/em:0",
            f"{base_topic}/status/emdata:0",
            # f"{base_topic}/status/#"
        ]

    def parse_shelly_data(
        self, message_type: str, data: Any
    ) -> Optional[MeasurementData]:
        """
        Implementa il parsing specifico per i dati del Pro 3EM.

        Args:
            message_type (str): Il tipo di messaggio (em, emeter, etc.)
            data (Any): I dati da parsare

        Returns:
            Optional[MeasurementData]: Oggetto contenente i dati della misurazione,
                                     None se il parsing fallisce
        """
        try:
            # Log dettagliati per debug
            logger.debug(f"Parsing dati Pro 3EM - Tipo: {type(data)}")
            logger.debug(f"Message type: {message_type}")
            logger.debug(f"Contenuto: {data}")

            # Gestione payload non-dict
            if not isinstance(data, dict):
                logger.debug(
                    f"Dati non in formato dict - Tipo: {type(data)}, Valore: {data}"
                )
                return None

            # Verifica campi richiesti
            required = [
                "total_act_power",
                "total_current",
                "a_voltage",
                "b_voltage",
                "c_voltage",
            ]
            missing_fields = [f for f in required if f not in data]
            if missing_fields:
                logger.debug(f"Campi mancanti: {missing_fields}")
                return None

            # Calcolo tensione media delle tre fasi
            phase_voltages = [
                self._safe_float(data.get(f"{p}_voltage", 0)) for p in ["a", "b", "c"]
            ]
            avg_voltage = sum(phase_voltages) / 3 if any(phase_voltages) else 0

            # Raccolta dati per ogni fase
            phase_data = {}
            for phase in ["a", "b", "c"]:
                try:
                    phase_data[phase] = {
                        "voltage": self._safe_float(data.get(f"{phase}_voltage")),
                        "current": self._safe_float(data.get(f"{phase}_current")),
                        "power": self._safe_float(data.get(f"{phase}_act_power")),
                        "power_factor": self._safe_float(data.get(f"{phase}_pf"), 1.0),
                        "frequency": self._safe_float(data.get(f"{phase}_freq"), 50.0),
                        "reactive_power": self._safe_float(
                            data.get(f"{phase}_react_power")
                        ),
                        "apparent_power": self._safe_float(
                            data.get(f"{phase}_aprt_power")
                        ),
                    }
                except ValueError as e:
                    logger.debug(f"Errore parsing fase {phase}: {e}")
                    continue

            # Creazione oggetto misurazione completo
            return MeasurementData(
                timestamp=timezone.now(),
                power=self._safe_float(data.get("total_act_power")),
                voltage=avg_voltage,
                current=self._safe_float(data.get("total_current")),
                energy=self._safe_float(data.get("total_act_energy")),
                power_factor=self._safe_float(data.get("total_pf"), 1.0),
                frequency=(
                    sum(d["frequency"] for d in phase_data.values()) / len(phase_data)
                    if phase_data
                    else 50.0
                ),
                quality="GOOD",
                phase_data=phase_data,
                extra_data={
                    "total_reactive_power": self._safe_float(
                        data.get("total_react_power")
                    ),
                    "total_apparent_power": self._safe_float(
                        data.get("total_aprt_power")
                    ),
                    "total_returned_energy": self._safe_float(
                        data.get("total_returned_energy")
                    ),
                },
            )

        except Exception as e:
            logger.error(
                f"Errore durante il parsing dei dati Pro 3EM: {str(e)}", exc_info=True
            )
            logger.debug(f"Dati problematici: {data}")
            return None

    def _safe_float(self, value: Any, default: float = 0.0) -> float:
        """
        Converte in modo sicuro un valore a float.

        Args:
            value (Any): Il valore da convertire
            default (float): Il valore di default se la conversione fallisce

        Returns:
            float: Il valore convertito o il default
        """
        try:
            return float(value) if value is not None else default
        except (ValueError, TypeError):
            return default
