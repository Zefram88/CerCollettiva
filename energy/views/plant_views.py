# energy/views/plant_views.py
import logging
from datetime import timedelta

from django import forms
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Max, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DetailView, ListView

from core.main_models import Plant

from ..models import DeviceConfiguration, DeviceMeasurement

logger = logging.getLogger(__name__)


class PlantListView(LoginRequiredMixin, ListView):
    model = Plant
    template_name = "energy/plants/list.html"
    context_object_name = "plants"

    def get_queryset(self):
        """
        Restituisce il queryset degli impianti.
        Staff può vedere tutti gli impianti o filtrati per proprietario,
        utenti normali solo i propri.
        """
        base_queryset = Plant.objects.prefetch_related("devices").select_related(
            "owner"
        )
        if self.request.user.is_staff:
            owner_id = self.request.GET.get("owner")
            if owner_id:
                return base_queryset.filter(owner_id=owner_id)
            return base_queryset
        return base_queryset.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.localtime()
        time_threshold = now - timedelta(minutes=5)

        # Aggiungi lista proprietari per il filtro admin
        if self.request.user.is_staff:
            User = get_user_model()
            context["owners"] = User.objects.filter(plants__isnull=False).distinct()
            context["selected_owner"] = self.request.GET.get("owner")

        try:
            plants = self.get_queryset()
            devices_data = []

            # Per gli amministratori, otteniamo la potenza totale in base al filtro
            if self.request.user.is_staff:
                owner_id = self.request.GET.get("owner")
                if owner_id:
                    total_power = Plant.get_total_system_power(user_id=owner_id)
                else:
                    total_power = Plant.get_total_system_power()
            else:
                total_power = Plant.get_total_system_power(user=self.request.user)

            logger.info(f"Potenza totale sistema calcolata: {total_power} kW")

            # Iteriamo sugli impianti per raccogliere i dati dei dispositivi
            for plant in plants:
                devices = DeviceConfiguration.objects.filter(plant=plant)
                logger.info(f"Elaborazione impianto: {plant.name}")

                # Otteniamo i dati delle ultime misurazioni per questo impianto
                latest_measurements = (
                    DeviceMeasurement.objects.filter(
                        device__plant=plant, timestamp__gte=time_threshold
                    )
                    .values("device")
                    .annotate(
                        latest_power=Max("power"), latest_timestamp=Max("timestamp")
                    )
                )

                # Raccogli i dati dei dispositivi
                for device in devices:
                    device_measurement = next(
                        (m for m in latest_measurements if m["device"] == device.id),
                        None,
                    )

                    devices_data.append(
                        {
                            "id": device.id,
                            "device_id": device.device_id,
                            "device_type": device.get_device_type_display(),
                            "power": (
                                device_measurement["latest_power"]
                                if device_measurement
                                else 0
                            ),
                            "is_online": bool(device_measurement),
                            "last_seen": (
                                timezone.localtime(
                                    device_measurement["latest_timestamp"]
                                )
                                if device_measurement
                                and device_measurement["latest_timestamp"]
                                else None
                            ),
                        }
                    )

            # Calcola l'energia totale giornaliera
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            total_energy = (
                DeviceMeasurement.objects.filter(
                    device__plant__in=plants, timestamp__gte=today_start
                ).aggregate(total=Sum("energy_total"))["total"]
                or 0
            )

            logger.info(f"Daily energy consumption: {total_energy:.2f} kWh")

            context.update(
                {
                    "devices": devices_data,
                    "mqtt_data": {"drawn_power": total_power},
                    "total_power": total_power,
                    "plantTotalPower": total_power,
                    "plantDeviceCount": sum(
                        DeviceConfiguration.objects.filter(
                            plant=plant, is_active=True
                        ).count()
                        for plant in plants
                    ),
                    "plantTodayEnergy": round(total_energy, 2),
                    "today_energy": round(total_energy, 2),
                    "plantLastUpdate": now if devices_data else None,
                    "online_devices": sum(1 for d in devices_data if d["is_online"]),
                    "total_devices": len(devices_data),
                }
            )

        except Exception as e:
            logger.error(f"Error retrieving plant data: {str(e)}", exc_info=True)
            context.update(
                {
                    "devices": [],
                    "mqtt_data": {"drawn_power": 0},
                    "total_power": 0,
                    "plantTotalPower": 0,
                    "plantDeviceCount": 0,
                    "plantTodayEnergy": 0,
                    "today_energy": 0,
                    "online_devices": 0,
                    "total_devices": 0,
                }
            )

        return context


