# energy/views/device_views.py
import json
import logging
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from core.main_models import Plant

from ..devices.registry import DeviceRegistry
from ..models import DeviceConfiguration, DeviceMeasurement
from ..mqtt.client import get_mqtt_client

logger = logging.getLogger(__name__)


class DeviceListView(LoginRequiredMixin, ListView):
    model = DeviceConfiguration
    template_name = "energy/devices/list.html"
    context_object_name = "devices"

    def post(self, request, *args, **kwargs):
        try:
            plant = get_object_or_404(Plant, id=request.POST.get("plant_id"))

            # Verifica che l'utente sia proprietario dell'impianto
            if plant.owner != request.user:
                messages.error(request, "Non hai i permessi per questo impianto")
                return redirect("energy:devices")

            device = DeviceConfiguration.objects.create(
                device_type=request.POST.get("deviceType"),
                device_id=request.POST.get("deviceId"),
                mqtt_topic_template=request.POST.get("mqttTopic"),
                plant=plant,
            )
            messages.success(request, "Dispositivo creato con successo")
            return redirect("energy:device-detail", pk=device.pk)
        except Exception as e:
            messages.error(request, f"Errore nella creazione del dispositivo: {str(e)}")
            return redirect("energy:devices")

    def get_queryset(self):
        # Get devices for current user with plant data
        queryset = DeviceConfiguration.objects.filter(
            plant__owner=self.request.user
        ).select_related("plant")

        # Optimize: Get all latest measurements in one query using subquery
        time_threshold = timezone.now() - timedelta(minutes=5)

        # First, get device IDs to avoid QuerySet evaluation in filter
        device_ids = list(queryset.values_list("id", flat=True))

        if device_ids:
            # Use subquery to get latest measurement per device efficiently
            from django.db.models import OuterRef, Subquery

            latest_measurements_subquery = DeviceMeasurement.objects.filter(
                device_id=OuterRef("id"), timestamp__gte=time_threshold
            ).order_by("-timestamp")

            # Annotate queryset with latest measurement data
            queryset = queryset.annotate(
                latest_measurement_power=Subquery(
                    latest_measurements_subquery.values("power")[:1]
                ),
                latest_measurement_timestamp=Subquery(
                    latest_measurements_subquery.values("timestamp")[:1]
                ),
            )

            # Add computed fields for template access
            for device in queryset:
                device._is_online = bool(device.latest_measurement_timestamp)
                device._current_power = device.latest_measurement_power or 0
                device._last_seen = device.latest_measurement_timestamp
        else:
            # No devices, set default values
            for device in queryset:
                device._is_online = False
                device._current_power = 0
                device._last_seen = None

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["plants"] = Plant.objects.filter(owner=self.request.user)
        return context


