# core/views/api/plant.py

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Avg, Sum, Count, Q
from django.conf import settings
from django.core.exceptions import ValidationError
from datetime import timedelta
import logging

from ...models import Plant
from energy.models import DeviceConfiguration, DeviceMeasurement
from core.validators import ValidationMixin, APIValidationMixin

logger = logging.getLogger(__name__)


class APIResponseHelper(ValidationMixin, APIValidationMixin):
    """Helper class for standardized API responses"""
    
    @staticmethod
    def success_response(data, status=200):
        """Return standardized success response"""
        return JsonResponse({
            'status': 'success',
            'data': data,
            'timestamp': timezone.now().isoformat()
        }, status=status)
    
    @staticmethod
    def error_response(message, detail=None, status=400):
        """Return standardized error response"""
        response_data = {
            'status': 'error',
            'message': message,
            'timestamp': timezone.now().isoformat()
        }
        if detail:
            response_data['detail'] = detail
        return JsonResponse(response_data, status=status)
    
    @staticmethod
    def validation_error_response(errors, status=400):
        """Return standardized validation error response"""
        return JsonResponse({
            'status': 'error',
            'message': 'Validation failed',
            'validation_errors': errors,
            'timestamp': timezone.now().isoformat()
        }, status=status)


def validate_api_parameters(request, valid_params):
    """Validate API parameters using centralized validation"""
    helper = APIResponseHelper()
    errors = {}
    
    for param, validator in valid_params.items():
        value = request.GET.get(param)
        if value is not None:
            try:
                validated_value = validator(value)
                request.GET = request.GET.copy()
                request.GET[param] = validated_value
            except ValidationError as e:
                errors[param] = str(e)
    
    return errors if errors else None


@login_required
def get_plant_data(request, pk):
    """API per dati impianto in formato JSON"""
    try:
        # Validate API parameters
        from core.validators import POWER_VALIDATOR
        param_validators = {
            'hours': lambda x: min(float(x), 48) if float(x) > 0 else 24,
            'interval': lambda x: max(int(x), 60) if int(x) > 0 else 600
        }
        
        validation_errors = validate_api_parameters(request, param_validators)
        if validation_errors:
            return APIResponseHelper.validation_error_response(validation_errors)
        
        # Verifica permessi in modo più completo e ottimizzato
        if request.user.is_staff:
            plant = get_object_or_404(Plant, pk=pk)
        else:
            # Query ottimizzata per evitare duplicati
            plant = get_object_or_404(
                Plant.objects.filter(
                    Q(owner=request.user) | 
                    Q(cer_configuration__memberships__user=request.user,
                      cer_configuration__memberships__is_active=True)
                ).distinct(),
                pk=pk
            )
        
        # Parametri di query - limita a max 48 ore
        hours = min(float(request.GET.get('hours', 24)), 48)  
        interval = int(request.GET.get('interval', 600))  # Intervallo in secondi
        time_threshold = timezone.now() - timedelta(hours=hours)
        
        # Recupera dispositivo
        device = DeviceConfiguration.objects.filter(plant=plant).first()
        if not device:
            return APIResponseHelper.error_response(
                'Nessun dispositivo trovato',
                'Non esistono dispositivi configurati per questo impianto',
                status=404
            )
            
        # Recupera ultima misurazione per potenza attuale
        last_measurement = DeviceMeasurement.objects.filter(
            device=device
        ).order_by('-timestamp').first()
        
        # Recupera misurazioni per il grafico
        measurements = DeviceMeasurement.objects.filter(
            device=device,
            timestamp__gte=time_threshold
        ).order_by('timestamp')
        
        # Calcola energia giornaliera
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        daily_energy = DeviceMeasurement.objects.filter(
            device=device,
            timestamp__gte=today_start
        ).aggregate(
            total_energy=Sum('energy_total')
        )['total_energy'] or 0
        
        # Formatta dati per il grafico
        data = [{
            'timestamp': measurement.timestamp.isoformat(),
            'power': float(measurement.power),  # In Watt
            'quality': measurement.quality
        } for measurement in measurements]
        
        # Calcola statistiche
        stats = measurements.aggregate(
            avg_power=Avg('power'),
            count=Count('id')
        )
        
        # Power è in Watt, verrà convertito in kW nel frontend
        current_power = float(last_measurement.power) if last_measurement else 0
        
        response_data = {
            'plant_info': {
                'name': plant.name,
                'type': plant.get_plant_type_display(),
                'pod': plant.pod_code
            },
            'data': data,
            'time_range': {
                'start': time_threshold.isoformat(),
                'end': timezone.now().isoformat()
            },
            'stats': {
                'avg_power': float(stats['avg_power'] or 0),
                'count': stats['count']
            },
            'current_power': current_power,
            'daily_energy': float(daily_energy),
            'last_update': last_measurement.timestamp.isoformat() if last_measurement else None
        }
        
        logger.info(f"Returning data for plant {pk}: {len(data)} measurements")
        return APIResponseHelper.success_response(response_data)
        
    except Exception as e:
        # Don't catch Http404 - let it propagate
        from django.http import Http404
        if isinstance(e, Http404):
            raise
        logger.error(f"Error in get_plant_data: {str(e)}", exc_info=True)
        return APIResponseHelper.error_response(
            'Internal server error',
            str(e) if settings.DEBUG else None,
            status=500
        )

