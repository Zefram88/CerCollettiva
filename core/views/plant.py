# core/views/plant.py
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DetailView, UpdateView

from energy.models import DeviceConfiguration

from ..forms import PlantForm, PlantMQTTConfigForm
from ..models import CERConfiguration, Plant

from .base import BasePlantView

logger = logging.getLogger(__name__)


@login_required
def plant_delete(request, pk):
    plant = get_object_or_404(Plant, pk=pk, owner=request.user)

    if request.method == "GET":
        # Renderizza la pagina di conferma
        return render(request, "core/plant_delete_confirm.html", {"plant": plant})

    elif request.method == "POST":
        try:
            plant_name = plant.name
            plant.delete()

            # Se è una richiesta AJAX, restituisci JSON
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"success": True})

            # Altrimenti, redirect con messaggio
            messages.success(
                request, _(f'Impianto "{plant_name}" eliminato con successo')
            )
            return redirect("core:plant_list")

        except Exception as e:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"success": False, "error": str(e)}, status=500)
            messages.error(request, str(e))
            return render(request, "core/plant_delete_confirm.html", {"plant": plant})

    # Se non è né GET né POST
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse(
            {"success": False, "error": "Metodo non consentito"}, status=405
        )
    return redirect("core:plant_list")


class PlantListView(BasePlantView):
    template_name = "core/plant_list.html"
    context_object_name = "plants"
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        is_global_admin = user.is_staff or user.is_superuser

        # Base queryset
        if is_global_admin:
            queryset = (
                Plant.objects.all()
                .select_related("cer_configuration", "owner")
                .prefetch_related("devices")
            )
        else:
            queryset = (
                Plant.objects.filter(owner=user)
                .select_related("cer_configuration", "owner")
                .prefetch_related("devices")
            )

        # Applica i filtri
        q = self.request.GET.get("q")
        if q:
            queryset = queryset.filter(Q(name__icontains=q) | Q(pod_code__icontains=q))
            print(f"Filtered by search term '{q}': {queryset.count()} plants")

        plant_type = self.request.GET.get("type")
        if plant_type:
            queryset = queryset.filter(plant_type=plant_type)
            print(f"Filtered by plant type '{plant_type}': {queryset.count()} plants")

        cer = self.request.GET.get("cer")
        if cer:
            queryset = queryset.filter(cer_configuration_id=cer)
            print(f"Filtered by CER '{cer}': {queryset.count()} plants")

        status = self.request.GET.get("status")
        if status:
            is_active = status == "active"
            queryset = queryset.filter(is_active=is_active)
            print(f"Filtered by status '{status}': {queryset.count()} plants")

        return queryset.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()

        context.update(
            {
                "plants": queryset,
                "plant_types": Plant.PLANT_TYPES,
                "cer_list": CERConfiguration.objects.filter(is_active=True),
                "total_power": queryset.aggregate(Sum("nominal_power"))[
                    "nominal_power__sum"
                ]
                or 0,
                "total_count": queryset.count(),
                # Aggiungiamo i parametri di filtro attivi al contesto
                "active_filters": {
                    "search": self.request.GET.get("q", ""),
                    "type": self.request.GET.get("type", ""),
                    "cer": self.request.GET.get("cer", ""),
                    "status": self.request.GET.get("status", ""),
                },
            }
        )
        return context


