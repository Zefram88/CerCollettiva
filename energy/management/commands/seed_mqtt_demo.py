from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone

from core.models import Plant
from energy.models import DeviceConfiguration
from energy.mqtt.auth import MQTTAuthService


class Command(BaseCommand):
    help = (
        "Crea dati demo per test MQTT: Plant + DeviceConfiguration, "
        "opzionalmente genera credenziali per-device e stampa i topic."
    )

    def add_arguments(self, parser):
        parser.add_argument("pod_code", nargs="?", default="IT001E00000000000000", help="Codice POD")
        parser.add_argument("device_id", nargs="?", default="demo-3em-001", help="ID dispositivo")
        parser.add_argument(
            "--device-type",
            default="SHELLY_PRO_3EM",
            choices=[
                "SHELLY_PRO_3EM",
                "SHELLY_PRO_EM",
                "SHELLY_EM3",
                "SHELLY_EM",
                "SHELLY_PLUS_PM",
                "CUSTOM",
            ],
            help="Tipo dispositivo (imposta vendor/model automaticamente)",
        )
        parser.add_argument("--owner", default=None, help="Username proprietario plant (se assente, viene creato un utente demo)")
        parser.add_argument("--with-creds", action="store_true", help="Genera credenziali MQTT per il device")
        parser.add_argument("--template", default=None, help="Override template topic MQTT (es. cercollettiva/{pod}/{device_id})")

    def handle(self, *args, **opts):
        User = get_user_model()

        # Owner
        owner = None
        if opts.get("owner"):
            owner = User.objects.filter(username=opts["owner"]).first()
        if not owner:
            owner, created = User.objects.get_or_create(
                username="seeduser",
                defaults={
                    "email": "seed@example.org",
                },
            )
            if created:
                owner.set_password("seedpassword")
                owner.save(update_fields=["password"])

        # Plant
        pod = opts["pod_code"].strip()
        plant, created_plant = Plant.objects.get_or_create(
            pod_code=pod,
            defaults={
                "name": f"Demo Plant {pod[-4:]}",
                "plant_type": "PROSUMER",
                "owner": owner,
                "nominal_power": 3.3,
                "connection_voltage": "230V",
                "installation_date": timezone.now().date(),
                "address": "Via Roma 1",
                "city": "Roma",
                "zip_code": "00100",
                "province": "RM",
                "raw_address": "Via Roma 1, 00100 Roma",
            },
        )

        # Device
        device_id = opts["device_id"].strip()
        device, created_device = DeviceConfiguration.objects.get_or_create(
            device_id=device_id,
            defaults={
                "device_type": opts["device_type"],
                "plant": plant,
                "is_active": True,
            },
        )
        # Assicura associazione al plant anche se già esisteva
        if device.plant_id != plant.id:
            device.plant = plant
        
        # Imposta template MQTT coerente con gli handler (prefisso 'cercollettiva')
        if opts.get("template"):
            template = opts["template"]
        else:
            template = f"cercollettiva/{plant.pod_code}/{device.device_id}"
        device.mqtt_topic_template = template
        device.save()

        self.stdout.write(self.style.SUCCESS("Dati demo creati/aggiornati"))
        self.stdout.write(f"  Plant:   {plant.name} (POD={plant.pod_code})")
        self.stdout.write(f"  Device:  {device.device_id} ({device.device_type})")
        self.stdout.write(f"  MQTT template: {device.mqtt_topic_template}")

        # Topic di interesse
        topics = device.get_mqtt_topics()
        if topics:
            self.stdout.write("  Topic suggeriti:")
            for t in topics:
                self.stdout.write(f"    - {t}")

        # Credenziali per-device
        if opts.get("with_creds"):
            username, password = MQTTAuthService.create_device_credentials(device)
            self.stdout.write(self.style.WARNING("Credenziali per-device generate:"))
            self.stdout.write(f"  Username: {username}")
            self.stdout.write(f"  Password: {password}")
            base = (device.mqtt_topic_template or "").split("/status")[0]
            if base:
                self.stdout.write("  Esempio ACL Mosquitto:")
                self.stdout.write(f"    topic read {base}/#")
                self.stdout.write(f"    topic write {base}/status/#")

        # Payload di esempio
        self.stdout.write("")
        self.stdout.write("Esempi payload:")
        self.stdout.write("  em:0")
        self.stdout.write("    {\"total_act_power\": 1234.5, \"total_pf\": 0.97, \"a_voltage\": 230.1, \"a_current\": 5.4}")
        self.stdout.write("  emdata:0")
        self.stdout.write("    {\"total_act\": 123456.0}")

