# energy/devices/models.py
from django.db import models
from django.utils import timezone

from ..models.base import BaseTimestampModel


class DeviceConfiguration(BaseTimestampModel):
    """Configurazione dei dispositivi"""

    DEVICE_TYPES = [
        ("SHELLY_PRO_3EM", "Shelly Pro 3EM"),
        ("SHELLY_PRO_EM", "Shelly Pro EM"),
        ("SHELLY_EM3", "Shelly 3EM"),
        ("SHELLY_EM", "Shelly EM"),
        ("SHELLY_PLUS_PM", "Shelly Plus PM"),
        ("CUSTOM_DEVICE", "Dispositivo Custom"),
    ]

    device_id = models.CharField(max_length=100, unique=True)
    device_type = models.CharField(max_length=50, choices=DEVICE_TYPES)
    vendor = models.CharField(max_length=50)
    model = models.CharField(max_length=50)
    mqtt_topic_template = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    last_seen = models.DateTimeField(null=True, blank=True)
    plant = models.ForeignKey(
        "core.Plant", on_delete=models.CASCADE, related_name="devices"
    )

    def get_mqtt_topics(self) -> List[str]:
        """Restituisce i topic MQTT da sottoscrivere"""
        try:
            device = DeviceRegistry.get_device_by_vendor_model(self.vendor, self.model)
            if device and self.mqtt_topic_template:
                return device.get_topics(self.mqtt_topic_template)
            return []
        except Exception as e:
            logger.error(f"Errore get_mqtt_topics: {str(e)}")
            return []

    class Meta:
        verbose_name = "Device Configuration"
        verbose_name_plural = "Device Configurations"
        ordering = ["device_id"]

    def __str__(self):
        return f"{self.device_id} ({self.device_type})"

    @property
    def is_online(self):
        """Verifica se il dispositivo è online (visto negli ultimi 5 minuti)"""
        return (
            self.last_seen is not None
            and (timezone.now() - self.last_seen).total_seconds() < 300  # 5 minuti
        )
