from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from energy.models import DeviceConfiguration
from energy.mqtt.auth import MQTTAuthService


class Command(BaseCommand):
    help = "Genera credenziali MQTT per un dispositivo (DeviceConfiguration) e le stampa."

    def add_arguments(self, parser):
        parser.add_argument("device_id", type=str, help="ID del dispositivo (DeviceConfiguration.device_id)")
        parser.add_argument(
            "--acl",
            action="store_true",
            help="Stampa anche una riga di esempio per ACL Mosquitto basata sul template MQTT del device",
        )

    def handle(self, *args, **options):
        device_id = options["device_id"].strip()

        try:
            device = DeviceConfiguration.objects.select_related("plant").get(device_id=device_id)
        except DeviceConfiguration.DoesNotExist:
            raise CommandError(f"DeviceConfiguration con device_id='{device_id}' non trovato")

        username, password = MQTTAuthService.create_device_credentials(device)

        self.stdout.write(self.style.SUCCESS("Credenziali MQTT generate"))
        self.stdout.write(f"  Device ID: {device.device_id}")
        self.stdout.write(f"  Username:  {username}")
        self.stdout.write(f"  Password:  {password}")
        self.stdout.write(f"  Timestamp: {timezone.now().isoformat()}")

        if options.get("acl"):
            base_topic = (device.mqtt_topic_template or "").split("/status")[0]
            if not base_topic and getattr(device, "plant", None) and getattr(device.plant, "pod_code", None):
                vendor_prefix = device.vendor.replace("_", "")
                base_topic = f"{vendor_prefix}/{device.plant.pod_code}/{device.device_id}"

            if base_topic:
                self.stdout.write("")
                self.stdout.write(self.style.WARNING("Esempio ACL Mosquitto (topic read-only/publish sui propri topic):"))
                self.stdout.write(f"  topic read {base_topic}/#")
                self.stdout.write(f"  topic write {base_topic}/status/#")
            else:
                self.stdout.write("")
                self.stdout.write(self.style.WARNING("Nessun base_topic deducibile; specifica mqtt_topic_template o plant.pod_code"))

