# documents/models.py
import logging

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils import timezone

logger = logging.getLogger(__name__)


class Document(models.Model):
    DOCUMENT_TYPES = [
        ("BILL", "Bolletta Energia"),
        ("SYSTEM_CERT", "Certificato Conformità Impianto"),
        ("GSE_DOC", "Documentazione GSE"),
        ("PANELS_PHOTO", "Foto Pannelli"),
        ("INVERTER_PHOTO", "Foto Inverter"),
        ("PANELS_LIST", "Elenco Seriali Pannelli"),
        ("ID_DOC", "Documento Identità"),
        ("GAUDI", "Attestazione Gaudì"),
        ("OTHER", "Altro"),
    ]

    DOCUMENT_SOURCES = [
        ("USER", "Caricato da Utente"),
        ("SYSTEM", "Generato dal Sistema"),
    ]

    DATA_CLASSIFICATIONS = [
        ("PUBLIC", "Pubblico"),
        ("INTERNAL", "Interno"),
        ("CONFIDENTIAL", "Confidenziale"),
        ("PERSONAL", "Dati Personali"),
    ]

    PROCESSING_STATUS = [
        ("PENDING", "In attesa"),
        ("PROCESSING", "In elaborazione"),
        ("COMPLETED", "Completato"),
        ("FAILED", "Fallito"),
    ]
    # Campi esistenti
    type = models.CharField(
        max_length=20, choices=DOCUMENT_TYPES, verbose_name="Tipo Documento"
    )
    source = models.CharField(
        max_length=10,
        choices=DOCUMENT_SOURCES,
        default="USER",
        verbose_name="Origine Documento",
    )
    file = models.FileField(
        upload_to="documents/%Y/%m/%d/",
        validators=[FileExtensionValidator(["pdf", "jpg", "jpeg", "png"])],
        verbose_name="File",
        help_text="Formati supportati: PDF, JPG, PNG. Dimensione massima: 10MB",
    )
    notes = models.TextField(
        blank=True, verbose_name="Note", help_text="Note opzionali sul documento"
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Data Caricamento"
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="uploaded_documents",
        verbose_name="Caricato da",
    )
    plant = models.ForeignKey(
        "core.Plant",
        on_delete=models.CASCADE,
        related_name="user_documents",
        null=True,
        blank=True,
        verbose_name="Impianto",
        help_text="Impianto associato al documento (opzionale)",
    )

    # Campi specifici per attestato Gaudì
    processing_status = models.CharField(
        max_length=20,
        choices=PROCESSING_STATUS,
        default="PENDING",
        null=True,  # Aggiungiamo questo temporaneamente
        blank=True,  # E questo
        verbose_name="Stato Elaborazione",
        help_text="Stato dell'elaborazione del documento",
    )
    processing_errors = models.TextField(
        blank=True,
        null=True,  # Aggiungiamo questo temporaneamente
        verbose_name="Errori Elaborazione",
        help_text="Eventuali errori durante l'elaborazione del documento",
    )
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Data Elaborazione",
        help_text="Data e ora dell'elaborazione del documento",
    )

    # Nuovi campi GDPR e sicurezza
    gdpr_consent = models.BooleanField(
        default=False,
        verbose_name="Consenso GDPR",
        help_text="L'utente ha acconsentito al trattamento dei dati contenuti "
        "nel documento",
    )
    retention_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data di Conservazione",
        help_text="Data fino alla quale il documento deve essere conservato",
    )
    data_classification = models.CharField(
        max_length=20,
        choices=DATA_CLASSIFICATIONS,
        default="INTERNAL",
        verbose_name="Classificazione Dati",
        help_text="Livello di riservatezza del documento",
    )
    checksum = models.CharField(
        max_length=64,
        blank=True,
        help_text="SHA-256 checksum del file per verifica integrità",
    )
    encryption_status = models.BooleanField(
        default=False,
        verbose_name="Stato Crittografia",
        help_text="Indica se il documento è stato crittografato",
    )
    last_accessed = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Ultimo Accesso",
        help_text="Data e ora dell'ultimo accesso al documento",
    )

    class Meta:
        ordering = ["-uploaded_at"]
        verbose_name = "Documento"
        verbose_name_plural = "Documenti"
        permissions = [
            ("view_confidential", "Può visualizzare documenti confidenziali"),
            ("view_personal_data", "Può visualizzare dati personali"),
            ("extend_retention", "Può estendere il periodo di conservazione"),
        ]

    def __str__(self):
        source_text = "Sistema" if self.source == "SYSTEM" else "Utente"
        return (
            f"{self.get_type_display()} ({source_text}) - "
            f"{self.uploaded_at.strftime('%d/%m/%Y')}"
        )

    def save(self, *args, **kwargs):
        # Genera il checksum se è un nuovo file
        if not self.pk or "file" in kwargs:
            self.generate_checksum()

        # Se è un attestato Gaudì, imposta classificazione e processing status iniziale
        if self.type == "GAUDI":
            self.data_classification = "CONFIDENTIAL"
            if not self.pk:  # Solo per nuovi documenti
                self.processing_status = "PENDING"

        # Imposta periodo di retention se non specificato
        if not self.retention_date:
            self.set_retention_period()

        # Verifica necessità di consenso GDPR
        if self.contains_personal_data and not self.gdpr_consent:
            raise ValidationError(
                "Il consenso GDPR è obbligatorio per questo tipo di documento"
            )

        super().save(*args, **kwargs)

        # Se è un nuovo attestato Gaudì in stato PENDING, avvia l'elaborazione
        if self.type == "GAUDI" and self.processing_status == "PENDING":
            self.process_gaudi_attestation()

    @property
    def is_system_generated(self):
        return self.source == "SYSTEM"

    @property
    def is_expired(self):
        """Verifica se il documento ha superato la data di retention"""
        if self.retention_date:
            return self.retention_date < timezone.now().date()
        return False

    @property
    def contains_personal_data(self):
        """Verifica se il documento contiene dati personali"""
        return self.type in ["ID_DOC", "BILL"] or self.data_classification == "PERSONAL"

    def generate_checksum(self):
        """Genera SHA-256 checksum del file"""
        import hashlib

        if self.file:
            sha256 = hashlib.sha256()
            for chunk in self.file.chunks():
                sha256.update(chunk)
            self.checksum = sha256.hexdigest()

    def set_retention_period(self):
        """Imposta il periodo di retention basato sul tipo di documento"""
        retention_periods = {
            "ID_DOC": 365 * 2,  # 2 anni
            "BILL": 365 * 10,  # 10 anni
            "GSE_DOC": 365 * 10,  # 10 anni
            "SYSTEM_CERT": 365 * 10,
            "PANELS_PHOTO": 365 * 5,
            "INVERTER_PHOTO": 365 * 5,
            "PANELS_LIST": 365 * 10,
            "GAUDI": 365 * 10,
            "OTHER": 365 * 2,
        }
        days = retention_periods.get(self.type, 365 * 2)
        self.retention_date = timezone.now().date() + timezone.timedelta(days=days)

    def record_access(self, user):
        """Registra l'accesso al documento"""
        self.last_accessed = timezone.now()
        self.save(update_fields=["last_accessed"])

        # Qui potresti anche voler loggare l'accesso in una tabella separata
        DocumentAccess.objects.create(
            document=self, accessed_by=user, access_timestamp=self.last_accessed
        )

    def process_gaudi_attestation(self):
        """
        Elabora un attestato Gaudì e aggiorna i dati dell'impianto
        """
        if self.type != "GAUDI":
            return False

        if not self.plant:
            self.processing_status = "FAILED"
            self.processing_errors = "Nessun impianto associato al documento"
            self.save()
            return False

        try:
            self.processing_status = "PROCESSING"
            self.save()

            from documents.processors.gaudi import GaudiProcessor

            processor = GaudiProcessor(self)

            # Wrap the processing in a try-except block specifically for encoding issues
            try:
                result = processor.process()
            except UnicodeDecodeError as ude:
                # Log the specific encoding error
                logger.error(f"Encoding error processing file: {str(ude)}")
                self.processing_status = "FAILED"
                self.processing_errors = (
                    "Errore di codifica nel file. Il file potrebbe "
                    "contenere caratteri speciali non supportati."
                )
                self.save()
                return False

            if result:
                self.processing_status = "COMPLETED"
                self.processed_at = timezone.now()
            else:
                self.processing_status = "FAILED"
                self.processing_errors = "Elaborazione fallita"

        except Exception as e:
            logger.error(
                f"Errore nell'elaborazione dell'attestato Gaudì: {str(e)}",
                exc_info=True,
            )
            self.processing_status = "FAILED"
            self.processing_errors = str(e)

        self.save()
        return self.processing_status == "COMPLETED"


class DocumentAccess(models.Model):
    """Modello per tracciare gli accessi ai documenti"""

    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    accessed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    access_timestamp = models.DateTimeField(auto_now_add=True)
    access_ip = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        verbose_name = "Accesso Documento"
        verbose_name_plural = "Accessi Documenti"
        ordering = ["-access_timestamp"]
