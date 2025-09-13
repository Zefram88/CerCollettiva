# energy/api/filters.py
# from functools import lru_cache

# from django.apps import apps
from django.db.models import Q

from django_filters import rest_framework as filters

from core.main_models import Plant

from ..models.device import DeviceConfiguration, DeviceMeasurement
from ..models.energy import EnergyAggregate, EnergyMeasurement


def create_filters():
    """
    Crea i filtri per i vari modelli.
    """

    class PlantFilter(filters.FilterSet):
        search = filters.CharFilter(method="search_filter")

        class Meta:
            model = Plant
            fields = {
                "name": ["exact", "icontains"],
                "pod_code": ["exact", "icontains"],
                "address": ["exact", "icontains"],
                "city": ["exact", "icontains"],
                "plant_type": ["exact"],
                "owner": ["exact"],
                "is_active": ["exact"],
            }

        def search_filter(self, queryset, name, value):
            return queryset.filter(
                Q(name__icontains=value)
                | Q(pod_code__icontains=value)
                | Q(address__icontains=value)
                | Q(city__icontains=value)
            )

    class DeviceConfigurationFilter(filters.FilterSet):
        plant = filters.CharFilter(field_name="plant__name")
        device_id = filters.CharFilter(field_name="device_id", lookup_expr="icontains")
        name = filters.CharFilter(lookup_expr="icontains")
        last_seen_after = filters.DateTimeFilter(
            field_name="last_seen", lookup_expr="gte"
        )

        class Meta:
            model = DeviceConfiguration
            fields = ["device_id", "plant", "name", "is_active", "last_seen"]

    class DeviceMeasurementFilter(filters.FilterSet):
        start_date = filters.DateTimeFilter(field_name="timestamp", lookup_expr="gte")
        end_date = filters.DateTimeFilter(field_name="timestamp", lookup_expr="lte")
        power_min = filters.NumberFilter(field_name="power", lookup_expr="gte")
        power_max = filters.NumberFilter(field_name="power", lookup_expr="lte")
        device = filters.ModelChoiceFilter(queryset=DeviceConfiguration.objects.all())
        device_id = filters.CharFilter(field_name="device__device_id")
        plant = filters.ModelChoiceFilter(queryset=Plant.objects.all())
        plant_id = filters.NumberFilter(field_name="plant__id")
        plant_name = filters.CharFilter(
            field_name="plant__name", lookup_expr="icontains"
        )

        class Meta:
            model = DeviceMeasurement
            fields = [
                "device",
                "plant",
                "quality",
                "power",
                "voltage",
                "current",
                "energy_total",
                "power_factor",
            ]

    class EnergyMeasurementFilter(filters.FilterSet):
        start_date = filters.DateTimeFilter(field_name="timestamp", lookup_expr="gte")
        end_date = filters.DateTimeFilter(field_name="timestamp", lookup_expr="lte")
        value_min = filters.NumberFilter(field_name="value", lookup_expr="gte")
        value_max = filters.NumberFilter(field_name="value", lookup_expr="lte")
        device_id = filters.CharFilter(
            field_name="device_measurement__device__device_id"
        )
        plant_id = filters.NumberFilter(field_name="device_measurement__plant__id")
        plant_name = filters.CharFilter(
            field_name="device_measurement__plant__name", lookup_expr="icontains"
        )

        class Meta:
            model = EnergyMeasurement
            fields = ["measurement_type", "unit", "quality", "value", "topic"]

    class EnergyAggregateFilter(filters.FilterSet):
        start_date = filters.DateTimeFilter(field_name="start_time", lookup_expr="gte")
        end_date = filters.DateTimeFilter(field_name="end_time", lookup_expr="lte")
        device = filters.ModelChoiceFilter(queryset=DeviceConfiguration.objects.all())
        device_id = filters.CharFilter(field_name="device__device_id")
        plant_id = filters.NumberFilter(field_name="device__plant__id")
        plant_name = filters.CharFilter(
            field_name="device__plant__name", lookup_expr="icontains"
        )
        min_energy = filters.NumberFilter(method="filter_min_energy")

        class Meta:
            model = EnergyAggregate
            fields = [
                "period",
                "device",
                "energy_in",
                "energy_out",
                "peak_power",
                "avg_power",
            ]

        def filter_min_energy(self, queryset, name, value):
            """Filtra aggregazioni con energia totale maggiore del valore specificato"""
            return queryset.filter(Q(energy_in__gte=value) | Q(energy_out__gte=value))

    return {
        "PlantFilter": PlantFilter,
        "DeviceConfigurationFilter": DeviceConfigurationFilter,
        "DeviceMeasurementFilter": DeviceMeasurementFilter,
        "EnergyMeasurementFilter": EnergyMeasurementFilter,
        "EnergyAggregateFilter": EnergyAggregateFilter,
    }


# Singleton per i filtri
_FILTERS = None


def get_filters():
    global _FILTERS
    if _FILTERS is None:
        _FILTERS = create_filters()
    return _FILTERS
