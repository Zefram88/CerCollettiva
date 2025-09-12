# energy/devices/vendors/shelly/em.py
from datetime import datetime
from typing import Any, Dict, List, Optional

from ...base.device import MeasurementData
from .base import BaseShellyMeter


class ShellyEM(BaseShellyMeter):
    """Shelly EM - Misuratore monofase di prima generazione"""

    @property
    def vendor(self) -> str:
        return "SHELLY"

    @property
    def model(self) -> str:
        return "EM"

    def get_topics(self, base_topic: str) -> List[str]:
        return [f"{base_topic}/emeter/0", f"{base_topic}/emeter/1"]

    def parse_message(
        self, topic: str, payload: Dict[str, Any]
    ) -> Optional[MeasurementData]:
        try:
            # Dati fase singola
            phase_data = {
                "a": {
                    "voltage": self._safe_float(payload.get("voltage")),
                    "current": self._safe_float(payload.get("current")),
                    "power": self._safe_float(payload.get("power")),
                    "power_factor": self._safe_float(payload.get("pf"), 1.0),
                    "frequency": self._safe_float(payload.get("freq"), 50.0),
                }
            }

            return MeasurementData(
                timestamp=datetime.now(),
                power=self._safe_float(payload.get("power")),
                voltage=self._safe_float(payload.get("voltage")),
                current=self._safe_float(payload.get("current")),
                energy=self._safe_float(payload.get("total")),
                power_factor=self._safe_float(payload.get("pf"), 1.0),
                frequency=self._safe_float(payload.get("freq"), 50.0),
                quality="GOOD",
                phase_data=phase_data,
                extra_data={
                    "total_returned": self._safe_float(payload.get("total_returned")),
                    "is_valid": bool(payload.get("is_valid", True)),
                },
            )

        except Exception:
            return None
