# energy/models/base.py
# from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class BaseTimestampModel(models.Model):
    """Modello base con timestamp di creazione e modifica"""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class BaseMeasurementModel(BaseTimestampModel):
    """Modello base per tutte le misurazioni"""

    QUALITY_CHOICES = [
        ("GOOD", "Good"),
        ("UNCERTAIN", "Uncertain"),
        ("BAD", "Bad"),
        ("MISSING", "Missing"),
    ]

    timestamp = models.DateTimeField(
        default=timezone.now, db_index=True, help_text="Timestamp della misurazione"
    )
    quality = models.CharField(
        max_length=10,
        choices=QUALITY_CHOICES,
        default="GOOD",
        help_text="Qualità della misurazione",
    )

    class Meta:
        abstract = True
        ordering = ["-timestamp"]

    def is_valid(self) -> bool:
        """Verifica se la misurazione è valida"""
        return self.quality == "GOOD"

    @property
    def age(self) -> float:
        """Calcola l'età della misurazione in secondi"""
        return (timezone.now() - self.timestamp).total_seconds()
