# core/views/mixins/gdpr.py

from django.contrib import messages
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _


class GDPRConsentRequiredMixin:
    """
    Richiede che l'utente abbia fornito i consensi GDPR necessari
    """

    def dispatch(self, request, *args, **kwargs):
        if not self._check_gdpr_consent():
            messages.warning(
                request, _("È necessario fornire i consensi GDPR prima di procedere")
            )
            return redirect("core:gdpr_consent")
        return super().dispatch(request, *args, **kwargs)

    def _check_gdpr_consent(self):
        """Verifica i consensi GDPR dell'utente"""
        user = self.request.user
        return all(
            [user.privacy_policy, user.data_processing, user.energy_data_processing]
        )


class GDPRDataProtectionMixin:
    """
    Implementa protezioni per i dati personali come richiesto dal GDPR
    """

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Maschera/filtra dati sensibili nel contesto
        if "user_data" in context:
            context["user_data"] = self._mask_sensitive_data(context["user_data"])
        return context

    def _mask_sensitive_data(self, data):
        """Maschera i dati sensibili"""
        if isinstance(data, dict):
            masked = data.copy()
            sensitive_fields = ["fiscal_code", "phone", "email"]
            for field in sensitive_fields:
                if field in masked:
                    masked[field] = self._mask_value(masked[field])
            return masked
        return data

    def _mask_value(self, value):
        """Maschera un singolo valore"""
        if not value:
            return value
        str_value = str(value)
        if len(str_value) <= 4:
            return "*" * len(str_value)
        return f"{str_value[:2]}{'*' * (len(str_value)-4)}{str_value[-2:]}"
