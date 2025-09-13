# energy/views/__init__.py
# flake8: noqa
from .api import DeviceConfigurationViewSet, DeviceMeasurementViewSet, PlantViewSet
from .dashboard_views import DashboardView, total_power_data
from .debug_views import debug_device_status, debug_mqtt_config
from .device_views import (
    DeviceCreateView,
    DeviceDetailView,
    DeviceListView,
    MeasurementDetailView,
    MeasurementListView,
    device_delete,
)
from .mqtt_views import mqtt_control, mqtt_settings, save_mqtt_settings
from .plant_views import (
    PlantCreateView,
    PlantDetailView,
    PlantListView,
    plant_delete,
    plant_mqtt_data,
)
