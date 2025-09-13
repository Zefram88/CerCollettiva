from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import Plant
from energy.models import DeviceConfiguration


class Command(BaseCommand):
    help = "Debug device and plant configurations"

    def handle(self, *args, **options):
        self.stdout.write("\n=== Active Plants ===")
        plants = Plant.objects.all()

        for plant in plants:
            self.stdout.write(f"\nPlant ID: {plant.id}")
            self.stdout.write(f"Name: {plant.name}")
            self.stdout.write(f"POD: {plant.pod_code}")
            self.stdout.write(f"Active: {plant.is_active}")

            devices = DeviceConfiguration.objects.filter(plant=plant)
            self.stdout.write("\nAssociated Devices:")
            for device in devices:
                self.stdout.write(
                    f"""
  - Device DB ID: {device.id}
    Device ID: {device.device_id}
    MQTT Template: {device.mqtt_topic_template}
    Active: {device.is_active}
    Last Seen: {device.last_seen if device.last_seen else 'Never'}
"""
                )

            # Get latest measurement for this plant
            latest_measurement = (
                device.measurements.order_by("-timestamp").first()
                if device.measurements.exists()
                else None
            )
            if latest_measurement:
                self.stdout.write(
                    f"""
Latest Measurement:
  ID: {latest_measurement.id}
  Timestamp: {timezone.localtime(latest_measurement.timestamp)}
  Power: {latest_measurement.power}W
  Device: {latest_measurement.device_id}
  Plant: {latest_measurement.plant_id}
"""
                )
            else:
                self.stdout.write("\nNo measurements found for this plant")

            self.stdout.write("-" * 50)
