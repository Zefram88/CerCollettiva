# Generated manually for cer app

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="MemberProfile",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "fiscal_code",
                    models.CharField(
                        blank=True,
                        help_text="Codice fiscale (16 caratteri per persone fisiche, 11 per aziende)",
                        max_length=16,
                        null=True,
                        verbose_name="Codice Fiscale",
                    ),
                ),
                (
                    "phone",
                    models.CharField(
                        blank=True,
                        help_text="Numero di telefono principale",
                        max_length=20,
                        null=True,
                        verbose_name="Telefono",
                    ),
                ),
                (
                    "address",
                    models.CharField(
                        blank=True,
                        help_text="Indirizzo completo di residenza/sede",
                        max_length=255,
                        null=True,
                        verbose_name="Indirizzo",
                    ),
                ),
                (
                    "city",
                    models.CharField(
                        blank=True, max_length=100, null=True, verbose_name="Città"
                    ),
                ),
                (
                    "zip_code",
                    models.CharField(
                        blank=True, max_length=10, null=True, verbose_name="CAP"
                    ),
                ),
                (
                    "province",
                    models.CharField(
                        blank=True,
                        help_text="Sigla provincia (es. MI, RM)",
                        max_length=2,
                        null=True,
                        verbose_name="Provincia",
                    ),
                ),
                (
                    "vat_number",
                    models.CharField(
                        blank=True,
                        help_text="11 caratteri numerici",
                        max_length=11,
                        null=True,
                        verbose_name="Partita IVA",
                    ),
                ),
                (
                    "legal_name",
                    models.CharField(
                        blank=True,
                        help_text="Nome completo dell'azienda/ente",
                        max_length=255,
                        null=True,
                        verbose_name="Denominazione Sociale",
                    ),
                ),
                (
                    "pec",
                    models.EmailField(
                        blank=True,
                        help_text="Indirizzo PEC aziendale",
                        null=True,
                        verbose_name="PEC",
                    ),
                ),
                (
                    "sdi_code",
                    models.CharField(
                        blank=True,
                        help_text="Codice destinatario fatturazione elettronica",
                        max_length=7,
                        null=True,
                        verbose_name="Codice SDI",
                    ),
                ),
                (
                    "registration_number",
                    models.CharField(
                        blank=True,
                        help_text="Numero di registrazione presso enti competenti",
                        max_length=50,
                        null=True,
                        verbose_name="Numero Registrazione",
                    ),
                ),
                (
                    "statute_date",
                    models.DateField(
                        blank=True,
                        help_text="Data di approvazione dello statuto",
                        null=True,
                        verbose_name="Data Statuto",
                    ),
                ),
                (
                    "religious_entity_code",
                    models.CharField(
                        blank=True,
                        help_text="Codice identificativo dell'ente religioso",
                        max_length=50,
                        null=True,
                        verbose_name="Codice Ente Religioso",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Data Creazione"
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True, verbose_name="Ultimo Aggiornamento"
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="member_profile",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Utente",
                    ),
                ),
            ],
            options={
                "verbose_name": "Profilo Membro CER",
                "verbose_name_plural": "Profili Membri CER",
                "ordering": ["user__last_name", "user__first_name"],
            },
        ),
        migrations.AddIndex(
            model_name="memberprofile",
            index=models.Index(
                fields=["fiscal_code"], name="cer_memberp_fiscal__index"
            ),
        ),
        migrations.AddIndex(
            model_name="memberprofile",
            index=models.Index(fields=["vat_number"], name="cer_memberp_vat_num_index"),
        ),
        migrations.AddIndex(
            model_name="memberprofile",
            index=models.Index(fields=["created_at"], name="cer_memberp_created_index"),
        ),
    ]
