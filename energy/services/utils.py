# energy/services/utils.py
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from django.db.models import Avg, Max, Min, Sum, Q
from django.utils import timezone
from ..models import (
    DeviceMeasurement, 
    EnergyMeasurement, 
    EnergyAggregate
)

def calculate_period_aggregates(
    device_id: str,
    start_date: datetime,
    end_date: datetime,
    period: str = '1H'
) -> List[EnergyAggregate]:
    """
    Calcola le aggregazioni per un periodo specifico
    """
    aggregates = []
    current_start = start_date

    while current_start < end_date:
        # Determina la fine del periodo corrente
        if period == '15M':
            current_end = current_start + timedelta(minutes=15)
        elif period == '1H':
            current_end = current_start + timedelta(hours=1)
        elif period == '1D':
            current_end = current_start + timedelta(days=1)
        else:
            raise ValueError(f"Periodo non supportato: {period}")

        # Ottieni le misurazioni per il periodo
        measurements = DeviceMeasurement.objects.filter(
            device__device_id=device_id,
            timestamp__gte=current_start,
            timestamp__lt=current_end
        )

        if measurements.exists():
            agg = measurements.aggregate(
                avg_power=Avg('power'),
                peak_power=Max('power'),
                min_power=Min('power')
            )

            # Calcola energie
            energy_values = EnergyMeasurement.objects.filter(
                device_measurement__in=measurements
            ).aggregate(
                energy_in=Sum('value', filter=Q(measurement_type='POWER_IN')),
                energy_out=Sum('value', filter=Q(measurement_type='POWER_DRAW'))
            )

            # Crea o aggiorna l'aggregazione
            aggregate, _ = EnergyAggregate.objects.update_or_create(
                device_id=device_id,
                period=period,
                start_time=current_start,
                defaults={
                    'end_time': current_end,
                    'energy_in': energy_values.get('energy_in', 0),
                    'energy_out': energy_values.get('energy_out', 0),
                    'peak_power': agg['peak_power'],
                    'avg_power': agg['avg_power']
                }
            )
            
            aggregates.append(aggregate)

        current_start = current_end

    return aggregates

def get_latest_measurement(device_id: str) -> Optional[DeviceMeasurement]:
    """
    Recupera l'ultima misurazione per un dispositivo
    """
    try:
        return DeviceMeasurement.objects.filter(
            device__device_id=device_id
        ).latest('timestamp')
    except DeviceMeasurement.DoesNotExist:
        return None

def check_measurement_quality(measurement: DeviceMeasurement) -> str:
    """
    Verifica la qualità di una misurazione
    """
    if measurement.age > 300:  # Più di 5 minuti
        return 'BAD'
    if abs(measurement.power_factor) > 1:
        return 'BAD'
    if measurement.voltage < 180 or measurement.voltage > 260:
        return 'UNCERTAIN'
    return 'GOOD'
