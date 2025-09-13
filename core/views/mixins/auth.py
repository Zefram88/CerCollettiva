# core/views/mixins/auth.py

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _


class StaffRequiredMixin(UserPassesTestMixin):
    """Richiede che l'utente sia staff"""

    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
        messages.error(self.request, _("Accesso riservato allo staff"))
        return redirect("core:home")


class PlantOwnerRequiredMixin(UserPassesTestMixin):
    """Richiede che l'utente sia proprietario dell'impianto"""

    def test_func(self):
        if self.request.user.is_staff:
            return True

        plant = self.get_object()
        return plant.owner == self.request.user

    def handle_no_permission(self):
        messages.error(self.request, _("Non hai i permessi per questo impianto"))
        return redirect("core:plant_list")


class CERMemberRequiredMixin(UserPassesTestMixin):
    """Richiede che l'utente sia membro della CER"""

    def test_func(self):
        if self.request.user.is_staff:
            return True

        cer = self.get_object()
        return cer.memberships.filter(user=self.request.user, is_active=True).exists()

    def handle_no_permission(self):
        messages.error(self.request, _("Non sei membro di questa CER"))
        return redirect("core:cer_list")
