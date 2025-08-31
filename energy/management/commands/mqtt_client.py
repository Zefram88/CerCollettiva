from django.core.management.base import BaseCommand
from django.utils import timezone
from energy.mqtt.client import get_mqtt_client
from energy.models import MQTTBroker
import time


class Command(BaseCommand):
    help = "Start or test the MQTT client/service using the active MQTTBroker configuration."

    def add_arguments(self, parser):
        parser.add_argument(
            "--once",
            action="store_true",
            help="Configure and connect once, then exit (for health checks)",
        )

    def handle(self, *args, **options):
        self.stdout.write("Initializing MQTT client...")

        client = get_mqtt_client()
        broker = MQTTBroker.objects.filter(is_active=True).first()

        if not broker:
            self.stdout.write(self.style.WARNING("No active MQTT broker configured"))
            return

        ok = client.configure(
            host=broker.host,
            port=broker.port,
            username=broker.username,
            password=broker.password,
            use_tls=broker.use_tls,
        )
        if not ok:
            self.stdout.write(self.style.ERROR("MQTT client configuration failed"))
            return

        self.stdout.write(self.style.SUCCESS("MQTT client configured"))

        if options.get("once"):
            # Useful for CI/health checks
            self.stdout.write(
                self.style.SUCCESS(
                    f"Connected: {getattr(client, 'is_connected', False)} @ {timezone.now().isoformat()}"
                )
            )
            return

        self.stdout.write("Entering loop. Press Ctrl+C to stop.")
        try:
            while True:
                # Lightweight heartbeat
                status = "connected" if getattr(client, "is_connected", False) else "disconnected"
                self.stdout.write(f"[{timezone.now().strftime('%H:%M:%S')}] MQTT status: {status}")
                time.sleep(30)
        except KeyboardInterrupt:
            self.stdout.write("Stopping MQTT client...")
            try:
                client.stop()
            except Exception:
                pass
            self.stdout.write(self.style.SUCCESS("Stopped"))

