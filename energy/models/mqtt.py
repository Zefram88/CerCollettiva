# energy/models/mqtt.py
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from encrypted_model_fields.fields import EncryptedCharField


class MQTTBroker(models.Model):
    """
    Configurazione del broker MQTT centrale.
    Utilizzato dal sistema per connettersi al broker che riceve i dati dai dispositivi.
    """

    # class Meta:
    #     app_label = "energy"

    name = models.CharField("Nome configurazione", max_length=100)
    host = models.CharField("Host", max_length=255)
    port = models.IntegerField(
        "Porta",
        validators=[MinValueValidator(1), MaxValueValidator(65535)],
        default=1883,
    )
    username = models.CharField("Username", max_length=255, blank=True, null=True)
    password = models.CharField("Password", max_length=255, blank=True, null=True)
    is_active = models.BooleanField("Attivo", default=True)
    use_tls = models.BooleanField("Usa TLS", default=True)
    verify_cert = models.BooleanField("Verifica certificato", default=True)
    ca_cert = models.FileField(
        "Certificato CA", upload_to="mqtt/certs/", null=True, blank=True
    )
    keepalive = models.IntegerField(
        "Keep Alive (secondi)",
        default=60,
        validators=[MinValueValidator(10), MaxValueValidator(600)],
    )
    qos_level = models.IntegerField(
        "Livello QoS",
        default=1,
        validators=[MinValueValidator(0), MaxValueValidator(2)],
    )
    tls_cert = models.CharField(
        "Certificato TLS", max_length=500, blank=True, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField("Note", blank=True)

    class Meta:
        verbose_name = "Configurazione Broker MQTT"
        verbose_name_plural = "Configurazioni Broker MQTT"
        db_table = "energy_mqtt_broker"

    def __str__(self):
        return f"{self.name} ({self.host}:{self.port})"

    def save(self, *args, **kwargs):
        if self.is_active:
            # Mantiene una sola configurazione attiva
            type(self).objects.exclude(id=self.id).update(is_active=False)
        super().save(*args, **kwargs)

    def clean(self):
        if self.use_tls and not self.verify_cert and not self.ca_cert:
            raise ValidationError(
                {
                    "ca_cert": (
                        "Il certificato CA è richiesto quando TLS è attivo ma "
                        "la verifica del certificato è disabilitata"
                    )
                }
            )


class MQTTConfiguration(models.Model):
    """
    Configurazione di una connessione MQTT per un dispositivo specifico.
    Utilizzato per gestire le credenziali e le impostazioni di connessione
    per singoli dispositivi.
    """

    # class Meta:
    #     app_label = "energy"

    device = models.OneToOneField(
        "energy.DeviceConfiguration",
        on_delete=models.CASCADE,
        related_name="mqtt_config",
        verbose_name="Dispositivo",
    )
    mqtt_username = models.CharField("Username MQTT", max_length=255, unique=True)
    mqtt_password = EncryptedCharField("Password MQTT", max_length=255)
    last_connected = models.DateTimeField("Ultima connessione", null=True, blank=True)
    is_active = models.BooleanField("Attivo", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configurazione MQTT Dispositivo"
        verbose_name_plural = "Configurazioni MQTT Dispositivi"
        db_table = "energy_mqtt_configuration"
        indexes = [
            models.Index(fields=["mqtt_username"]),
            models.Index(fields=["is_active", "last_connected"]),
        ]

    def __str__(self):
        return f"MQTT Config: {self.device.device_id} ({self.mqtt_username})"

    def update_last_connected(self):
        """Aggiorna il timestamp dell'ultima connessione"""
        self.last_connected = timezone.now()
        self.save(update_fields=["last_connected", "updated_at"])

    @property
    def is_connected(self):
        """
        Verifica se il dispositivo è considerato connesso
        (ultima connessione negli ultimi 5 minuti)
        """
        if not self.last_connected:
            return False
        return self.last_connected >= timezone.now() - timezone.timedelta(minutes=5)

    def generate_client_id(self):
        """Genera un ID cliente univoco per la connessione MQTT"""
        return f"cercollettiva-{self.device.device_id}-{timezone.now().timestamp()}"
