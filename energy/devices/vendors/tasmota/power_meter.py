# energy/devices/vendors/tasmota/power_meter.py
from typing import Any, Dict, List, Optional

from ....devices.base.meter import BaseMeter, MeasurementData


class TasmotaPowerMeter(BaseMeter):
    @property
    def vendor(self) -> str:
        return "TASMOTA"

    @property
    def model(self) -> str:
        return "POWER_METER"

    def get_topics(self, base_topic: str) -> List[str]:
        return [f"{base_topic}/tele/SENSOR"]

    def parse_message(
        self, topic: str, payload: Dict[str, Any]
    ) -> Optional[MeasurementData]:
        # Implementa il parsing specifico per Tasmota
        pass


# Registra il nuovo dispositivo
DeviceRegistry.register(TasmotaPowerMeter)