class PlantCreateView(LoginRequiredMixin, CreateView):
    model = Plant
    template_name = "energy/plants/create.html"
    fields = ["name", "pod_code", "city", "is_active"]
    success_url = reverse_lazy("energy:plants")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        # Aggiungi classi Bootstrap ai campi
        for field in form.fields.values():
            field.widget.attrs.update({"class": "form-control"})

        # Aggiungi il campo owner solo per gli amministratori
        if self.request.user.is_staff:
            form.fields["owner"] = forms.ModelChoiceField(
                queryset=get_user_model().objects.all().order_by("username"),
                label="Proprietario",
                widget=forms.Select(attrs={"class": "form-control"}),
                help_text="Seleziona il proprietario dell'impianto",
            )

        return form

    def form_valid(self, form):
        try:
            if not self.request.user.is_staff:
                form.instance.owner = self.request.user

            response = super().form_valid(form)
            messages.success(self.request, "Impianto creato con successo")
            return response

        except Exception as e:
            logger.error(f"Errore nella creazione dell'impianto: {str(e)}")
            messages.error(self.request, "Errore nella creazione dell'impianto")
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {"title": "Nuovo Impianto", "is_admin": self.request.user.is_staff}
        )
        return context


class PlantDetailView(LoginRequiredMixin, DetailView):
    model = Plant
    template_name = "energy/plants/detail.html"
    context_object_name = "plant"

    def get_queryset(self):
        """
        Limita l'accesso agli impianti in base ai permessi dell'utente
        """
        if self.request.user.is_staff:
            return Plant.objects.all()
        return Plant.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        plant = self.get_object()
        now = timezone.localtime()
        time_threshold = now - timedelta(minutes=5)

        devices = DeviceConfiguration.objects.filter(plant=plant)
        devices_data = []

        logger.info(f"\nCalcolo potenza per impianto: {plant.name}")
        logger.info(f"Timestamp threshold: {time_threshold}")

        latest_measurements = (
            DeviceMeasurement.objects.filter(
                device__plant=plant, timestamp__gte=time_threshold
            )
            .values("device")
            .annotate(latest_power=Max("power"), latest_timestamp=Max("timestamp"))
        )

        total_power = sum(
            m["latest_power"]
            for m in latest_measurements
            if m["latest_power"] is not None
        )
        logger.info(f"Trovati {len(latest_measurements)} dispositivi attivi")
        logger.info(f"Potenza totale calcolata: {total_power}W")

        for device in devices:
            device_measurement = next(
                (m for m in latest_measurements if m["device"] == device.id), None
            )

            device_data = {
                "id": device.id,
                "device_id": device.device_id,
                "device_type": device.get_device_type_display(),
                "power": 0,
                "is_online": False,
                "last_seen": None,
            }

            if device_measurement:
                logger.info(
                    f"Dispositivo {device.device_id}: {device_measurement['latest_power']}W"
                )

                device_data.update(
                    {
                        "power": device_measurement["latest_power"],
                        "is_online": True,
                        "last_seen": timezone.localtime(
                            device_measurement["latest_timestamp"]
                        ),
                    }
                )

            devices_data.append(device_data)

        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        total_energy = (
            DeviceMeasurement.objects.filter(
                device__plant=plant, timestamp__gte=today_start
            ).aggregate(total=Sum("energy_total"))["total"]
            or 0
        )

        logger.info(f"Potenza totale calcolata: {total_power / 1000.0} kW")
        logger.info(f"Energia totale oggi: {total_energy} kWh")

        context.update(
            {
                "devices": devices_data,
                "mqtt_data": {
                    "drawn_power": round(total_power / 1000.0, 2),
                },
                "plantTotalPower": round(total_power / 1000.0, 2),
                "plantDeviceCount": devices.filter(is_active=True).count(),
                "plantTodayEnergy": round(total_energy, 2),
                "plantLastUpdate": now if devices_data else None,
            }
        )

        return context


@login_required
def plant_delete(request, pk):
    if request.method == "POST":
        try:
            # Permetti agli admin di eliminare qualsiasi impianto
            if request.user.is_staff:
                plant = get_object_or_404(Plant, pk=pk)
            else:
                plant = get_object_or_404(Plant, pk=pk, owner=request.user)

            plant_name = plant.name
            plant.delete()
            logger.info(
                f"Impianto {plant_name} (ID: {pk}) eliminato dall'utente {request.user}"
            )
            return JsonResponse(
                {
                    "success": True,
                    "message": f"Impianto {plant_name} eliminato con successo",
                }
            )

        except Plant.DoesNotExist:
            logger.warning(
                f"Tentativo di eliminare un impianto inesistente (ID: {pk}) da parte dell'utente {request.user}"
            )
            return JsonResponse(
                {"success": False, "error": "Impianto non trovato"}, status=404
            )

        except Exception as e:
            logger.error(f"Errore nell'eliminazione dell'impianto {pk}: {str(e)}")
            return JsonResponse(
                {
                    "success": False,
                    "error": "Errore durante l'eliminazione dell'impianto",
                },
                status=500,
            )

    return JsonResponse(
        {"success": False, "error": "Metodo non consentito"}, status=405
    )


