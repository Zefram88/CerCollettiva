import logging

from django.db.models.signals import pre_save
from django.dispatch import receiver

from .models import Plant

logger = logging.getLogger("gaudi")


@receiver(pre_save, sender=Plant)
def track_gaudi_changes(sender, instance, **kwargs):
    if not instance.pk:
        return

    old_instance = Plant.objects.get(pk=instance.pk)
    gaudi_fields = [
        "gaudi_request_code",
        "censimp_code",
        "validation_date",
        "gaudi_verified",
        "gaudi_version",
    ]

    changes = []
    for field in gaudi_fields:
        old_value = getattr(old_instance, field)
        new_value = getattr(instance, field)
        if old_value != new_value:
            changes.append(f"{field}: {old_value} -> {new_value}")

    if changes:
        logger.info(
            f"Modifiche dati Gaudì per impianto {instance.pod_code}: {', '.join(changes)}"
        )
