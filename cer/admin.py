# cer/admin.py
from django.contrib import admin
from django.utils.html import format_html

from .models import MemberProfile


@admin.register(MemberProfile)
class MemberProfileAdmin(admin.ModelAdmin):
    """Admin per MemberProfile"""

    list_display = [
        "user_full_name",
        "user_email",
        "legal_type",
        "is_complete_display",
        "created_at",
    ]
    list_filter = ["user__legal_type", "created_at", "updated_at"]
    search_fields = [
        "user__first_name",
        "user__last_name",
        "user__email",
        "fiscal_code",
        "vat_number",
        "legal_name",
    ]
    readonly_fields = ["created_at", "updated_at", "is_complete_display"]

    fieldsets = (
        ("Informazioni Utente", {"fields": ("user", "created_at", "updated_at")}),
        (
            "Dati Anagrafici",
            {
                "fields": (
                    "fiscal_code",
                    "phone",
                    "address",
                    "city",
                    "zip_code",
                    "province",
                )
            },
        ),
        (
            "Dati Aziendali",
            {
                "fields": ("legal_name", "vat_number", "pec", "sdi_code"),
                "classes": ("collapse",),
            },
        ),
        (
            "Dati Associazione",
            {
                "fields": ("registration_number", "statute_date"),
                "classes": ("collapse",),
            },
        ),
        (
            "Dati Ente Religioso",
            {"fields": ("religious_entity_code",), "classes": ("collapse",)},
        ),
        (
            "Stato Profilo",
            {"fields": ("is_complete_display",), "classes": ("collapse",)},
        ),
    )

    def user_full_name(self, obj):
        """Nome completo dell'utente"""
        return obj.user.get_full_name()

    user_full_name.short_description = "Nome Completo"
    user_full_name.admin_order_field = "user__last_name"

    def user_email(self, obj):
        """Email dell'utente"""
        return obj.user.email

    user_email.short_description = "Email"
    user_email.admin_order_field = "user__email"

    def legal_type(self, obj):
        """Tipo legale dell'utente"""
        return obj.user.get_legal_type_display()

    legal_type.short_description = "Tipo Soggetto"
    legal_type.admin_order_field = "user__legal_type"

    def is_complete_display(self, obj):
        """Indicatore visivo se il profilo è completo"""
        if obj.is_complete:
            return format_html('<span style="color: green;">✓ Completo</span>')
        else:
            missing = ", ".join(obj.missing_fields)
            return format_html(
                '<span style="color: red;">✗ Incompleto</span><br>'
                "<small>Mancanti: {}</small>",
                missing,
            )

    is_complete_display.short_description = "Stato Profilo"

    def get_queryset(self, request):
        """Ottimizza le query"""
        return super().get_queryset(request).select_related("user")
