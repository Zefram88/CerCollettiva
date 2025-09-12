# energy/devices/base/inverter.py
from .device import BaseDevice, MeasurementData


class BaseInverter(BaseDevice):
    """Classe base per gli inverter"""

    @property
    def device_type(self) -> str:
        return "INVERTER"

    def validate_measurement(self, data: MeasurementData) -> bool:
        """Validazione base dei dati di misurazione"""
        return data.power is not None and data.energy is not None
