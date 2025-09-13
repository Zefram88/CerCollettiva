from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        # Se username non è specificato, usa email come username
        if "username" not in extra_fields:
            extra_fields["username"] = email
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    objects = CustomUserManager()

    # Configurazione per usare email come username
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    # Sovrascrivi il campo email per renderlo univoco
    email = models.EmailField(
        _("email address"),
        unique=True,
        help_text=_("Required. Enter a valid email address."),
    )

    # DEPRECATO: username mantenuto solo per compatibilità, sempre == email
    # Non modificare direttamente, viene impostato automaticamente

    LEGAL_TYPES = [
        ("PRIVATE", "Privato"),
        ("BUSINESS", "Azienda"),
        ("ASSOCIATION", "Associazione"),
        ("CHURCH", "Ente Religioso"),
        ("PUBLIC", "Ente Pubblico"),
    ]

    PROFIT_TYPES = [
        ("PROFIT", "Con scopo di lucro"),
        ("NON_PROFIT", "Senza scopo di lucro"),
    ]

    # Campi base
    legal_type = models.CharField(
        max_length=20,
        choices=LEGAL_TYPES,
        default="PRIVATE",
        verbose_name="Tipo Soggetto",
    )
    profit_type = models.CharField(
        max_length=20,
        choices=PROFIT_TYPES,
        default="NON_PROFIT",
        verbose_name="Finalità",
    )
    fiscal_code = models.CharField(
        max_length=16, blank=True, null=True, verbose_name="Codice Fiscale"
    )
    address = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="Indirizzo"
    )
    phone = models.CharField(
        max_length=20, blank=True, null=True, verbose_name="Telefono"
    )

    # Campi per aziende/enti
    vat_number = models.CharField(
        max_length=11,
        blank=True,
        null=True,
        verbose_name="Partita IVA",
        help_text="11 caratteri per la partita IVA",
    )

    legal_name = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="Denominazione"
    )
    pec = models.EmailField(blank=True, null=True, verbose_name="PEC")
    sdi_code = models.CharField(
        max_length=7, blank=True, null=True, verbose_name="Codice SDI"
    )

    # Campi per associazioni
    registration_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Numero Registrazione",
    )
    statute_date = models.DateField(
        blank=True, null=True, verbose_name="Data Statuto"
    )

    # Campi per enti religiosi
    religious_entity_code = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Codice Ente Religioso",
    )

    # Consensi GDPR
    privacy_accepted = models.BooleanField(
        "Privacy Accettata",
        default=False,
        help_text="Indica se l'utente ha accettato la privacy policy",
    )
    privacy_acceptance_date = models.DateTimeField(
        "Data Accettazione Privacy", null=True, blank=True
    )
    privacy_last_update = models.DateTimeField(
        "Ultimo Aggiornamento Privacy", null=True, blank=True
    )

    # Consensi GDPR estesi
    privacy_policy = models.BooleanField(
        "Privacy Policy",
        default=False,
        help_text="Consenso alla privacy policy",
    )
    data_processing = models.BooleanField(
        "Trattamento Dati",
        default=False,
        help_text="Consenso al trattamento dei dati personali",
    )
    privacy_policy_timestamp = models.DateTimeField(
        "Timestamp Privacy Policy",
        null=True,
        blank=True,
        help_text="Data e ora di lettura della privacy policy",
    )
    data_processing_timestamp = models.DateTimeField(
        "Timestamp Trattamento Dati",
        null=True,
        blank=True,
        help_text="Data e ora di lettura dell'accordo trattamento dati",
    )

    # Stato Onboarding CER
    class OnboardingStatus(models.TextChoices):
        REGISTRATO = "REGISTRATO", "Registrato"
        ANAGRAFICA_COMPLETA = "ANAGRAFICA_COMPLETA", "Anagrafica Completa"
        CER_COMPLETA = "CER_COMPLETA", "CER Completa"
        ONBOARDING_COMPLETATO = (
            "ONBOARDING_COMPLETATO",
            "Onboarding Completato",
        )

    onboarding_status = models.CharField(
        max_length=25,
        choices=OnboardingStatus.choices,
        default=OnboardingStatus.REGISTRATO,
        verbose_name="Stato Onboarding",
    )

    # Flag per sostenitori (non membri CER)
    is_supporter = models.BooleanField(
        default=False,
        verbose_name="Sostenitore",
        help_text="Indica se l'utente è un sostenitore (non membro CER)",
    )

    # Ruolo CER
    class CERRole(models.TextChoices):
        ISCRITTO = "ISCRITTO", "Iscritto"
        SOCIO_ORDINARIO = "SOCIO_ORDINARIO", "Socio Ordinario"
        SOCIO_SOSTENITORE = "SOCIO_SOSTENITORE", "Socio Sostenitore"

    cer_role = models.CharField(
        max_length=20,
        choices=CERRole.choices,
        default=CERRole.ISCRITTO,
        verbose_name="Ruolo CER",
    )

    # Property per verifica tipo utente
    @property
    def is_business(self):
        """Verifica se l'utente è un'azienda"""
        return self.legal_type == "BUSINESS"

    @property
    def is_private(self):
        """Verifica se l'utente è un privato"""
        return self.legal_type == "PRIVATE"

    @property
    def is_association(self):
        """Verifica se l'utente è un'associazione"""
        return self.legal_type == "ASSOCIATION"

    @property
    def is_church(self):
        """Verifica se l'utente è un ente religioso"""
        return self.legal_type == "CHURCH"

    @property
    def is_public(self):
        """Verifica se l'utente è un ente pubblico"""
        return self.legal_type == "PUBLIC"

    @property
    def is_onboarding_complete(self):
        """Verifica se l'onboarding è completato"""
        return (
            self.onboarding_status
            == self.OnboardingStatus.ONBOARDING_COMPLETATO
        )

    @property
    def needs_profile_completion(self):
        """Verifica se l'utente deve completare il profilo anagrafico"""
        return self.onboarding_status == self.OnboardingStatus.REGISTRATO

    @property
    def needs_cer_setup(self):
        """Verifica se l'utente deve configurare la partecipazione CER"""
        return (
            self.onboarding_status == self.OnboardingStatus.ANAGRAFICA_COMPLETA
        )

    @property
    def requires_vat(self):
        """Verifica se l'utente richiede partita IVA"""
        return self.legal_type in [
            "BUSINESS",
            "ASSOCIATION",
            "CHURCH",
            "PUBLIC",
        ]

    @property
    def requires_pec(self):
        """Verifica se l'utente richiede PEC"""
        return self.legal_type in ["BUSINESS", "ASSOCIATION", "PUBLIC"]

    def accept_privacy(self):
        """
        Registra l'accettazione della privacy da parte dell'utente
        """
        now = timezone.now()
        self.privacy_accepted = True
        self.privacy_acceptance_date = now
        self.privacy_last_update = now
        self.save()

    def update_privacy(self):
        """
        Registra un aggiornamento della privacy
        """
        self.last_privacy_update = timezone.now()
        self.save(update_fields=["last_privacy_update"])

    def clean(self):
        super().clean()
        # Imposta automaticamente NON_PROFIT per soggetti privati
        if self.legal_type == "PRIVATE":
            self.profit_type = "NON_PROFIT"

        # Validazioni specifiche per tipo
        if self.legal_type == "PRIVATE":
            if not all([self.first_name, self.last_name]):
                raise ValidationError(
                    "Nome e cognome sono obbligatori per gli utenti privati."
                )
        elif self.legal_type in [
            "BUSINESS",
            "ASSOCIATION",
            "CHURCH",
            "PUBLIC",
        ]:
            if not all([self.vat_number, self.legal_name, self.pec]):
                raise ValidationError(
                    "Partita IVA, denominazione e PEC sono obbligatori per "
                    "aziende, associazioni, enti religiosi e pubblici."
                )

    def save(self, *args, **kwargs):
        # DEPRECAZIONE: Assicura che username sia sempre == email
        if self.email:
            self.username = self.email

        # Non validare durante il login o aggiornamenti automatici
        skip_validation = kwargs.pop("skip_validation", False)
        if not skip_validation:
            # Controlla se è un aggiornamento di last_login
            if hasattr(self, "_state") and self._state.adding is False:
                # Se è un aggiornamento, controlla se solo last_login è cambiato
                if hasattr(self, "_last_login_only"):
                    skip_validation = True
            if not skip_validation:
                self.clean()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Utente"
        verbose_name_plural = "Utenti"
        ordering = ["username"]
        permissions = [
            ("can_view_all_users", "Può vedere tutti gli utenti"),
            ("can_manage_users", "Può gestire gli utenti"),
            ("can_approve_users", "Può approvare gli utenti"),
        ]
        indexes = [
            models.Index(fields=["legal_type"]),
            models.Index(fields=["fiscal_code"]),
            models.Index(fields=["vat_number"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(
                    legal_type__in=[
                        "PRIVATE",
                        "BUSINESS",
                        "ASSOCIATION",
                        "CHURCH",
                        "PUBLIC",
                    ]
                ),
                name="valid_legal_type",
            ),
            models.CheckConstraint(
                check=models.Q(profit_type__in=["PROFIT", "NON_PROFIT"]),
                name="valid_profit_type",
            ),
            models.CheckConstraint(
                check=models.Q(
                    onboarding_status__in=[
                        "REGISTRATO",
                        "ANAGRAFICA_COMPLETA",
                        "CER_COMPLETA",
                        "ONBOARDING_COMPLETATO",
                    ]
                ),
                name="valid_onboarding_status",
            ),
        ]

    def __str__(self):
        if self.legal_name:
            return f"{self.legal_name} ({self.get_legal_type_display()})"
        return f"{self.username} ({self.get_legal_type_display()})"