class DeviceCreateView(LoginRequiredMixin, CreateView):
    model = DeviceConfiguration
    template_name = "energy/devices/create.html"
    fields = [
        "device_id",
        "vendor",
        "model",
        "mqtt_topic_template",
        "plant",
        "is_active",
    ]
    success_url = reverse_lazy("energy:devices")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        # Filtra gli impianti in base al ruolo dell'utente
        if self.request.user.is_staff:
            # Gli amministratori possono vedere tutti gli impianti esistenti nel sistema
            form.fields["plant"].queryset = (
                Plant.objects.all()
                .select_related("owner")
                .order_by("owner__username", "name")
            )
            # Aggiungi il nome del proprietario al display dell'impianto
            form.fields["plant"].label_from_instance = (
                lambda obj: f"{obj.name} (Proprietario: {obj.owner.username})"
            )
        else:
            # Gli utenti normali vedono solo i propri impianti
            form.fields["plant"].queryset = Plant.objects.filter(
                owner=self.request.user
            )

        # Genera un nuovo Device ID
        last_device = DeviceConfiguration.objects.order_by("-device_id").first()
        try:
            last_id = int(last_device.device_id) if last_device else 0
            new_id = last_id + 1
        except (ValueError, AttributeError):
            new_id = 1

        while DeviceConfiguration.objects.filter(device_id=str(new_id)).exists():
            new_id += 1

        # Imposta il nuovo ID come valore iniziale
        form.fields["device_id"].initial = str(new_id)
        form.fields["device_id"].widget.attrs["readonly"] = True

        # Ottieni i vendor supportati dal registry
        supported_vendors = DeviceRegistry.get_supported_vendors()
        vendor_choices = [("", "Seleziona vendor...")] + [
            (v, v) for v in supported_vendors
        ]

        # Definisci le scelte per vendor e model
        form.fields["vendor"].choices = vendor_choices
        form.fields["model"].widget.attrs.update({"class": "form-select"})
        form.fields["vendor"].widget.attrs.update({"class": "form-select"})

        # Personalizza gli altri campi
        form.fields["mqtt_topic_template"].required = False
        form.fields["is_active"].initial = True

        return form

    def dispatch(self, request, *args, **kwargs):
        try:
            if request.user.is_staff:
                # Per gli amministratori, verifica se esistono impianti nel sistema
                if not Plant.objects.exists():
                    messages.warning(request, "Non ci sono impianti nel sistema")
                    return redirect("energy:plants")
            else:
                # Per gli utenti normali, verifica solo i propri impianti
                if not Plant.objects.filter(owner=request.user).exists():
                    messages.warning(request, "Devi prima creare un impianto")
                    return redirect("energy:plants")
            return super().dispatch(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Errore nel dispatch della view: {str(e)}")
            messages.error(request, "Si è verificato un errore")
            return redirect("energy:devices")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Ottieni i vendor e modelli supportati dal registry
        supported_vendors = DeviceRegistry.get_supported_vendors()
        supported_models = {
            vendor: [(m, m) for m in DeviceRegistry.get_supported_models(vendor)]
            for vendor in supported_vendors
        }

        context.update(
            {
                "supported_vendors": [(v, v) for v in supported_vendors],
                "supported_models": supported_models,
                "supported_models_json": json.dumps(supported_models),
            }
        )

        # Aggiungi la lista degli impianti al contesto in base al ruolo
        if self.request.user.is_staff:
            context["plants"] = Plant.objects.all().select_related("owner")
        else:
            context["plants"] = Plant.objects.filter(owner=self.request.user)

        return context

    def form_valid(self, form):
        try:
            logger.info("Tentativo di salvataggio form dispositivo")
            logger.debug(f"Form data: {form.cleaned_data}")

            # Ottieni l'impianto selezionato
            plant = form.cleaned_data["plant"]

            # Assegna i valori dal form
            form.instance.vendor = form.cleaned_data["vendor"].upper()
            form.instance.model = form.cleaned_data["model"].upper()

            # Determina il device_type dal vendor e model usando il registry
            device = DeviceRegistry.get_device_by_vendor_model(
                form.instance.vendor, form.instance.model
            )

            if not device:
                raise ValueError(
                    f"Combinazione vendor/model non valida: "
                    f"{form.instance.vendor}/{form.instance.model}"
                )

            form.instance.device_type = device.get_device_type()

            # Genera il topic MQTT se non specificato
            if not form.cleaned_data.get("mqtt_topic_template"):
                mqtt_topic = (
                    f"{form.instance.vendor}/{plant.pod_code}/"
                    f"{form.instance.device_id}/status"
                )
                form.instance.mqtt_topic_template = mqtt_topic
                logger.info(f"Generato MQTT topic: {mqtt_topic}")

            response = super().form_valid(form)

            logger.info(f"Dispositivo creato con successo. ID: {self.object.id}")
            messages.success(self.request, "Dispositivo creato con successo")
            return response

        except Exception as e:
            logger.error(f"Errore durante il salvataggio del dispositivo: {str(e)}")
            messages.error(
                self.request, f"Errore nella creazione del dispositivo: {str(e)}"
            )
            return self.form_invalid(form)


class DeviceDetailView(LoginRequiredMixin, UpdateView):
    model = DeviceConfiguration
    template_name = "energy/devices/detail.html"
    context_object_name = "device"
    fields = [
        "device_id",
        "device_type",
        "mqtt_topic_template",
        "vendor",
        "model",
        "is_active",
    ]

    def get(self, request, *args, **kwargs):
        # Verifica se è una richiesta AJAX
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            device = self.get_object()
            now = timezone.now()
            time_threshold = now - timedelta(minutes=5)

            # Ottieni l'ultima misurazione
            latest_measurement = (
                DeviceMeasurement.objects.filter(
                    device=device, timestamp__gte=time_threshold
                )
                .order_by("-timestamp")
                .first()
            )

            # Prepara i dati per la risposta JSON
            data = {
                "current_power": (
                    round(latest_measurement.power / 1000.0, 2)
                    if latest_measurement
                    else 0
                ),
                "current_voltage": (
                    round(latest_measurement.voltage, 1) if latest_measurement else 0
                ),
                "current_current": (
                    round(latest_measurement.current, 1) if latest_measurement else 0
                ),
                "apparent_power": (
                    round(getattr(latest_measurement, "apparent_power", 0) / 1000.0, 2)
                    if latest_measurement
                    else 0
                ),
                "reactive_power": (
                    round(getattr(latest_measurement, "reactive_power", 0) / 1000.0, 2)
                    if latest_measurement
                    else 0
                ),
                "is_online": bool(latest_measurement),
                "last_seen": (
                    latest_measurement.timestamp.isoformat()
                    if latest_measurement
                    else None
                ),
            }

            return JsonResponse(data)

        # Se non è una richiesta AJAX, procedi normalmente
        return super().get(request, *args, **kwargs)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Se stiamo aggiornando solo il topic
        if self.request.GET.get("update_topic"):
            # Mostra solo il campo mqtt_topic_template
            for field in list(form.fields.keys()):
                if field != "mqtt_topic_template":
                    form.fields.pop(field)
        return form

    def get_queryset(self):
        # SICURO: Verifica ownership implementata
        return DeviceConfiguration.objects.filter(
            plant__owner=self.request.user
        ).select_related("plant")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        device = self.get_object()
        now = timezone.now()
        time_threshold = now - timedelta(minutes=5)

        # Flag per identificare se siamo in modalità aggiornamento topic
        context["is_topic_update"] = bool(self.request.GET.get("update_topic"))

        # Aggiungi i vendor e modelli supportati
        context["supported_vendors"] = [
            ("VePro", "VePro"),
            ("Shelly", "Shelly"),
        ]

        context["supported_models"] = {
            "VePro": [("Contatore_Generale", "Contatore Generale")],
            "Shelly": [
                ("Pro_3EM", "Pro 3EM"),
                ("Pro_EM", "Pro EM"),
                ("EM", "EM"),
                ("3EM", "3EM"),
            ],
        }

        # Ottieni l'ultima misurazione con una query efficiente
        latest_measurement = (
            DeviceMeasurement.objects.filter(
                device=device, timestamp__gte=time_threshold
            )
            .select_related("device")
            .prefetch_related("phase_details")
            .order_by("-timestamp")
            .first()
        )

        if latest_measurement:
            context.update(
                {
                    "current_power": round(
                        latest_measurement.power / 1000.0, 2
                    ),  # Converti in kW
                    "current_voltage": round(latest_measurement.voltage, 1),
                    "current_current": round(latest_measurement.current, 1),
                    "phase_details": latest_measurement.phase_details.all(),
                    "apparent_power": round(
                        getattr(latest_measurement, "apparent_power", 0) / 1000.0, 2
                    ),  # kVA
                    "reactive_power": round(
                        getattr(latest_measurement, "reactive_power", 0) / 1000.0, 2
                    ),  # kVAR
                    "is_online": True,
                    "last_seen": latest_measurement.timestamp,
                }
            )
        else:
            context.update(
                {
                    "current_power": 0,
                    "current_voltage": 0,
                    "current_current": 0,
                    "phase_details": [],
                    "apparent_power": 0,
                    "reactive_power": 0,
                    "is_online": False,
                    "last_seen": device.last_seen,
                }
            )

        # Aggiungi informazioni di stato del dispositivo
        context["device_status"] = {
            "is_active": device.is_active,
            "is_connected": context["is_online"],
            "last_update": context["last_seen"],
        }

        return context

    def form_valid(self, form):
        try:
            self.object = form.save()
            messages.success(self.request, "Dispositivo aggiornato con successo")
            return super().form_valid(form)
        except Exception as e:
            messages.error(
                self.request, f"Errore nell'aggiornamento del dispositivo: {str(e)}"
            )
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse_lazy("energy:device-detail", kwargs={"pk": self.object.pk})


class MeasurementListView(LoginRequiredMixin, ListView):
    template_name = "energy/measurements/list.html"
    context_object_name = "measurements"
    paginate_by = 50

    def get_queryset(self):
        return (
            DeviceMeasurement.objects.select_related(
                "device", "plant", "device__plant__owner"
            )
            .prefetch_related("phase_details")
            .filter(plant__owner=self.request.user)
            .order_by("-timestamp")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["measurement_types"] = DeviceMeasurement.MEASUREMENT_TYPES
        context["selected_type"] = self.request.GET.get("type", "")
        return context


class MeasurementDetailView(LoginRequiredMixin, DetailView):
    model = DeviceMeasurement
    template_name = "energy/measurements/detail.html"
    context_object_name = "measurement"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("device", "plant", "device__plant__owner")
            .prefetch_related("phase_details")
            .filter(plant__owner=self.request.user)
        )


@login_required
def device_delete(request, pk):
    if request.method == "POST":
        try:
            # SICURO: Verifica ownership implementata
            device = get_object_or_404(
                DeviceConfiguration, pk=pk, plant__owner=request.user
            )

            # Ottieni i topic MQTT prima dell'eliminazione
            device_topics = device.get_mqtt_topics()

            # Memorizza informazioni per il logging
            device_info = f"Dispositivo (ID: {pk}, Device ID: {device.device_id})"

            # Elimina il dispositivo
            device.delete()

            # Log dell'eliminazione
            logger.info(f"{device_info} eliminato dall'utente {request.user}")

            # Aggiorna le sottoscrizioni MQTT
            try:
                client = get_mqtt_client()
                if client and client.is_connected:
                    # Annulla la sottoscrizione ai topic del dispositivo eliminato
                    for topic in device_topics:
                        logger.info(f"Annullamento sottoscrizione a topic: {topic}")
                        client.unsubscribe(topic)

                    # Ottieni i dispositivi rimanenti attivi
                    active_devices = DeviceConfiguration.objects.filter(is_active=True)

                    if active_devices.exists():
                        # Raccogli tutti i topic attivi rimanenti
                        active_topics = []
                        for active_device in active_devices:
                            device_topics = active_device.get_mqtt_topics()
                            active_topics.extend(device_topics)

                        # Sottoscrivi i topic rimanenti
                        for topic in active_topics:
                            logger.info(f"Sottoscrizione a topic: {topic}")
                            client.subscribe(topic)
                    else:
                        # Se non ci sono più dispositivi attivi, usa il topic wildcard
                        default_topic = "cercollettiva/+/+/value"
                        logger.info(
                            f"Nessun dispositivo attivo, sottoscrizione a: "
                            f"{default_topic}"
                        )
                        client.subscribe(default_topic)
            except Exception as mqtt_error:
                logger.error(
                    f"Errore nell'aggiornamento delle sottoscrizioni MQTT: "
                    f"{str(mqtt_error)}"
                )

            return JsonResponse({"success": True})

        except DeviceConfiguration.DoesNotExist:
            logger.warning(
                f"Tentativo di eliminare un dispositivo inesistente (ID: {pk}) "
                f"da parte dell'utente {request.user}"
            )
            return JsonResponse(
                {"success": False, "error": "Dispositivo non trovato"}, status=404
            )

        except Exception as e:
            logger.error(f"Errore nell'eliminazione del dispositivo {pk}: {str(e)}")
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    return JsonResponse(
        {"success": False, "error": "Metodo non consentito"}, status=405
    )
