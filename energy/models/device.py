# energy/models/device.py
import logging
import time

from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models

# from core.main_models import Plant
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .base import BaseMeasurementModel, BaseTimestampModel

logger = logging.getLogger(__name__)


class DeviceType(models.Model):
    """
    Modello per la definizione dei tipi di dispositivo supportati
    """

    class Meta:
        app_label = "energy"

    name = models.CharField("Nome", max_length=100, unique=True)
    vendor = models.CharField("Produttore", max_length=100)
    model = models.CharField("Modello", max_length=100)
    description = models.TextField("Descrizione", blank=True)
    is_active = models.BooleanField("Attivo", default=True)

    # Configurazione misure supportate
    supports_voltage = models.BooleanField("Supporta Voltaggio", default=False)
    supports_current = models.BooleanField("Supporta Corrente", default=False)
    supports_power = models.BooleanField("Supporta Potenza", default=False)
    supports_energy = models.BooleanField("Supporta Energia", default=False)
    supports_frequency = models.BooleanField("Supporta Frequenza", default=False)
    supports_power_factor = models.BooleanField(
        "Supporta Fattore di Potenza", default=False
    )

    # Configurazione MQTT
    mqtt_topic_template = models.CharField(
        "Template Topic MQTT",
        max_length=255,
        help_text="Usa {serial} per il numero seriale del dispositivo",
    )
    mqtt_payload_format = models.JSONField(
        "Formato Payload MQTT",
        help_text="Definizione della struttura del payload MQTT",
        default=dict,
    )

    class Meta:
        verbose_name = "Tipo Dispositivo"
        verbose_name_plural = "Tipi Dispositivo"
        unique_together = ["vendor", "model"]

    def __str__(self):
        return f"{self.vendor} {self.model}"


class Device(models.Model):
    """
    Modello per i dispositivi installati
    """

    class Meta:
        app_label = "energy"

    device_type = models.ForeignKey(
        DeviceType, on_delete=models.PROTECT, verbose_name="Tipo Dispositivo"
    )
    serial_number = models.CharField(
        "Numero Seriale",
        max_length=100,
        validators=[
            RegexValidator(
                regex=r"^[A-Za-z0-9_-]+$",
                message="Il numero seriale può contenere solo lettere, numeri, underscore e trattini",
            )
        ],
    )
    name = models.CharField("Nome", max_length=100)
    description = models.TextField("Descrizione", blank=True)
    installation_date = models.DateField("Data Installazione")
    is_active = models.BooleanField("Attivo", default=True)

    # Parametri di connessione
    mqtt_topic_override = models.CharField(
        "Override Topic MQTT",
        max_length=255,
        blank=True,
        help_text="Lasciare vuoto per usare il template del tipo dispositivo",
    )

    # Configurazione aggiuntiva specifica del dispositivo
    config = models.JSONField(
        "Configurazione",
        default=dict,
        help_text="Configurazione specifica del dispositivo in formato JSON",
    )

    class Meta:
        verbose_name = "Dispositivo"
        verbose_name_plural = "Dispositivi"
        unique_together = ["device_type", "serial_number"]

    def __str__(self):
        return f"{self.name} ({self.device_type})"

    def get_mqtt_topic(self):
        """Restituisce il topic MQTT effettivo per il dispositivo"""
        if self.mqtt_topic_override:
            return self.mqtt_topic_override
        return self.device_type.mqtt_topic_template.format(serial=self.serial_number)


