# energy/services/device_manager.py
from typing import Any, Dict, Optional

# from django.core.cache import cache

from ..models.device import Device

# from ..models.device import DeviceType


class DeviceManager:
    """Gestore centralizzato dei dispositivi"""

    @staticmethod
    def get_device(device_id: int) -> Optional[Device]:
        """Recupera un dispositivo dal database"""
        return (
            Device.objects.filter(id=device_id, is_active=True)
            .select_related("device_type")
            .first()
        )

    @staticmethod
    def process_mqtt_message(topic: str, payload: Dict[str, Any]) -> None:
        """Processa un messaggio MQTT"""
        # Implementa la logica di processing qui
        pass

    @staticmethod
    def get_active_devices():
        """Recupera tutti i dispositivi attivi"""
        return Device.objects.filter(is_active=True).select_related("device_type")

    @classmethod
    def validate_payload(cls, device: Device, payload: Dict[str, Any]) -> bool:
        """Valida il payload MQTT contro il formato atteso"""
        # expected_format = device.device_type.mqtt_payload_format  # Unused variable
        # Implementa la validazione qui
        return True
