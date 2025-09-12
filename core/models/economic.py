# core/models/economic.py
import uuid
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class EconomicTransaction(models.Model):
    """
    Modello per transazioni economiche CER - REQUISITO NORMATIVO
    Gestisce tutte le transazioni finanziarie del sistema CER
    """

    TRANSACTION_TYPES = [
        ("BENEFIT_DISTRIBUTION", "Distribuzione Benefici"),
        ("GSE_PAYMENT", "Pagamento GSE"),
        ("MANAGEMENT_FEE", "Quota Gestione"),
        ("TAX_PAYMENT", "Pagamento Imposte"),
        ("REFUND", "Rimborso"),
        ("ADJUSTMENT", "Rettifica"),
        ("PENALTY", "Penale"),
        ("BONUS", "Bonus"),
    ]

    STATUS_CHOICES = [
        ("PENDING", "In Attesa"),
        ("PROCESSING", "In Elaborazione"),
        ("PROCESSED", "Elaborata"),
        ("FAILED", "Fallita"),
        ("CANCELLED", "Annullata"),
        ("REVERSED", "Stornata"),
    ]

    PAYMENT_METHODS = [
        ("BANK_TRANSFER", "Bonifico Bancario"),
        ("GSE_CREDIT", "Credito GSE"),
        ("CASH", "Contanti"),
        ("CHECK", "Assegno"),
        ("OTHER", "Altro"),
    ]

    # Identificatori
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="ID Transazione",
    )
    transaction_number = models.CharField(
        "Numero Transazione",
        max_length=50,
        unique=True,
        help_text="Numero univoco della transazione",
    )

    # Riferimenti
    cer_configuration = models.ForeignKey(
        "core.CERConfiguration",
        on_delete=models.CASCADE,
        related_name="economic_transactions",
        verbose_name="Configurazione CER",
    )
    plant = models.ForeignKey(
        "core.Plant",
        on_delete=models.CASCADE,
        related_name="economic_transactions",
        null=True,
        blank=True,
        verbose_name="Impianto",
        help_text="Impianto di riferimento (se applicabile)",
    )

    # Dettagli transazione
    transaction_type = models.CharField(
        "Tipo Transazione", max_length=50, choices=TRANSACTION_TYPES
    )
    amount = models.DecimalField(
        "Importo",
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Importo in euro",
    )
    currency = models.CharField(
        "Valuta", max_length=3, default="EUR", help_text="Codice valuta ISO 4217"
    )

    # Status e metodi
    status = models.CharField(
        "Stato", max_length=20, choices=STATUS_CHOICES, default="PENDING"
    )
    payment_method = models.CharField(
        "Metodo Pagamento",
        max_length=20,
        choices=PAYMENT_METHODS,
        default="BANK_TRANSFER",
    )

    # Periodi di riferimento
    reference_period_start = models.DateField(
        "Inizio Periodo Riferimento",
        help_text="Data inizio del periodo energetico di riferimento",
    )
    reference_period_end = models.DateField(
        "Fine Periodo Riferimento",
        help_text="Data fine del periodo energetico di riferimento",
    )

    # Date operative
    created_at = models.DateTimeField("Creata il", auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField("Aggiornata il", auto_now=True)
    processed_at = models.DateTimeField(
        "Elaborata il",
        null=True,
        blank=True,
        help_text="Data e ora di elaborazione della transazione",
    )
    due_date = models.DateTimeField(
        "Scadenza", null=True, blank=True, help_text="Data di scadenza per il pagamento"
    )

    # Informazioni aggiuntive
    description = models.TextField(
        "Descrizione", blank=True, help_text="Descrizione dettagliata della transazione"
    )
    notes = models.TextField("Note", blank=True, help_text="Note interne")

    # Dati bancari
    bank_reference = models.CharField(
        "Riferimento Bancario",
        max_length=100,
        blank=True,
        help_text="Codice di riferimento bancario",
    )
    bank_account = models.CharField(
        "Conto Bancario",
        max_length=34,  # IBAN max length
        blank=True,
        help_text="IBAN del conto di destinazione",
    )

    # Conformità normativa
    fiscal_year = models.IntegerField(
        "Anno Fiscale", help_text="Anno fiscale di riferimento"
    )
    vat_amount = models.DecimalField(
        "Importo IVA",
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Importo IVA applicata",
    )
    tax_code = models.CharField(
        "Codice Fiscale",
        max_length=20,
        blank=True,
        help_text="Codice fiscale per adempimenti tributari",
    )

    class Meta:
        verbose_name = "Transazione Economica"
        verbose_name_plural = "Transazioni Economiche"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["cer_configuration", "created_at"]),
            models.Index(fields=["transaction_type", "status"]),
            models.Index(fields=["status", "due_date"]),
            models.Index(fields=["reference_period_start", "reference_period_end"]),
            models.Index(fields=["fiscal_year"]),
        ]

    def __str__(self):
        return f"{self.transaction_number} - {self.get_transaction_type_display()} - €{self.amount}"

    def save(self, *args, **kwargs):
        # Genera numero transazione se non presente
        if not self.transaction_number:
            self.transaction_number = self._generate_transaction_number()

        # Imposta anno fiscale se non presente
        if not self.fiscal_year:
            self.fiscal_year = (
                self.reference_period_start.year
                if self.reference_period_start
                else timezone.now().year
            )

        # Aggiorna processed_at quando status cambia a PROCESSED
        if self.status == "PROCESSED" and not self.processed_at:
            self.processed_at = timezone.now()

        super().save(*args, **kwargs)

    def _generate_transaction_number(self):
        """Genera un numero di transazione univoco"""
        year = timezone.now().year
        # Conta le transazioni dell'anno corrente per la CER
        count = (
            EconomicTransaction.objects.filter(
                cer_configuration=self.cer_configuration, created_at__year=year
            ).count()
            + 1
        )

        return f"TXN-{self.cer_configuration.code}-{year}-{count:06d}"

    @property
    def net_amount(self):
        """Importo netto (senza IVA)"""
        return self.amount - self.vat_amount

    @property
    def is_overdue(self):
        """Verifica se la transazione è in ritardo"""
        if self.due_date and self.status in ["PENDING", "PROCESSING"]:
            return timezone.now() > self.due_date
        return False

    def can_be_processed(self):
        """Verifica se la transazione può essere elaborata"""
        return self.status == "PENDING"

    def mark_as_processed(self, user=None):
        """Marca la transazione come elaborata"""
        if self.can_be_processed():
            self.status = "PROCESSED"
            self.processed_at = timezone.now()
            self.save()
            return True
        return False


