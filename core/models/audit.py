# core/models/audit.py
from django.db import models
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

class EconomicTransactionAudit(models.Model):
    """
    Audit trail per transazioni economiche - REQUISITO NORMATIVO CER
    Traccia tutte le modifiche alle transazioni economiche per compliance
    """
    
    OPERATION_TYPES = [
        ('CREATE', 'Creazione'),
        ('UPDATE', 'Aggiornamento'),
        ('DELETE', 'Eliminazione'),
        ('APPROVE', 'Approvazione'),
        ('REJECT', 'Rifiuto'),
        ('PROCESS', 'Elaborazione'),
        ('CANCEL', 'Annullamento'),
    ]
    
    # Riferimento alla transazione (se esiste ancora)
    transaction_id = models.PositiveIntegerField(
        "ID Transazione",
        help_text="ID della transazione modificata"
    )
    transaction_type = models.CharField(
        "Tipo Transazione",
        max_length=50,
        help_text="Tipo di transazione (BENEFIT_DISTRIBUTION, GSE_PAYMENT, etc.)"
    )
    
    # Dettagli operazione
    operation_type = models.CharField(
        "Tipo Operazione",
        max_length=20,
        choices=OPERATION_TYPES
    )
    operation_timestamp = models.DateTimeField(
        "Timestamp Operazione",
        auto_now_add=True,
        db_index=True
    )
    
    # Utente che ha eseguito l'operazione
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Utente",
        help_text="Utente che ha eseguito l'operazione"
    )
    
    # Dati della transazione prima e dopo la modifica
    old_values = models.JSONField(
        "Valori Precedenti",
        default=dict,
        encoder=DjangoJSONEncoder,
        help_text="Valori prima della modifica"
    )
    new_values = models.JSONField(
        "Nuovi Valori",
        default=dict,
        encoder=DjangoJSONEncoder,
        help_text="Valori dopo la modifica"
    )
    
    # Informazioni contestuali
    ip_address = models.GenericIPAddressField(
        "Indirizzo IP",
        null=True,
        blank=True,
        help_text="IP da cui è stata eseguita l'operazione"
    )
    user_agent = models.TextField(
        "User Agent",
        blank=True,
        help_text="Browser/applicazione utilizzata"
    )
    session_id = models.CharField(
        "ID Sessione",
        max_length=40,
        blank=True,
        help_text="ID della sessione"
    )
    
    # Motivo della modifica
    reason = models.TextField(
        "Motivo",
        blank=True,
        help_text="Motivazione della modifica"
    )
    
    # Conformità normativa - ritenzione 2 anni
    retention_date = models.DateTimeField(
        "Data Scadenza",
        help_text="Data oltre la quale il record può essere eliminato (2 anni)"
    )
    
    class Meta:
        verbose_name = "Audit Transazione Economica"
        verbose_name_plural = "Audit Transazioni Economiche"
        ordering = ['-operation_timestamp']
        indexes = [
            models.Index(fields=['transaction_id', 'operation_timestamp']),
            models.Index(fields=['user', 'operation_timestamp']),
            models.Index(fields=['operation_type']),
            models.Index(fields=['retention_date']),
        ]
    
    def __str__(self):
        return f"Audit {self.operation_type} - Transazione {self.transaction_id} - {self.operation_timestamp}"
    
    def save(self, *args, **kwargs):
        # Imposta data di scadenza a 2 anni dalla creazione
        if not self.retention_date:
            self.retention_date = timezone.now() + timezone.timedelta(days=730)  # 2 anni
        super().save(*args, **kwargs)
    
    @classmethod
    def log_transaction_operation(cls, transaction, operation_type, user=None, 
                                 old_values=None, new_values=None, reason="", 
                                 ip_address=None, user_agent="", session_id=""):
        """
        Helper per creare record di audit per transazioni
        """
        return cls.objects.create(
            transaction_id=transaction.id if transaction else 0,
            transaction_type=transaction.transaction_type if transaction else "UNKNOWN",
            operation_type=operation_type,
            user=user,
            old_values=old_values or {},
            new_values=new_values or {},
            reason=reason,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
        )


