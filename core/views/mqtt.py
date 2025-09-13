# core/views/mqtt.py

import logging

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from energy.models import DeviceConfiguration

from ..forms import PlantMQTTConfigForm
from ..models import Plant
from .base import BasePlantView

logger = logging.getLogger(__name__)


class PlantMQTTConfigView(BasePlantView, UserPassesTestMixin):
    """Configurazione MQTT per un impianto"""

    template_name = "core/mqtt_config.html"
    form_class = PlantMQTTConfigForm

    def test_func(self):
        """Verifica che l'utente possa modificare la configurazione MQTT"""
        plant = self.get_object()
        return self.request.user.is_staff or plant.owner == self.request.user

    def get_object(self):
        return get_object_or_404(Plant, pk=self.kwargs["pk"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        plant = self.get_object()

        # Aggiungi stato MQTT corrente
        device = DeviceConfiguration.objects.filter(plant=plant).first()
        context["mqtt_status"] = {
            "connected": bool(
                device
                and device.last_seen
                and (timezone.now() - device.last_seen).total_seconds() < 300
            ),
            "last_seen": device.last_seen if device else None,
        }

        return context

    def form_valid(self, form):
        plant = form.save(commit=False)

        try:
            # Test connessione MQTT
            if not plant.test_mqtt_connection():
                messages.error(
                    self.request,
                    _("Test connessione MQTT fallito. Verifica le impostazioni."),
                )
                return self.form_invalid(form)

            # Update configurazione
            plant.save()

            # Log configurazione
            logger.info(
                f"MQTT config updated for plant {plant.id} by user {self.request.user}"
            )

            messages.success(
                self.request, _("Configurazione MQTT aggiornata con successo")
            )
            return redirect("core:plant_detail", pk=plant.pk)

        except Exception as e:
            logger.error(
                f"Error updating MQTT config for plant {plant.id}: {str(e)}",
                exc_info=True,
            )
            messages.error(self.request, str(e))
            return self.form_invalid(form)

    def handle_no_permission(self):
        messages.error(
            self.request, _("Non hai i permessi per modificare la configurazione MQTT")
        )
        return redirect("core:plant_list")


def mqtt_reconnect_view(request, pk):
    """Vista per forzare la riconnessione MQTT"""
    plant = get_object_or_404(Plant, pk=pk)

    if not (request.user.is_staff or plant.owner == request.user):
        messages.error(request, _("Non hai i permessi per questa operazione"))
        return redirect("core:plant_list")

    try:
        if plant.test_mqtt_connection():
            messages.success(request, _("Riconnessione MQTT eseguita con successo"))
        else:
            messages.error(request, _("Riconnessione MQTT fallita"))

    except Exception as e:
        logger.error(
            f"Error reconnecting MQTT for plant {plant.id}: {str(e)}", exc_info=True
        )
        messages.error(request, str(e))

    return redirect("core:plant_detail", pk=pk)
