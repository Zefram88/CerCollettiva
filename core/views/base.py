# core/views/base.py

from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.views.generic import TemplateView

from energy.models import DeviceConfiguration, DeviceMeasurement

from ..models import CERConfiguration, Plant
from .mixins.gdpr import GDPRDataProtectionMixin


class CerBaseView(LoginRequiredMixin, GDPRDataProtectionMixin, TemplateView):
    """Vista base per tutte le viste di CerCollettiva"""

    def get_time_threshold(self, minutes=5):
        """Restituisce la soglia temporale per i dati recenti"""
        return timezone.now() - timezone.timedelta(minutes=minutes)

    def get_plant_measurements(self, plant, time_threshold=None):
        """Recupera le misurazioni recenti di un impianto"""
        if time_threshold is None:
            time_threshold = self.get_time_threshold()

        device = DeviceConfiguration.objects.filter(plant=plant).first()
        if not device:
            return None

        return DeviceMeasurement.objects.filter(
            device=device, timestamp__gte=time_threshold
        ).order_by("-timestamp")

    def calculate_power_data(self, plant_measurements):
        """Calcola i dati di potenza dalle misurazioni"""
        if not plant_measurements:
            return {"current_power": 0, "direction": "none", "power_kw": 0}

        latest = plant_measurements.first()
        power = latest.power if latest else 0

        return {
            "current_power": abs(power),
            "direction": "production" if power > 0 else "consumption",
            "power_kw": round(abs(power) / 1000.0, 2),
        }

    def get_devices_status(self, plant):
        """Recupera lo stato dei dispositivi di un impianto"""
        devices = DeviceConfiguration.objects.filter(plant=plant)
        time_threshold = self.get_time_threshold()

        status = {
            "total": devices.count(),
            "online": 0,
            "offline": 0,
            "last_update": None,
        }

        for device in devices:
            latest = device.measurements.filter(timestamp__gte=time_threshold).first()

            if latest:
                status["online"] += 1
                if (
                    not status["last_update"]
                    or latest.timestamp > status["last_update"]
                ):
                    status["last_update"] = latest.timestamp
            else:
                status["offline"] += 1

        return status


class BasePlantView(CerBaseView):
    """Vista base per le viste relative agli impianti"""

    model = Plant

    def get_queryset(self):
        if self.request.user.is_staff:
            return Plant.objects.all()
        return Plant.objects.filter(owner=self.request.user)


class BaseCERView(CerBaseView):
    """Vista base per le viste relative alle CER"""

    model = CERConfiguration

    def get_queryset(self):
        if self.request.user.is_staff:
            return CERConfiguration.objects.all()
        return CERConfiguration.objects.filter(
            memberships__user=self.request.user, memberships__is_active=True
        ).distinct()
