# energy/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views.dashboard_views import DashboardView, total_power_data
from .views.plant_views import (
    PlantListView, 
    PlantDetailView, 
    PlantCreateView, 
    plant_delete, 
    plant_mqtt_data
)
from .views.device_views import (
    DeviceListView, 
    DeviceDetailView, 
    DeviceCreateView, 
    MeasurementListView, 
    MeasurementDetailView, 
    device_delete
)
from .views.mqtt_views import mqtt_settings, mqtt_control, save_mqtt_settings, mqtt_status_overview
from .views.api import PlantViewSet, DeviceConfigurationViewSet, DeviceMeasurementViewSet

app_name = 'energy'

# Configurazione Router API REST
router = DefaultRouter()
router.register(r'plants', PlantViewSet, basename='api-plant')
router.register(r'devices', DeviceConfigurationViewSet, basename='api-device')
router.register(r'measurements', DeviceMeasurementViewSet, basename='api-measurement')

urlpatterns = [
    # Vista Dashboard principale
    path('', DashboardView.as_view(), name='dashboard'),

    # Gestione Impianti
    path('plants/', PlantListView.as_view(), name='plants'),
    path('plants/create/', PlantCreateView.as_view(), name='plant-create'),
    path('plants/<int:pk>/', PlantDetailView.as_view(), name='plant-detail'),
    path('plants/<int:pk>/delete/', plant_delete, name='plant-delete'),

    # Gestione Dispositivi
    path('devices/', DeviceListView.as_view(), name='devices'),
    path('devices/create/', DeviceCreateView.as_view(), name='device-create'),
    path('devices/<int:pk>/', DeviceDetailView.as_view(), name='device-detail'),
    path('devices/<int:pk>/delete/', device_delete, name='device-delete'),

    # Gestione Misurazioni
    path('measurements/', MeasurementListView.as_view(), name='measurement-list'),
    path('measurements/<int:pk>/', MeasurementDetailView.as_view(), name='measurement-detail'),

    # Configurazione MQTT
    path('settings/mqtt/', mqtt_settings, name='mqtt_settings'),
    path('settings/mqtt/save/', save_mqtt_settings, name='save_mqtt_settings'),
    path('settings/mqtt/control/', mqtt_control, name='mqtt_control'),
    # API stato MQTT per frontend
    path('api/mqtt/status/', mqtt_status_overview, name='mqtt_status_overview'),

    # API MQTT Data - Messo al livello principale
    path('api/plants/<int:plant_id>/mqtt-data/', plant_mqtt_data, name='plant-mqtt-data'),
    path('api/plants/mqtt-data/', plant_mqtt_data, name='mqtt-data'),

    # API Dispositivi
    path('api/devices/<int:pk>/latest_measurement/',
         DeviceConfigurationViewSet.as_view({'get': 'latest_measurement'}),
         name='api-device-latest-measurement'),
    path('api/measurements/latest/',
         DeviceMeasurementViewSet.as_view({'get': 'latest'}),
         name='api-measurements-latest'),
         
    # API Dati di Potenza
    path('api/total-power/', total_power_data, name='total-power-data'),

    # Inclusione delle API REST standard come ultimo pattern
    path('api/', include(router.urls)),
]