class CERDocumentAudit(models.Model):
    """
    Audit trail per documenti CER - REQUISITO NORMATIVO
    Traccia tutte le operazioni sui documenti della CER
    """
    
    OPERATION_TYPES = [
        ('UPLOAD', 'Caricamento'),
        ('UPDATE', 'Aggiornamento'),
        ('DELETE', 'Eliminazione'),
        ('DOWNLOAD', 'Download'),
        ('VIEW', 'Visualizzazione'),
        ('APPROVE', 'Approvazione'),
        ('REJECT', 'Rifiuto'),
    ]
    
    DOCUMENT_TYPES = [
        ('STATUTE', 'Statuto'),
        ('REGULATION', 'Regolamento'),
        ('MEMBERSHIP', 'Documentazione Adesione'),
        ('FINANCIAL', 'Documentazione Finanziaria'),
        ('TECHNICAL', 'Documentazione Tecnica'),
        ('LEGAL', 'Documentazione Legale'),
        ('OTHER', 'Altro'),
    ]
    
    # Riferimento alla CER
    cer_configuration = models.ForeignKey(
        'core.CERConfiguration',
        on_delete=models.CASCADE,
        related_name='document_audits',
        verbose_name="Configurazione CER"
    )
    
    # Dettagli documento
    document_type = models.CharField(
        "Tipo Documento",
        max_length=20,
        choices=DOCUMENT_TYPES
    )
    document_name = models.CharField(
        "Nome Documento",
        max_length=255,
        help_text="Nome del file o identificativo del documento"
    )
    
    # Dettagli operazione
    operation_type = models.CharField(
        "Tipo Operazione",
        max_length=20,
        choices=OPERATION_TYPES
    )
    operation_timestamp = models.DateTimeField(
        "Timestamp Operazione",
        auto_now_add=True,
        db_index=True
    )
    
    # Utente che ha eseguito l'operazione
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Utente"
    )
    
    # Informazioni contestuali
    ip_address = models.GenericIPAddressField(
        "Indirizzo IP",
        null=True,
        blank=True
    )
    user_agent = models.TextField(
        "User Agent",
        blank=True
    )
    
    # Motivo dell'operazione
    reason = models.TextField(
        "Motivo",
        blank=True,
        help_text="Motivazione dell'operazione"
    )
    
    # Conformità normativa - ritenzione 3 anni per documenti
    retention_date = models.DateTimeField(
        "Data Scadenza",
        help_text="Data oltre la quale il record può essere eliminato (3 anni)"
    )
    
    class Meta:
        verbose_name = "Audit Documento CER"
        verbose_name_plural = "Audit Documenti CER"
        ordering = ['-operation_timestamp']
        indexes = [
            models.Index(fields=['cer_configuration', 'operation_timestamp']),
            models.Index(fields=['document_type', 'operation_timestamp']),
            models.Index(fields=['user', 'operation_timestamp']),
            models.Index(fields=['retention_date']),
        ]
    
    def __str__(self):
        return f"Audit {self.operation_type} - {self.document_name} - {self.operation_timestamp}"
    
    def save(self, *args, **kwargs):
        # Imposta data di scadenza a 3 anni dalla creazione
        if not self.retention_date:
            self.retention_date = timezone.now() + timezone.timedelta(days=1095)  # 3 anni
        super().save(*args, **kwargs)


class UserActionAudit(models.Model):
    """
    Audit trail per azioni utente - REQUISITO NORMATIVO
    Traccia tutte le azioni significative degli utenti
    """
    
    ACTION_TYPES = [
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('PASSWORD_CHANGE', 'Cambio Password'),
        ('PROFILE_UPDATE', 'Aggiornamento Profilo'),
        ('PERMISSION_GRANT', 'Concessione Permesso'),
        ('PERMISSION_REVOKE', 'Revoca Permesso'),
        ('DATA_EXPORT', 'Esportazione Dati'),
        ('ADMIN_ACTION', 'Azione Amministrativa'),
        ('API_ACCESS', 'Accesso API'),
        ('SUSPICIOUS_ACTIVITY', 'Attività Sospetta'),
    ]
    
    # Utente che ha eseguito l'azione
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Utente"
    )
    
    # Dettagli azione
    action_type = models.CharField(
        "Tipo Azione",
        max_length=20,
        choices=ACTION_TYPES
    )
    description = models.TextField(
        "Descrizione",
        help_text="Descrizione dettagliata dell'azione"
    )
    
    # Timestamp
    action_timestamp = models.DateTimeField(
        "Timestamp Azione",
        auto_now_add=True,
        db_index=True
    )
    
    # Informazioni contestuali
    ip_address = models.GenericIPAddressField(
        "Indirizzo IP",
        null=True,
        blank=True
    )
    user_agent = models.TextField(
        "User Agent",
        blank=True
    )
    session_id = models.CharField(
        "ID Sessione",
        max_length=40,
        blank=True
    )
    
    # Informazioni aggiuntive
    metadata = models.JSONField(
        "Metadati",
        default=dict,
        blank=True,
        help_text="Informazioni aggiuntive sull'azione"
    )
    
    # Conformità normativa - ritenzione 1 anno per azioni utente
    retention_date = models.DateTimeField(
        "Data Scadenza",
        help_text="Data oltre la quale il record può essere eliminato (1 anno)"
    )
    
    class Meta:
        verbose_name = "Audit Azione Utente"
        verbose_name_plural = "Audit Azioni Utente"
        ordering = ['-action_timestamp']
        indexes = [
            models.Index(fields=['user', 'action_timestamp']),
            models.Index(fields=['action_type', 'action_timestamp']),
            models.Index(fields=['ip_address', 'action_timestamp']),
            models.Index(fields=['retention_date']),
        ]
    
    def __str__(self):
        user_str = self.user.email if self.user else "Anonimo"
        return f"Audit {self.action_type} - {user_str} - {self.action_timestamp}"
    
    def save(self, *args, **kwargs):
        # Imposta data di scadenza a 1 anno dalla creazione
        if not self.retention_date:
            self.retention_date = timezone.now() + timezone.timedelta(days=365)  # 1 anno
        super().save(*args, **kwargs)