class TransactionApproval(models.Model):
    """
    Sistema approvazioni per transazioni economiche - REQUISITO NORMATIVO
    Gestisce il workflow di approvazione delle transazioni
    """

    STATUS_CHOICES = [
        ("PENDING", "In Attesa"),
        ("APPROVED", "Approvata"),
        ("REJECTED", "Rifiutata"),
        ("EXPIRED", "Scaduta"),
    ]

    APPROVAL_LEVELS = [
        ("L1", "Livello 1 - Operativo"),
        ("L2", "Livello 2 - Supervisore"),
        ("L3", "Livello 3 - Dirigenziale"),
        ("L4", "Livello 4 - Amministratore"),
    ]

    # Transazione da approvare
    transaction = models.OneToOneField(
        EconomicTransaction,
        on_delete=models.CASCADE,
        related_name="approval",
        verbose_name="Transazione",
    )

    # Utenti coinvolti
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="requested_approvals",
        verbose_name="Richiesta da",
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="given_approvals",
        verbose_name="Approvata da",
    )

    # Status e livello
    status = models.CharField(
        "Stato", max_length=20, choices=STATUS_CHOICES, default="PENDING"
    )
    approval_level = models.CharField(
        "Livello Approvazione", max_length=2, choices=APPROVAL_LEVELS, default="L1"
    )

    # Date
    requested_at = models.DateTimeField(
        "Richiesta il", auto_now_add=True, db_index=True
    )
    approved_at = models.DateTimeField("Approvata il", null=True, blank=True)
    expires_at = models.DateTimeField(
        "Scade il", help_text="Data di scadenza della richiesta di approvazione"
    )

    # Motivazioni
    request_reason = models.TextField(
        "Motivo Richiesta", help_text="Motivazione della richiesta di approvazione"
    )
    approval_notes = models.TextField(
        "Note Approvazione", blank=True, help_text="Note dell'approvatore"
    )

    # Priorità
    priority = models.CharField(
        "Priorità",
        max_length=10,
        choices=[
            ("LOW", "Bassa"),
            ("NORMAL", "Normale"),
            ("HIGH", "Alta"),
            ("URGENT", "Urgente"),
        ],
        default="NORMAL",
    )

    # Metadati
    metadata = models.JSONField(
        "Metadati",
        default=dict,
        blank=True,
        help_text="Informazioni aggiuntive per l'approvazione",
    )

    class Meta:
        verbose_name = "Approvazione Transazione"
        verbose_name_plural = "Approvazioni Transazioni"
        ordering = ["-requested_at"]
        indexes = [
            models.Index(fields=["status", "requested_at"]),
            models.Index(fields=["requested_by", "status"]),
            models.Index(fields=["approved_by", "approved_at"]),
            models.Index(fields=["expires_at"]),
            models.Index(fields=["approval_level", "status"]),
        ]

    def __str__(self):
        return f"Approvazione {self.transaction.transaction_number} - {self.get_status_display()}"

    def save(self, *args, **kwargs):
        # Imposta data di scadenza se non presente (7 giorni)
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(days=7)

        # Aggiorna approved_at quando status cambia a APPROVED
        if self.status == "APPROVED" and not self.approved_at:
            self.approved_at = timezone.now()

        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        """Verifica se la richiesta è scaduta"""
        return timezone.now() > self.expires_at and self.status == "PENDING"

    @property
    def days_remaining(self):
        """Giorni rimanenti per l'approvazione"""
        if self.status != "PENDING":
            return 0
        delta = self.expires_at - timezone.now()
        return max(0, delta.days)

    def can_be_approved_by(self, user):
        """Verifica se l'utente può approvare questa transazione"""
        # Logica di autorizzazione basata sui ruoli e livelli
        # Da implementare in base alle regole di business
        if self.status != "PENDING":
            return False

        if self.is_expired:
            return False

        # Non può auto-approvarsi
        if user == self.requested_by:
            return False

        return True

    def approve(self, user, notes=""):
        """Approva la transazione"""
        if self.can_be_approved_by(user):
            self.status = "APPROVED"
            self.approved_by = user
            self.approved_at = timezone.now()
            self.approval_notes = notes
            self.save()

            # Marca la transazione come pronta per elaborazione
            if self.transaction.status == "PENDING":
                self.transaction.status = "PROCESSING"
                self.transaction.save()

            return True
        return False

    def reject(self, user, notes=""):
        """Rifiuta la transazione"""
        if self.can_be_approved_by(user):
            self.status = "REJECTED"
            self.approved_by = user
            self.approved_at = timezone.now()
            self.approval_notes = notes
            self.save()

            # Marca la transazione come fallita
            if self.transaction.status in ["PENDING", "PROCESSING"]:
                self.transaction.status = "FAILED"
                self.transaction.save()

            return True
        return False
