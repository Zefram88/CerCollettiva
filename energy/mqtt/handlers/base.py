# energy/mqtt/handlers/base.py
import logging
from typing import Any, Dict, Optional

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)


class MQTTConfig:
    """Configurazione base per MQTT"""

    def __init__(self):
        mqtt_settings = getattr(settings, "MQTT_SETTINGS", {})
        if not mqtt_settings:
            raise ImproperlyConfigured("MQTT_SETTINGS not found in Django settings")

        self.broker = mqtt_settings.get("BROKER_HOST")
        self.port = mqtt_settings.get("BROKER_PORT")
        self.username = mqtt_settings.get("USERNAME")
        self.password = mqtt_settings.get("PASSWORD")
        self.keepalive = mqtt_settings.get("KEEPALIVE", 60)
        self.qos = mqtt_settings.get("QOS_LEVEL", 1)

        if not all([self.broker, self.port]):
            raise ImproperlyConfigured("Required MQTT settings missing")


class BaseHandler:
    """Handler base per il processamento dei messaggi MQTT"""

    # Cache per errori già loggati
    _logged_errors = set()

    def __init__(self):
        self.config = MQTTConfig()

    def handle_message(self, topic: str, payload: Any) -> bool:
        """
        Template method per gestione messaggi
        """
        try:
            # Pre-processing
            if not self._validate_message(topic, payload):
                return False

            # Parse del payload
            data = self._parse_payload(payload)
            if not data:
                return False

            # Processamento del messaggio
            return self._process_message(topic, data)

        except Exception as e:
            error_key = f"handle_{str(e)}"
            if error_key not in self._logged_errors:
                logger.error(f"Message handling error: {e}")
                self._logged_errors.add(error_key)
            return False

    def _validate_message(self, topic: str, payload: Any) -> bool:
        """Validazione base del messaggio"""
        return True

    def _parse_payload(self, payload: Any) -> Optional[Dict[str, Any]]:
        """Parse del payload con gestione errori"""
        raise NotImplementedError

    def _process_message(self, topic: str, data: Dict[str, Any]) -> bool:
        """Processamento del messaggio"""
        raise NotImplementedError

    def _safe_float(self, value: Any, default: float = 0.0) -> float:
        """Converte in modo sicuro un valore in float"""
        try:
            return float(value) if value is not None else default
        except (TypeError, ValueError):
            return default
