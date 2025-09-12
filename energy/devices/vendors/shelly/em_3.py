# energy/devices/vendors/shelly/em_3.py
from datetime import datetime
from typing import Any, Dict, List, Optional

from ...base.device import MeasurementData
from .base import BaseShellyMeter


class ShellyEM3(BaseShellyMeter):
    """Shelly 3EM - Misuratore trifase di prima generazione"""

    @property
    def vendor(self) -> str:
        return "SHELLY"

    @property
    def model(self) -> str:
        return "EM3"

    def get_topics(self, base_topic: str) -> List[str]:
        return [
            f"{base_topic}/emeter/0",
            f"{base_topic}/emeter/1",
            f"{base_topic}/emeter/2",
        ]

    def parse_message(
        self, topic: str, payload: Dict[str, Any]
    ) -> Optional[MeasurementData]:
        try:
            # Determina la fase dal topic
            phase_num = int(topic.split("/")[-1])
            phase_map = {0: "a", 1: "b", 2: "c"}
            phase = phase_map.get(phase_num)

            if not phase:
                return None

            # Struttura base per le fasi
            phase_data = {
                p: {
                    "voltage": 0,
                    "current": 0,
                    "power": 0,
                    "power_factor": 1.0,
                    "frequency": 50.0,
                }
                for p in ["a", "b", "c"]
            }

            # Aggiorna i dati della fase corrente
            phase_data[phase].update(
                {
                    "voltage": self._safe_float(payload.get("voltage")),
                    "current": self._safe_float(payload.get("current")),
                    "power": self._safe_float(payload.get("power")),
                    "power_factor": self._safe_float(payload.get("pf"), 1.0),
                    "frequency": self._safe_float(payload.get("freq"), 50.0),
                }
            )

            # Calcola i totali
            total_power = sum(p["power"] for p in phase_data.values())
            avg_voltage = sum(p["voltage"] for p in phase_data.values()) / 3
            total_current = sum(p["current"] for p in phase_data.values())

            return MeasurementData(
                timestamp=datetime.now(),
                power=total_power,
                voltage=avg_voltage,
                current=total_current,
                energy=self._safe_float(payload.get("total")),
                power_factor=self._safe_float(payload.get("pf"), 1.0),
                frequency=self._safe_float(payload.get("freq"), 50.0),
                quality="GOOD",
                phase_data=phase_data,
                extra_data={
                    "total_returned": self._safe_float(payload.get("total_returned")),
                    "phase_number": phase_num,
                },
            )

        except Exception:
            return None
