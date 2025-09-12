# energy/devices/vendors/shelly/pro_em.py
from datetime import datetime
from typing import Any, Dict, List, Optional

from ...base.device import MeasurementData
from .base import BaseShellyMeter


class ShellyProEM(BaseShellyMeter):
    """Shelly Pro EM - Misuratore monofase professionale"""

    @property
    def vendor(self) -> str:
        return "SHELLY"

    @property
    def model(self) -> str:
        return "PRO_EM"

    def get_topics(self, base_topic: str) -> List[str]:
        return [f"{base_topic}/status/em:0/#", f"{base_topic}/status/#"]

    def parse_message(
        self, topic: str, payload: Dict[str, Any]
    ) -> Optional[MeasurementData]:
        try:
            # Verifica campi richiesti
            required = ["power", "voltage", "current"]
            if not all(field in payload for field in required):
                return None

            # Dati fase singola
            phase_data = {
                "a": {
                    "voltage": self._safe_float(payload["voltage"]),
                    "current": self._safe_float(payload["current"]),
                    "power": self._safe_float(payload["power"]),
                    "power_factor": self._safe_float(payload.get("pf"), 1.0),
                    "frequency": self._safe_float(payload.get("freq"), 50.0),
                    "reactive_power": self._safe_float(payload.get("reactive_power")),
                    "apparent_power": self._safe_float(payload.get("apparent_power")),
                }
            }

            extra_data = {
                "returned_energy": self._safe_float(payload.get("returned_energy")),
                "total_returned": self._safe_float(payload.get("total_returned")),
            }

            return MeasurementData(
                timestamp=datetime.now(),
                power=self._safe_float(payload["power"]),
                voltage=self._safe_float(payload["voltage"]),
                current=self._safe_float(payload["current"]),
                energy=self._safe_float(payload.get("energy_total", 0)),
                power_factor=self._safe_float(payload.get("pf"), 1.0),
                frequency=self._safe_float(payload.get("freq"), 50.0),
                quality="GOOD",
                phase_data=phase_data,
                extra_data=extra_data,
            )

        except Exception:
            return None
