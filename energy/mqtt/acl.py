from typing import Dict, Any
from ..models import MQTTConfiguration


class MQTTAccessControl:
    @staticmethod
    def check_acl(username: str, topic: str, access_type: str) -> bool:
        """
        Verifica i permessi di accesso per un topic MQTT (per-device).
        Consente l'accesso ai topic che iniziano col template del device.
        access_type: 'subscribe' o 'publish'
        """
        try:
            cfg = MQTTConfiguration.objects.select_related('device', 'device__plant').get(
                mqtt_username=username,
                is_active=True,
            )
            base = (cfg.device.mqtt_topic_template or '').split('/status')[0]
            if base and topic.startswith(base):
                return True

            # Fallback: consentire se il topic contiene il POD dell'impianto
            pod = getattr(cfg.device.plant, 'pod_code', None)
            if pod and pod in topic:
                return True

            return False
        except MQTTConfiguration.DoesNotExist:
            return False
