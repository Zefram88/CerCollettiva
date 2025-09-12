# core/views/document.py

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DeleteView, ListView

from ..forms import PlantDocumentForm
from ..models import Plant, PlantDocument
from .base import BasePlantView
from .mixins.gdpr import GDPRDataProtectionMixin


class PlantDocumentListView(BasePlantView):
    """Lista documenti di un impianto"""

    template_name = "core/documents/list.html"
    context_object_name = "documents"

    def get_queryset(self):
        plant = self.get_plant_if_allowed(self.kwargs["pk"])
        return PlantDocument.objects.filter(plant=plant).order_by("-uploaded_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["plant"] = get_object_or_404(Plant, pk=self.kwargs["pk"])
        return context


class PlantDocumentUploadView(BasePlantView, GDPRDataProtectionMixin):
    """Upload documento per un impianto"""

    template_name = "core/documents/upload.html"
    form_class = PlantDocumentForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["plant"] = self.get_plant_if_allowed(self.kwargs["pk"])
        return context

    def form_valid(self, form):
        plant = self.get_plant_if_allowed(self.kwargs["pk"])
        document = form.save(commit=False)
        document.plant = plant

        try:
            # Validazione dimensione file
            if document.document.size > 10 * 1024 * 1024:  # 10MB
                messages.error(self.request, _("Il file non può superare i 10MB"))
                return self.form_invalid(form)

            document.save()
            messages.success(self.request, _("Documento caricato con successo"))
            return redirect("core:plant_documents", pk=plant.pk)

        except Exception as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)


class PlantDocumentDeleteView(BasePlantView, UserPassesTestMixin):
    """Eliminazione documento"""

    model = PlantDocument

    def test_func(self):
        document = self.get_object()
        return self.request.user.is_staff or document.plant.owner == self.request.user

    def get_object(self):
        return get_object_or_404(
            PlantDocument, id=self.kwargs["document_id"], plant__id=self.kwargs["pk"]
        )

    def post(self, request, *args, **kwargs):
        document = self.get_object()

        try:
            document_name = document.name
            document.delete()
            messages.success(
                request, _(f'Documento "{document_name}" eliminato con successo')
            )
        except Exception as e:
            messages.error(request, str(e))

        return redirect("core:plant_documents", pk=self.kwargs["pk"])

    def handle_no_permission(self):
        return HttpResponseForbidden(
            _("Non hai i permessi per eliminare questo documento")
        )