@login_required
def plant_measurements_api(request, plant_id):
    """API per le misurazioni di un impianto"""
    try:
        # Validate API parameters
        param_validators = {
            'hours': lambda x: min(int(x), 48) if int(x) > 0 else 24
        }
        
        validation_errors = validate_api_parameters(request, param_validators)
        if validation_errors:
            return APIResponseHelper.validation_error_response(validation_errors)
        
        # Verifica permessi con la stessa logica ottimizzata
        if request.user.is_staff:
            plant = get_object_or_404(Plant, id=plant_id)
        else:
            plant = get_object_or_404(
                Plant.objects.filter(
                    Q(owner=request.user) | 
                    Q(cer_configuration__memberships__user=request.user,
                      cer_configuration__memberships__is_active=True)
                ).distinct(),
                id=plant_id
            )
            
        # Recupera device
        device = DeviceConfiguration.objects.filter(plant=plant).first()
        if not device:
            return APIResponseHelper.error_response(
                'Dispositivo non trovato',
                'Non esistono dispositivi configurati per questo impianto',
                status=404
            )
            
        # Parametri temporali
        hours = min(int(request.GET.get('hours', 24)), 48)  # Max 48h
        time_threshold = timezone.now() - timedelta(hours=hours)
        
        # Recupera misurazioni
        measurements = DeviceMeasurement.objects.filter(
            device=device,
            timestamp__gte=time_threshold
        ).order_by('timestamp')
        
        response_data = {
            'data': [{
                'timestamp': m.timestamp.isoformat(),
                'power': float(m.power),
                'voltage': float(m.voltage),
                'current': float(m.current),
                'energy_total': float(m.energy_total),
                'quality': m.quality
            } for m in measurements],
            'plant_info': {
                'name': plant.name,
                'type': plant.plant_type,
                'pod': plant.pod_code
            },
            'stats': {
                'total_points': measurements.count(),
                'avg_power': float(measurements.aggregate(
                    avg=Avg('power')
                )['avg'] or 0)
            }
        }
        
        return APIResponseHelper.success_response(response_data)
        
    except Exception as e:
        # Don't catch Http404 - let it propagate
        from django.http import Http404
        if isinstance(e, Http404):
            raise
        logger.error(f"Error in plant_measurements_api: {str(e)}", exc_info=True)
        return APIResponseHelper.error_response(
            'Internal server error',
            str(e) if settings.DEBUG else None,
            status=500
        )