class PlantDetailView(BasePlantView, DetailView):
    """Dettaglio di un impianto"""

    model = Plant
    template_name = "core/plant_detail.html"
    context_object_name = "plant"

    def get_queryset(self):
        # Modifichiamo questa parte per includere tutti gli impianti per gli admin
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return (
                Plant.objects.all()
                .select_related("cer_configuration", "owner")
                .prefetch_related("devices__measurements", "documents")
            )
        return (
            Plant.objects.filter(owner=self.request.user)
            .select_related("cer_configuration", "owner")
            .prefetch_related("devices__measurements", "documents")
        )

    def get_context_data(self, **kwargs):
        # Assicuriamoci che l'oggetto sia disponibile
        self.object = self.get_object()
        context = super().get_context_data(**kwargs)

        # Recupera il dispositivo associato
        device = DeviceConfiguration.objects.filter(plant=self.object).first()

        # Recupera le ultime misurazioni
        time_threshold = self.get_time_threshold()
        measurements = self.get_plant_measurements(self.object, time_threshold)

        # Calcola statistiche energetiche
        power_data = self.calculate_power_data(measurements)

        # Prepara i dati Gaudì se l'impianto è verificato
        if self.object.gaudi_verified:
            gaudi_data = {
                "address": self.object.address,
                "plant_name": self.object.name,
                "pod_code": self.object.pod_code,
                "nominal_power": self.object.nominal_power,
                "connection_voltage": self.object.connection_voltage,
                "expected_yearly_production": self.object.expected_yearly_production,
                "validation_date": self.object.validation_date,
                "gaudi_request_code": self.object.gaudi_request_code,
                "censimp_code": self.object.censimp_code,
            }
        else:
            gaudi_data = None

        context.update(
            {
                "device": device,
                "device_status": self.get_devices_status(self.object),
                "power_data": power_data,
                "measurements": measurements[:100] if measurements else [],
                "documents": self.object.documents.all().order_by("-uploaded_at"),
                "mqtt_connected": bool(
                    device
                    and device.last_seen
                    and (timezone.now() - device.last_seen).total_seconds() < 300
                ),
                "gaudi_data": gaudi_data,  # Aggiungiamo i dati Gaudì al contesto
            }
        )
        return context


class PlantCreateView(CreateView, BasePlantView):
    """Creazione di un nuovo impianto"""

    model = Plant
    template_name = "core/plant_form.html"
    form_class = PlantForm
    success_url = reverse_lazy("core:plant_list")
    object = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": _("Nuovo Impianto"),
                "submit_label": _("Crea Impianto"),
                "object": None,
            }
        )
        return context

    def form_valid(self, form):
        form.instance.owner = self.request.user
        try:
            response = super().form_valid(form)
            messages.success(self.request, _("Impianto creato con successo"))
            return response
        except Exception as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)


class PlantUpdateView(UpdateView, BasePlantView):
    """Aggiornamento di un impianto esistente"""

    model = Plant
    template_name = "core/plant_form.html"
    form_class = PlantForm

    def setup(self, request, *args, **kwargs):
        """Inizializza l'oggetto all'avvio della vista"""
        super().setup(request, *args, **kwargs)
        self.object = self.get_object()

    def get_queryset(self):
        """Definisce il queryset base per il recupero dell'oggetto"""
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Plant.objects.all().select_related("cer_configuration", "owner")
        return Plant.objects.filter(owner=user).select_related(
            "cer_configuration", "owner"
        )

    def get_context_data(self, **kwargs):
        """Aggiunge dati al contesto"""
        context = super().get_context_data(**kwargs)
        context.update({"title": _("Modifica Impianto"), "submit_label": _("Aggiorna")})
        return context

    def form_valid(self, form):
        try:
            # Log per GDPR se admin modifica impianto altrui
            if (
                self.request.user.is_staff or self.request.user.is_superuser
            ) and self.object.owner != self.request.user:
                logger.info(
                    f"Admin {self.request.user.username} ha modificato "
                    f"l'impianto {self.object.id} di {self.object.owner.username}"
                )

            response = super().form_valid(form)
            messages.success(self.request, _("Impianto aggiornato con successo"))
            return response
        except Exception as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)

    def get_success_url(self):
        """URL di redirect dopo il salvataggio"""
        return reverse_lazy("core:plant_detail", kwargs={"pk": self.object.pk})


class PlantMQTTConfigView(BasePlantView):
    """Configurazione MQTT di un impianto"""

    template_name = "core/mqtt_config.html"
    form_class = PlantMQTTConfigForm

    def get_object(self):
        return get_object_or_404(Plant, pk=self.kwargs["pk"], owner=self.request.user)

    def form_valid(self, form):
        try:
            plant = form.save(commit=False)

            # Test connessione MQTT
            if plant.test_mqtt_connection():
                plant.save()
                messages.success(
                    self.request, _("Configurazione MQTT aggiornata con successo")
                )
                return redirect("core:plant_detail", pk=plant.pk)
            else:
                messages.error(self.request, _("Test connessione MQTT fallito"))
                return self.form_invalid(form)

        except Exception as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)