class DeviceConfiguration(BaseTimestampModel):
    """Configurazione dei dispositivi"""

    class Meta:
        app_label = "energy"

    # Costanti per vendor
    VENDOR_SHELLY = "SHELLY"
    VENDOR_CUSTOM = "CUSTOM"

    VENDOR_CHOICES = [
        (VENDOR_SHELLY, "Shelly"),
        (VENDOR_CUSTOM, "Custom"),
    ]

    DEVICE_TYPES = [
        ("SHELLY_PRO_3EM", "Shelly Pro 3EM"),
        ("SHELLY_PRO_EM", "Shelly Pro EM"),
        ("SHELLY_EM3", "Shelly 3EM"),
        ("SHELLY_EM", "Shelly EM"),
        ("SHELLY_PLUS_PM", "Shelly Plus PM"),
        ("CUSTOM", "Custom"),
    ]

    DEVICE_TYPE_MAPPING = {
        "SHELLY_PRO_3EM": {"vendor": VENDOR_SHELLY, "model": "pro_3em"},
        "SHELLY_PRO_EM": {"vendor": VENDOR_SHELLY, "model": "pro_em"},
        "SHELLY_EM3": {"vendor": VENDOR_SHELLY, "model": "em3"},
        "SHELLY_EM": {"vendor": VENDOR_SHELLY, "model": "em"},
        "SHELLY_PLUS_PM": {"vendor": VENDOR_SHELLY, "model": "plus_pm"},
        "CUSTOM": {"vendor": VENDOR_CUSTOM, "model": "custom"},
    }

    # Campi base
    device_id = models.CharField(max_length=100, unique=True)
    name = models.CharField("Nome", max_length=100, default="")
    device_type = models.CharField(
        max_length=50, choices=DEVICE_TYPES, default="CUSTOM"
    )
    vendor = models.CharField(
        max_length=50, choices=VENDOR_CHOICES, default=VENDOR_CUSTOM
    )
    model = models.CharField(max_length=50, default="custom")
    plant = models.ForeignKey(
        "core.Plant", on_delete=models.CASCADE, related_name="devices"
    )
    last_energy_total = models.FloatField(
        help_text="Ultimo valore di energia totale ricevuto", null=True, blank=True
    )

    # Configurazione e stato
    mqtt_topic_template = models.CharField(max_length=255, blank=True, null=True)
    firmware_version = models.CharField(max_length=50, blank=True, null=True)
    last_seen = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Dispositivo"
        verbose_name_plural = "Dispositivi"
        indexes = [
            models.Index(fields=["device_type", "vendor"]),
            models.Index(fields=["last_seen", "is_active"]),
        ]

    def __str__(self):
        return f"{self.device_id} ({self.get_device_type_display()})"

    def save(self, *args, **kwargs):
        """Applica il mapping device_type -> vendor/model e salva"""
        if self.device_type in self.DEVICE_TYPE_MAPPING:
            mapping = self.DEVICE_TYPE_MAPPING[self.device_type]
            self.vendor = mapping["vendor"]
            self.model = mapping["model"]
        else:
            self.vendor = self.VENDOR_CUSTOM
            self.model = "custom"

        if not self.device_type:
            self.device_type = "CUSTOM"

        super().save(*args, **kwargs)

    @property
    def device_key(self) -> str:
        """Restituisce la chiave per il device registry"""
        return f"{self.vendor}_{self.model}".lower()

    def get_device_instance(self):
        """Ottiene l'istanza del dispositivo dal registry"""
        from ..devices.registry import DeviceRegistry

        return DeviceRegistry.get_device(self.device_type)

    @property
    def is_online(self) -> bool:
        """Verifica se il dispositivo è online (ultimi 5 minuti)"""
        if not self.last_seen:
            return False
        return (timezone.now() - self.last_seen).total_seconds() < 300

    def update_last_seen(self):
        """Aggiorna il timestamp dell'ultima comunicazione"""
        self.last_seen = timezone.now()
        self.save(update_fields=["last_seen", "updated_at"])

    @property
    def status(self) -> str:
        """Restituisce lo stato corrente del dispositivo"""
        if not self.is_active:
            return "disabled"
        if not self.is_online:
            return "offline"
        measurement = self.get_latest_measurement()
        if measurement and measurement.power > 0:
            return "active"
        return "idle"

    def get_latest_measurement(self):
        """Recupera l'ultima misurazione"""
        return self.measurements.select_related("plant").first()

    def get_measurements_in_range(self, start_time, end_time):
        """Recupera le misurazioni in un intervallo"""
        return self.measurements.filter(
            timestamp__gte=start_time, timestamp__lte=end_time
        ).select_related("plant")

    def get_mqtt_topics(self):
        """Restituisce la lista dei topic MQTT per questo dispositivo"""
        topics = []

        try:
            # Se è specificato un template MQTT personalizzato
            if self.mqtt_topic_template:
                base_topic = self.mqtt_topic_template.rstrip("/")
                topics.extend([f"{base_topic}/status/#"])

                # Aggiungi topic specifici per Shelly
                if self.vendor == self.VENDOR_SHELLY:
                    topics.extend(
                        [f"{base_topic}/status/em:0", f"{base_topic}/status/emdata:0"]
                    )
                    logger.info(
                        f"MQTT topics generated by template for device: {self.device_id} - {topics}"
                    )

            # Se non c'è un template, genera i topic in base al vendor e POD
            elif self.plant and hasattr(self.plant, "pod_code"):
                vendor_prefix = self.vendor.replace("_", "")
                base_topic = f"{vendor_prefix}/{self.plant.pod_code}/{self.device_id}"

                if self.vendor == self.VENDOR_SHELLY:
                    topics.extend(
                        [f"{base_topic}/status/em:0", f"{base_topic}/status/emdata:0"]
                    )
                else:
                    topics.extend(
                        [
                            f"{base_topic}/status/#",
                            f"{base_topic}/power/#",
                            f"{base_topic}/energy/#",
                        ]
                    )
                logger.info(
                    f"MQTT topics generated by vendor and pod_code for device: {self.device_id} - {topics}"
                )

            logger.info(f"Generated MQTT topics for device {self.device_id}: {topics}")
            return topics

        except Exception as e:
            logger.error(
                f"Error generating MQTT topics for device {self.device_id}: {str(e)}"
            )
            return ["cercollettiva/+/+/value"]  # Fallback a topic wildcard


