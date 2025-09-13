# energy/models/audit.py
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.utils import timezone


class MQTTAuditLog(models.Model):
    # class Meta:
    #     app_label = "energy"

    OPERATION_TYPES = [
        ("AUTH", "Autenticazione"),
        ("CONNECT", "Connessione"),
        ("DISCONNECT", "Disconnessione"),
        ("SUBSCRIBE", "Sottoscrizione"),
        ("PUBLISH", "Pubblicazione"),
        ("CREDENTIALS_CREATE", "Creazione Credenziali"),
        ("CREDENTIALS_UPDATE", "Aggiornamento Credenziali"),
        ("CREDENTIALS_DELETE", "Eliminazione Credenziali"),
        ("ACL_CHECK", "Verifica ACL"),
    ]

    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    mqtt_username = models.CharField(max_length=50)
    operation = models.CharField(max_length=20, choices=OPERATION_TYPES)
    status = models.BooleanField(default=True)  # True = success, False = failure
    topic = models.CharField(max_length=255, null=True, blank=True)
    client_id = models.CharField(max_length=100, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    details = models.JSONField(encoder=DjangoJSONEncoder, null=True, blank=True)
    retention_date = models.DateTimeField()

    class Meta:
        verbose_name = "Log Audit MQTT"
        verbose_name_plural = "Log Audit MQTT"
        indexes = [
            models.Index(fields=["operation", "timestamp"]),
            models.Index(fields=["mqtt_username", "timestamp"]),
        ]

    def __str__(self):
        return f"{self.operation} - {self.mqtt_username} - {self.timestamp}"

    def save(self, *args, **kwargs):
        # Imposta la data di retention se non specificata (6 mesi di default)
        if not self.retention_date:
            self.retention_date = timezone.now() + timezone.timedelta(days=180)
        # Pulisci eventuali dati sensibili nel topic prima di salvare
        if self.topic:
            self.clean_topic()
        super().save(*args, **kwargs)

    def clean_topic(self):
        """Pulisce eventuali dati sensibili dal topic"""
        parts = self.topic.split("/")
        if len(parts) > 2:
            # Maschera POD o altri identificativi sensibili
            parts[2] = f"{parts[2][:3]}...{parts[2][-3:]}"
            self.topic = "/".join(parts)
