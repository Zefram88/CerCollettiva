# energy/devices/vendors/shelly/plus_plug_s.py
from datetime import datetime
from typing import Any, Dict, List, Optional

from ...base.device import MeasurementData
from .base import BaseShellyMeter


class ShellyPlusPlugS(BaseShellyMeter):
    """Shelly Plus Plug S - Smart plug con misurazione energetica"""

    @property
    def vendor(self) -> str:
        return "SHELLY"

    @property
    def model(self) -> str:
        return "PLUS_PLUG_S"

    def get_topics(self, base_topic: str) -> List[str]:
        return [
            f"{base_topic}/status/switch:0",  # Stato del relay e misurazioni
            f"{base_topic}/status",  # Stato generale del dispositivo
        ]

    def parse_message(
        self, topic: str, payload: Dict[str, Any]
    ) -> Optional[MeasurementData]:
        try:
            # Estrai i dati di misurazione dal payload
            switch_data = payload.get("switch:0", {})
            if not switch_data:
                return None

            # Verifica campi richiesti
            required = ["apower", "voltage", "current"]
            if not all(field in switch_data for field in required):
                return None

            # Dati fase singola (il Plus Plug S è monofase)
            phase_data = {
                "a": {
                    "voltage": self._safe_float(switch_data.get("voltage")),
                    "current": self._safe_float(switch_data.get("current")),
                    "power": self._safe_float(
                        switch_data.get("apower")
                    ),  # Potenza attiva
                    "power_factor": self._safe_float(switch_data.get("pf"), 1.0),
                    "frequency": self._safe_float(switch_data.get("freq"), 50.0),
                    "apparent_power": self._safe_float(switch_data.get("apower")),  # VA
                }
            }

            # Dati aggiuntivi specifici del Plus Plug S
            extra_data = {
                "is_relay_on": bool(switch_data.get("output", False)),
                "temperature": {
                    "celsius": self._safe_float(
                        switch_data.get("temperature", {}).get("tC")
                    ),
                    "fahrenheit": self._safe_float(
                        switch_data.get("temperature", {}).get("tF")
                    ),
                },
                "overpower_occurred": bool(
                    switch_data.get("errors", {}).get("overpower", False)
                ),
                "overvoltage_occurred": bool(
                    switch_data.get("errors", {}).get("overvoltage", False)
                ),
                "relay_state_timestamps": {
                    "last_on": switch_data.get("last_on", ""),
                    "last_off": switch_data.get("last_off", ""),
                },
            }

            return MeasurementData(
                timestamp=datetime.now(),
                power=self._safe_float(switch_data.get("apower")),
                voltage=self._safe_float(switch_data.get("voltage")),
                current=self._safe_float(switch_data.get("current")),
                energy=self._safe_float(switch_data.get("aenergy", {}).get("total")),
                power_factor=self._safe_float(switch_data.get("pf"), 1.0),
                frequency=self._safe_float(switch_data.get("freq"), 50.0),
                quality="GOOD",
                phase_data=phase_data,
                extra_data=extra_data,
            )

        except Exception:
            return None

    def validate_config(self) -> bool:
        """Validazione specifica per Shelly Plus Plug S"""
        # Qui potrebbero andare validazioni specifiche per il Plus Plug S
        return True