class DeviceMeasurement(BaseMeasurementModel):
    """Misurazione principale del dispositivo"""

    class Meta:
        app_label = "energy"

    MEASUREMENT_TYPES = [
        ("DRAWN_POWER", "Potenza Prelevata"),
        ("DRAWN_ENERGY", "Energia Prelevata"),
        ("INJECTED_POWER", "Potenza Immessa"),
        ("INJECTED_ENERGY", "Energia Immessa"),
        ("PRODUCTION_POWER", "Potenza Prodotta"),
        ("PRODUCTION_ENERGY", "Energia Prodotta"),
    ]

    plant = models.ForeignKey(
        "core.Plant",  # Usiamo una stringa per riferirci al modello Plant
        on_delete=models.CASCADE,
        related_name="device_measurements",
        db_index=True,  # Ottimizza le query per plant
    )
    device = models.ForeignKey(
        DeviceConfiguration,
        on_delete=models.CASCADE,
        related_name="measurements",
        db_index=True,  # Ottimizza le query per device
    )
    measurement_type = models.CharField(
        max_length=20,
        choices=MEASUREMENT_TYPES,
        db_index=True,  # Ottimizza le query per type
    )
    power = models.FloatField(
        help_text="Potenza attiva in W",
        validators=[MinValueValidator(-1000000), MaxValueValidator(1000000)],
    )
    voltage = models.FloatField(
        help_text="Tensione in V",
        validators=[MinValueValidator(0), MaxValueValidator(500)],
    )
    current = models.FloatField(
        help_text="Corrente in A",
        validators=[MinValueValidator(-1000), MaxValueValidator(1000)],
    )
    energy_total = models.FloatField(
        help_text="Energia totale in kWh", validators=[MinValueValidator(0)], default=0
    )
    energy = models.FloatField(
        help_text="Energia in kWh", validators=[MinValueValidator(0)], default=0
    )
    frequency = models.FloatField(
        help_text="Frequenza in Hz",
        validators=[MinValueValidator(45), MaxValueValidator(65)],
        default=50,
        null=True,
        blank=True,
    )
    raw_data = models.JSONField(
        help_text="Dati grezzi in formato JSON", default=dict, blank=True
    )
    power_factor = models.FloatField(
        help_text="Fattore di potenza",
        validators=[MinValueValidator(-1), MaxValueValidator(1)],
        null=True,
        blank=True,  # Permette il campo vuoto nei form
    )

    class Meta:
        verbose_name = "Misurazione Dispositivo"
        verbose_name_plural = "Misurazioni Dispositivi"
        indexes = [
            models.Index(fields=["device", "measurement_type", "timestamp"]),
            models.Index(fields=["timestamp", "device"]),
            models.Index(
                fields=["plant", "timestamp"]
            ),  # Utile per query aggregate per impianto
            models.Index(
                fields=["measurement_type", "timestamp"]
            ),  # Utile per query per tipo
        ]
        ordering = ["-timestamp"]
        get_latest_by = "timestamp"
        # Aggiungiamo vincoli per GDPR
        permissions = [
            ("can_view_sensitive_data", "Can view sensitive measurement data"),
            ("can_export_measurements", "Can export measurement data"),
        ]

    def __str__(self):
        return f"{self.device.device_id} - {self.measurement_type} - {self.timestamp:%Y-%m-%d %H:%M:%S}"

    def clean(self):
        """Validazione custom del modello"""
        super().clean()
        if self.power_factor and not -1 <= self.power_factor <= 1:
            raise ValidationError(
                {
                    "power_factor": "Il fattore di potenza deve essere compreso tra -1 e 1"
                }
            )
        if self.power and abs(self.power) > 1000000:
            raise ValidationError({"power": "La potenza non può superare ±1MW"})

    @property
    def apparent_power(self) -> float:
        """Calcola la potenza apparente in VA"""
        return abs(self.voltage * self.current)

    @property
    def reactive_power(self) -> float:
        """Calcola la potenza reattiva in VAR"""
        if self.power_factor:
            return self.apparent_power * (1 - self.power_factor**2) ** 0.5
        return 0

    @property
    def power_kw(self) -> float:
        """Restituisce la potenza in kW"""
        return self.power / 1000.0 if self.power else 0

    def get_measurement_direction(self) -> str:
        """Determina la direzione del flusso di potenza"""
        if not self.power:
            return "NEUTRAL"
        return "IMPORT" if self.power < 0 else "EXPORT"

    def anonymize(self):
        """Anonimizza i dati sensibili per GDPR"""
        self.device = None
        self.plant = None
        self.save()


