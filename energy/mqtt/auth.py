# energy/services/mqtt_auth.py
import hashlib
import secrets
import string
from typing import Tuple

from ..models import MQTTCredential


class MQTTAuthService:
    @staticmethod
    def create_credentials(user) -> Tuple[str, str]:
        """Crea nuove credenziali MQTT per un utente"""
        # Genera una password casuale
        password = "".join(
            secrets.choice(string.ascii_letters + string.digits) for _ in range(16)
        )

        # Crea o aggiorna le credenziali
        cred, created = MQTTCredential.objects.get_or_create(user=user)
        cred.mqtt_password = hashlib.sha256(password.encode()).hexdigest()
        cred.save()

        return cred.mqtt_username, password

    @staticmethod
    def validate_credentials(username: str, password: str) -> bool:
        """Valida le credenziali MQTT"""
        try:
            cred = MQTTCredential.objects.get(mqtt_username=username, is_active=True)
            return cred.mqtt_password == hashlib.sha256(password.encode()).hexdigest()
        except MQTTCredential.DoesNotExist:
            return False