@login_required
def plant_mqtt_data(request, plant_id=None):
    try:
        now = timezone.localtime()
        time_range = request.GET.get("range", "5m")

        # Determina l'intervallo temporale e il periodo di aggregazione
        if time_range == "5m":
            time_threshold = now - timedelta(minutes=5)
            aggregation_minutes = 1
        elif time_range == "1h":
            time_threshold = now - timedelta(hours=1)
            aggregation_minutes = 5
        elif time_range == "24h":
            time_threshold = now - timedelta(days=1)
            aggregation_minutes = 15
        else:
            time_threshold = now - timedelta(minutes=5)
            aggregation_minutes = 1

        # Modifica la query per permettere agli admin di vedere tutti gli impianti
        if plant_id:
            if request.user.is_staff:
                plants = Plant.objects.filter(id=plant_id)
            else:
                plants = Plant.objects.filter(id=plant_id, owner=request.user)
        else:
            if request.user.is_staff:
                plants = Plant.objects.all()
            else:
                plants = Plant.objects.filter(owner=request.user)

        response_data = {}

        for plant in plants:
            devices = DeviceConfiguration.objects.filter(plant=plant)
            device_ids = list(devices.values_list("id", flat=True))

            # Ottieni dati per il grafico
            measurements = DeviceMeasurement.objects.filter(
                device__in=device_ids, timestamp__gte=time_threshold
            ).order_by("timestamp")

            # Aggregazione dei dati per il grafico
            data_points = {}
            for measurement in measurements:
                # Arrotonda il timestamp al periodo di aggregazione più vicino
                rounded_time = measurement.timestamp.replace(
                    second=0,
                    microsecond=0,
                    minute=(measurement.timestamp.minute // aggregation_minutes)
                    * aggregation_minutes,
                )

                if rounded_time not in data_points:
                    data_points[rounded_time] = {"power_sum": 0, "count": 0}

                data_points[rounded_time]["power_sum"] += measurement.power
                data_points[rounded_time]["count"] += 1

            # Prepara i dati del grafico
            chart_data = {"timestamps": [], "values": []}

            for timestamp in sorted(data_points.keys()):
                point = data_points[timestamp]
                avg_power = point["power_sum"] / point["count"]

                chart_data["timestamps"].append(timestamp.isoformat())
                chart_data["values"].append(
                    round(avg_power / 1000.0, 2)
                )  # Converti in kW

            # Calcola i dati attuali dell'impianto
            latest_measurements = DeviceMeasurement.objects.filter(
                device__in=device_ids, timestamp__gte=now - timedelta(minutes=5)
            ).select_related("device")

            # Prepara i dati dei dispositivi
            devices_data = []
            total_power = 0
            for device in devices:
                device_measurement = (
                    latest_measurements.filter(device=device)
                    .order_by("-timestamp")
                    .first()
                )

                device_data = {
                    "id": device.id,
                    "device_id": device.device_id,
                    "type": device.get_device_type_display(),
                    "model": device.model,
                    "power": 0,
                    "daily_energy": 0,
                    "is_online": False,
                    "last_seen": None,
                }

                if device_measurement:
                    device_data.update(
                        {
                            "power": round(device_measurement.power / 1000, 2),
                            "daily_energy": round(device_measurement.energy_total, 2),
                            "is_online": True,
                            "last_seen": device_measurement.timestamp.isoformat(),
                        }
                    )
                    total_power += device_measurement.power

                devices_data.append(device_data)

            # Calcola energia giornaliera
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            daily_energy = (
                DeviceMeasurement.objects.filter(
                    device__in=device_ids, timestamp__gte=today_start
                ).aggregate(total_energy=Sum("energy_total"))["total_energy"]
                or 0
            )

            plant_data = {
                "drawn_power": round(total_power / 1000.0, 2),
                "power_direction": "prelievo" if total_power < 0 else "immissione",
                "daily_energy": round(daily_energy, 2),
                "last_update": now.isoformat(),
                "devices": devices_data,
                "chart_data": chart_data,  # Aggiungi i dati del grafico
            }

            response_data[str(plant.id)] = plant_data

        return JsonResponse(response_data)

    except Exception as e:
        logger.error(f"Error retrieving MQTT data: {str(e)}", exc_info=True)
        return JsonResponse({"error": str(e)}, status=500)
