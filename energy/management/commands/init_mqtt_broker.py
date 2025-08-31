from django.core.management.base import BaseCommand
from django.conf import settings
from energy.models import MQTTBroker


class Command(BaseCommand):
    help = "Create or update the active MQTTBroker from environment variables."

    def handle(self, *args, **options):
        host = getattr(settings, 'MQTT_SETTINGS', {}).get('BROKER_HOST') or settings.MQTT_SETTINGS.get('BROKER_HOST')
        port = getattr(settings, 'MQTT_SETTINGS', {}).get('BROKER_PORT') or settings.MQTT_SETTINGS.get('BROKER_PORT')
        username = getattr(settings, 'MQTT_SETTINGS', {}).get('USERNAME') or settings.MQTT_SETTINGS.get('USERNAME')
        password = getattr(settings, 'MQTT_SETTINGS', {}).get('PASSWORD') or settings.MQTT_SETTINGS.get('PASSWORD')
        use_tls = getattr(settings, 'MQTT_SETTINGS', {}).get('TLS_ENABLED') or settings.MQTT_SETTINGS.get('TLS_ENABLED')

        if not host or not port:
            self.stdout.write(self.style.ERROR('MQTT host/port not found in settings.MQTT_SETTINGS'))
            return

        # Ensure only one active broker
        MQTTBroker.objects.update(is_active=False)
        broker, _ = MQTTBroker.objects.get_or_create(
            host=host,
            port=port,
            defaults={
                'name': 'Active Broker',
                'username': username or '',
                'password': password or '',
                'use_tls': bool(use_tls),
                'is_active': True,
            }
        )
        # Update fields if needed
        broker.name = broker.name or 'Active Broker'
        broker.username = username or ''
        broker.password = password or ''
        broker.use_tls = bool(use_tls)
        broker.is_active = True
        broker.save()

        self.stdout.write(self.style.SUCCESS(
            f"Active MQTTBroker set to {broker.host}:{broker.port} (TLS={broker.use_tls})"
        ))