class DeviceMeasurementDetail(BaseMeasurementModel):
    """Dettagli per fase della misurazione"""

    class Meta:
        app_label = "energy"

    PHASE_CHOICES = [("a", "Fase A"), ("b", "Fase B"), ("c", "Fase C"), ("n", "Neutro")]

    measurement = models.ForeignKey(
        DeviceMeasurement, on_delete=models.CASCADE, related_name="phase_details"
    )
    phase = models.CharField(
        max_length=1, choices=PHASE_CHOICES, help_text="Identificativo della fase"
    )

    # Valori per fase
    voltage = models.FloatField(
        help_text="Tensione di fase in V",
        validators=[MinValueValidator(0), MaxValueValidator(500)],
    )
    current = models.FloatField(
        help_text="Corrente di fase in A",
        validators=[MinValueValidator(-1000), MaxValueValidator(1000)],
    )
    power = models.FloatField(
        help_text="Potenza attiva di fase in W",
        validators=[MinValueValidator(-1000000), MaxValueValidator(1000000)],
    )
    power_factor = models.FloatField(
        help_text="Fattore di potenza di fase",
        validators=[MinValueValidator(-1), MaxValueValidator(1)],
        null=True,
    )
    frequency = models.FloatField(
        help_text="Frequenza in Hz",
        validators=[MinValueValidator(45), MaxValueValidator(65)],
        default=50,
    )

    class Meta:
        verbose_name = "Dettaglio Fase"
        verbose_name_plural = "Dettagli Fase"
        unique_together = ["measurement", "phase"]
        ordering = ["phase"]  # Ordina per identificativo di fase
        indexes = [
            models.Index(fields=["measurement", "phase"]),
        ]

    def __str__(self):
        return f"{self.measurement} - Fase {self.phase}"

    @property
    def apparent_power(self) -> float:
        """Calcola la potenza apparente di fase in VA"""
        return abs(self.voltage * self.current)

    @property
    def reactive_power(self) -> float:
        """Calcola la potenza reattiva di fase in VAR"""
        if self.power_factor:
            return self.apparent_power * (1 - self.power_factor**2) ** 0.5
        return 0

    def get_phase_power_metrics(self) -> dict:
        """Restituisce tutte le metriche di potenza per la fase"""
        return {
            "active_power": self.power,
            "apparent_power": self.apparent_power,
            "reactive_power": self.reactive_power,
            "power_factor": self.power_factor,
            "voltage": self.voltage,
            "current": self.current,
            "frequency": self.frequency,
        }

    def validate_phase_data(self) -> bool:
        """Valida i dati della fase"""
        try:
            if not all(
                [
                    isinstance(self.voltage, (int, float)),
                    isinstance(self.current, (int, float)),
                    isinstance(self.power, (int, float)),
                ]
            ):
                return False

            if not (
                0 <= self.voltage <= 500
                and -1000 <= self.current <= 1000
                and -1000000 <= self.power <= 1000000
            ):
                return False

            if self.power_factor is not None and not -1 <= self.power_factor <= 1:
                return False

            if self.frequency and not 45 <= self.frequency <= 65:
                return False

            return True
        except Exception:
            return False


@receiver([post_save, post_delete], sender=DeviceConfiguration)
def handle_device_configuration_change(sender, instance, created=False, **kwargs):
    """Gestisce i cambiamenti nelle configurazioni dei dispositivi"""
    try:
        # Evita refresh per aggiornamenti frequenti
        cache_key = f"device_config_refresh_{instance.id}"
        last_refresh = cache.get(cache_key)

        if last_refresh and time.time() - last_refresh < 60:
            logger.debug("Skipping refresh - too soon")
            return

        # Evita refresh per gli aggiornamenti di last_seen e updated_at
        if kwargs.get("update_fields") in [
            {"last_seen"},
            {"last_seen", "updated_at"},
            {"updated_at", "last_seen"},
        ]:
            return

        from ..mqtt.client import get_mqtt_client

        client = get_mqtt_client()
        if client and client.is_connected:
            client.refresh_configurations()
            logger.info(
                f"MQTT configurations refreshed after device change: {instance.device_id}"
            )

        # Aggiorna timestamp ultimo refresh
        cache.set(cache_key, time.time(), 300)

    except Exception as e:
        logger.error(f"Error handling device configuration change: {e}")
