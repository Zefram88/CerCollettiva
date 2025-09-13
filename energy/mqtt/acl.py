# energy/mqtt/acl.py
# from typing import Any, Dict

from ..models import MQTTCredential, Plant


class MQTTAccessControl:
    @staticmethod
    def check_acl(username: str, topic: str, access_type: str) -> bool:
        """
        Verifica i permessi di accesso per un topic MQTT
        access_type: 'subscribe' o 'publish'
        """
        try:
            cred = MQTTCredential.objects.select_related("user").get(
                mqtt_username=username, is_active=True
            )

            # Verifica se il topic appartiene a un impianto dell'utente
            user_plants = Plant.objects.filter(owner=cred.user)
            for plant in user_plants:
                if topic.startswith(f"cercollettiva/{plant.pod}/"):
                    return True

            return False

        except MQTTCredential.DoesNotExist:
            return False
