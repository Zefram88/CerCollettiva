# energy/models/energy.py
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from .base import BaseMeasurementModel
from .device import DeviceConfiguration, DeviceMeasurement


class EnergyInterval(models.Model):
    """Misurazioni di energia per intervalli di 15 minuti"""

    class Meta:
        app_label = "energy"

    device = models.ForeignKey(
        "energy.DeviceConfiguration",
        on_delete=models.CASCADE,
        related_name="energy_intervals",
    )
    start_time = models.DateTimeField(help_text="Inizio dell'intervallo di misurazione")
    end_time = models.DateTimeField(help_text="Fine dell'intervallo di misurazione")
    energy_value = models.FloatField(
        help_text="Energia misurata nell'intervallo in kWh",
        validators=[MinValueValidator(0)],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Intervallo Energia"
        verbose_name_plural = "Intervalli Energia"
        ordering = ["-start_time"]
        indexes = [
            models.Index(fields=["device", "start_time"]),
            models.Index(fields=["device", "end_time"]),
            models.Index(fields=["start_time", "end_time"]),
        ]
        unique_together = ["device", "start_time"]

    def __str__(self):
        return (
            f"{self.device.device_id} - "
            f"{self.start_time.strftime('%Y-%m-%d %H:%M')} - "
            f"{self.energy_value:.2f} kWh"
        )

    @property
    def interval_duration(self) -> int:
        """Restituisce la durata dell'intervallo in minuti"""
        return int((self.end_time - self.start_time).total_seconds() / 60)

    def is_valid_interval(self) -> bool:
        """Verifica se l'intervallo è valido (15 minuti)"""
        return self.interval_duration == 15 and self.energy_value >= 0


class EnergyMeasurement(BaseMeasurementModel):
    """Misurazioni di energia"""

    class Meta:
        app_label = "energy"

    MEASUREMENT_TYPES = [
        ("POWER_DRAW", "Prelievo"),
        ("POWER_IN", "Immissione"),
        ("ENERGY_TOTAL", "Energia Totale"),
        ("ENERGY_RETURNED", "Energia Restituita"),
    ]

    UNIT_CHOICES = [
        ("W", "Watt"),
        ("kW", "Kilowatt"),
        ("kWh", "Kilowattora"),
        ("Wh", "Wattora"),
    ]

    measurement_type = models.CharField(
        max_length=20,
        choices=MEASUREMENT_TYPES,
        help_text="Tipo di misurazione energetica",
    )
    value = models.FloatField(
        validators=[MinValueValidator(0)], help_text="Valore della misurazione"
    )
    unit = models.CharField(
        max_length=5, choices=UNIT_CHOICES, default="W", help_text="Unità di misura"
    )
    topic = models.CharField(max_length=255, help_text="Topic MQTT di origine")
    device_measurement = models.ForeignKey(
        DeviceMeasurement, on_delete=models.CASCADE, related_name="energy_measurements"
    )

    class Meta:
        verbose_name = "Misurazione Energia"
        verbose_name_plural = "Misurazioni Energia"
        indexes = [
            models.Index(fields=["measurement_type", "timestamp"]),
            models.Index(fields=["topic", "timestamp"]),
        ]

    def __str__(self):
        return (
            f"{self.measurement_type} - {self.value} {self.unit} - "
            f"{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
        )

    def convert_to_kwh(self) -> float:
        """Converte il valore in kWh"""
        if self.unit == "kWh":
            return self.value
        elif self.unit == "Wh":
            return self.value / 1000
        elif self.unit == "W":
            # Converti assumendo 1 ora di misurazione
            return self.value / 1000
        elif self.unit == "kW":
            return self.value
        return 0


class EnergyAggregate(BaseMeasurementModel):
    """Aggregazioni di misurazioni energetiche"""

    class Meta:
        app_label = "energy"

    PERIOD_CHOICES = [
        ("15M", "15 Minuti"),
        ("1H", "1 Ora"),
        ("1D", "1 Giorno"),
        ("1W", "1 Settimana"),
        ("1M", "1 Mese"),
    ]

    period = models.CharField(
        max_length=3, choices=PERIOD_CHOICES, help_text="Periodo di aggregazione"
    )
    start_time = models.DateTimeField(help_text="Inizio del periodo")
    end_time = models.DateTimeField(help_text="Fine del periodo")
    device = models.ForeignKey(
        "energy.DeviceConfiguration",
        on_delete=models.CASCADE,
        related_name="energy_aggregates",
    )

    # Valori aggregati
    energy_in = models.FloatField(default=0, help_text="Energia immessa in kWh")
    energy_out = models.FloatField(default=0, help_text="Energia prelevata in kWh")
    peak_power = models.FloatField(
        null=True, help_text="Picco di potenza nel periodo in W"
    )
    avg_power = models.FloatField(null=True, help_text="Potenza media nel periodo in W")

    class Meta:
        verbose_name = "Aggregazione Energia"
        verbose_name_plural = "Aggregazioni Energia"
        indexes = [
            models.Index(fields=["device", "period", "start_time"]),
            models.Index(fields=["period", "start_time"]),
        ]
        unique_together = ["device", "period", "start_time"]

    def __str__(self):
        return (
            f"{self.device.device_id} - {self.period} - "
            f"{self.start_time.strftime('%Y-%m-%d %H:%M')}"
        )

    @property
    def net_energy(self) -> float:
        """Calcola l'energia netta (immessa - prelevata)"""
        return self.energy_in - self.energy_out

    def is_complete(self) -> bool:
        """Verifica se l'aggregazione è completa"""
        return self.end_time <= timezone.now()
