import string
import secrets
from typing import Tuple
from ..models import MQTTConfiguration


class MQTTAuthService:
    """Gestione credenziali MQTT per dispositivo (device-level)."""

    @staticmethod
    def create_device_credentials(device) -> Tuple[str, str]:
        """Crea credenziali per un DeviceConfiguration."""
        username = f"dev_{device.device_id}"
        password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(16))

        config, _ = MQTTConfiguration.objects.get_or_create(device=device)
        config.mqtt_username = username
        config.mqtt_password = password  # EncryptedCharField gestisce cifratura a riposo
        config.is_active = True
        config.save()
        return username, password

    @staticmethod
    def validate_credentials(username: str, password: str) -> bool:
        """Valida credenziali confrontando con MQTTConfiguration attive."""
        try:
            cfg = MQTTConfiguration.objects.get(mqtt_username=username, is_active=True)
            return cfg.mqtt_password == password
        except MQTTConfiguration.DoesNotExist:
            return False
