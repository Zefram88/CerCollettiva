# core/views/api/mqtt.py

import logging

from django.contrib.auth.decorators import login_required
# from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone

from core.validators import APIValidationMixin, ValidationMixin
from energy.models import DeviceConfiguration

from ...models import Plant

logger = logging.getLogger(__name__)


class APIResponseHelper(ValidationMixin, APIValidationMixin):
    """Helper class for standardized API responses"""

    @staticmethod
    def success_response(data, status=200):
        """Return standardized success response"""
        return JsonResponse(
            {
                "status": "success",
                "data": data,
                "timestamp": timezone.now().isoformat(),
            },
            status=status,
        )

    @staticmethod
    def error_response(message, detail=None, status=400):
        """Return standardized error response"""
        response_data = {
            "status": "error",
            "message": message,
            "timestamp": timezone.now().isoformat(),
        }
        if detail:
            response_data["detail"] = detail
        return JsonResponse(response_data, status=status)


@login_required
def mqtt_status_api(request, plant_id):
    """API per stato connessione MQTT"""
    try:
        # Verifica permessi
        if request.user.is_staff:
            plant = get_object_or_404(Plant, id=plant_id)
        else:
            plant = get_object_or_404(Plant, id=plant_id, owner=request.user)

        # Recupera device
        device = DeviceConfiguration.objects.filter(plant=plant).first()

        # Verifica stato connessione
        is_connected = False
        last_seen = None

        if device:
            if device.last_seen:
                time_diff = (timezone.now() - device.last_seen).total_seconds()
                is_connected = time_diff < 300  # 5 minuti
                last_seen = device.last_seen.isoformat()

        response_data = {
            "mqtt_status": {"connected": is_connected, "last_seen": last_seen},
            "device_info": (
                {
                    "id": device.device_id if device else None,
                    "type": device.get_device_type_display() if device else None,
                }
                if device
                else None
            ),
        }

        return APIResponseHelper.success_response(response_data)

    except Exception as e:
        # Don't catch Http404 - let it propagate
        from django.http import Http404

        if isinstance(e, Http404):
            raise
        logger.error(f"Error in mqtt_status_api: {str(e)}", exc_info=True)
        return APIResponseHelper.error_response(
            "Internal server error",
            str(e) if hasattr(e, "__str__") else None,
            status=500,
        )
