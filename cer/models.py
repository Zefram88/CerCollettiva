# cer/models.py
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _  # noqa: F401


class MemberProfile(models.Model):
    """
    Profilo membro CER - OneToOne con CustomUser
    Estende i dati base dell'utente con informazioni specifiche per l'adesione CER
    """

    # Relazione con CustomUser
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="member_profile",
        verbose_name="Utente",
    )

    # Dati anagrafici completi (per fase 2 onboarding)
    fiscal_code = models.CharField(
        max_length=16,
        blank=True,
        null=True,
        verbose_name="Codice Fiscale",
        help_text="Codice fiscale (16 caratteri per persone fisiche, 11 per aziende)",
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Telefono",
        help_text="Numero di telefono principale",
    )

    address = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Indirizzo",
        help_text="Indirizzo completo di residenza/sede",
    )

    city = models.CharField(max_length=100, blank=True, null=True, verbose_name="Città")

    zip_code = models.CharField(
        max_length=10, blank=True, null=True, verbose_name="CAP"
    )

    province = models.CharField(
        max_length=2,
        blank=True,
        null=True,
        verbose_name="Provincia",
        help_text="Sigla provincia (es. MI, RM)",
    )

    # Dati specifici per aziende/enti
    vat_number = models.CharField(
        max_length=11,
        blank=True,
        null=True,
        verbose_name="Partita IVA",
        help_text="11 caratteri numerici",
    )

    legal_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Denominazione Sociale",
        help_text="Nome completo dell'azienda/ente",
    )

    pec = models.EmailField(
        blank=True, null=True, verbose_name="PEC", help_text="Indirizzo PEC aziendale"
    )

    sdi_code = models.CharField(
        max_length=7,
        blank=True,
        null=True,
        verbose_name="Codice SDI",
        help_text="Codice destinatario fatturazione elettronica",
    )

    # Dati per associazioni
    registration_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Numero Registrazione",
        help_text="Numero di registrazione presso enti competenti",
    )

    statute_date = models.DateField(
        blank=True,
        null=True,
        verbose_name="Data Statuto",
        help_text="Data di approvazione dello statuto",
    )

    # Dati per enti religiosi
    religious_entity_code = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Codice Ente Religioso",
        help_text="Codice identificativo dell'ente religioso",
    )

    # Dati wizard onboarding (JSON)
    onboarding_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Dati Onboarding",
        help_text="Dati temporanei del wizard di onboarding",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data Creazione")
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name="Ultimo Aggiornamento"
    )

    class Meta:
        verbose_name = "Profilo Membro CER"
        verbose_name_plural = "Profili Membri CER"
        ordering = ["user__last_name", "user__first_name"]
        indexes = [
            models.Index(fields=["fiscal_code"]),
            models.Index(fields=["vat_number"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        if self.legal_name:
            return f"{self.legal_name} - {self.user.get_full_name()}"
        return f"{self.user.get_full_name()} - Profilo CER"

    def clean(self):
        """Validazioni specifiche per tipo di soggetto"""
        super().clean()

        # Validazioni per persone fisiche (solo se il profilo è già stato inizializzato)
        if self.user.legal_type == "PRIVATE" and self.pk:
            if not self.fiscal_code:
                raise ValidationError(
                    {
                        "fiscal_code": "Il codice fiscale è obbligatorio per le "
                        "persone fisiche."
                    }
                )
            if len(self.fiscal_code) != 16:
                raise ValidationError(
                    {
                        "fiscal_code": "Il codice fiscale per persone fisiche deve "
                        "essere di 16 caratteri."
                    }
                )

        # Validazioni per aziende/associazioni (solo se il profilo è già stato
        # inizializzato)
        elif self.user.legal_type in ["BUSINESS", "ASSOCIATION"] and self.pk:
            if not all([self.vat_number, self.legal_name, self.pec]):
                missing_fields = []
                if not self.vat_number:
                    missing_fields.append("Partita IVA")
                if not self.legal_name:
                    missing_fields.append("Denominazione")
                if not self.pec:
                    missing_fields.append("PEC")
                raise ValidationError(
                    {
                        "vat_number": f"Campi obbligatori mancanti: "
                        f'{", ".join(missing_fields)}'
                    }
                )

            if self.vat_number and len(self.vat_number) != 11:
                raise ValidationError(
                    {
                        "vat_number": "La Partita IVA deve essere di 11 caratteri "
                        "numerici."
                    }
                )

        # Validazioni per enti pubblici (solo se il profilo è già stato inizializzato)
        elif self.user.legal_type == "PUBLIC" and self.pk:
            if not self.legal_name:
                raise ValidationError(
                    {
                        "legal_name": "La denominazione è obbligatoria per gli "
                        "enti pubblici."
                    }
                )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    @property
    def is_complete(self):
        """Verifica se il profilo è completo per il tipo di soggetto"""
        if self.user.legal_type == "PRIVATE":
            return all(
                [
                    self.fiscal_code,
                    self.phone,
                    self.address,
                    self.city,
                    self.zip_code,
                    self.province,
                ]
            )
        elif self.user.legal_type in ["BUSINESS", "ASSOCIATION"]:
            return all(
                [
                    self.vat_number,
                    self.legal_name,
                    self.pec,
                    self.fiscal_code,
                    self.phone,
                    self.address,
                    self.city,
                    self.zip_code,
                    self.province,
                ]
            )
        elif self.user.legal_type in ["PUBLIC", "CHURCH"]:
            return all(
                [
                    self.legal_name,
                    self.fiscal_code,
                    self.phone,
                    self.address,
                    self.city,
                    self.zip_code,
                    self.province,
                ]
            )
        return False

    @property
    def missing_fields(self):
        """Restituisce i campi mancanti per completare il profilo"""
        missing = []

        if self.user.legal_type == "PRIVATE":
            required_fields = [
                ("fiscal_code", "Codice Fiscale"),
                ("phone", "Telefono"),
                ("address", "Indirizzo"),
                ("city", "Città"),
                ("zip_code", "CAP"),
                ("province", "Provincia"),
            ]
        elif self.user.legal_type in ["BUSINESS", "ASSOCIATION"]:
            required_fields = [
                ("vat_number", "Partita IVA"),
                ("legal_name", "Denominazione"),
                ("pec", "PEC"),
                ("fiscal_code", "Codice Fiscale"),
                ("phone", "Telefono"),
                ("address", "Indirizzo"),
                ("city", "Città"),
                ("zip_code", "CAP"),
                ("province", "Provincia"),
            ]
        elif self.user.legal_type in ["PUBLIC", "CHURCH"]:
            required_fields = [
                ("legal_name", "Denominazione"),
                ("fiscal_code", "Codice Fiscale"),
                ("phone", "Telefono"),
                ("address", "Indirizzo"),
                ("city", "Città"),
                ("zip_code", "CAP"),
                ("province", "Provincia"),
            ]
        else:
            return []

        for field_name, field_label in required_fields:
            if not getattr(self, field_name):
                missing.append(field_label)

        return missing
