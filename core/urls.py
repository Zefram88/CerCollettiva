from django.urls import path
from django.contrib import admin
from .admin import admin_site
from .views.gaudi import PlantCreateFromGaudiView
from .views.dashboard import HomeView, DashboardView, CerDashboardView
from .views.cer import CERListView, CERDetailView, CERPublicDetailView, CERJoinView, MembershipCardView, MemberRegistryView
from .views.fees import CERFeesManagementView, MembershipFeeDetailView, set_membership_fee, mark_fee_paid, bulk_set_fees
from .views.setup import InitialSetupView, setup_complete_view, setup_check_view
from .views.plant import (
    PlantListView,
    PlantDetailView,
    PlantCreateView,
    PlantUpdateView,
    PlantMQTTConfigView,
    plant_delete
)
from .views.document import (
    PlantDocumentListView,
    PlantDocumentUploadView,
    PlantDocumentDeleteView
)
from .views.gaudi import NewPlantFromGaudiView, PlantGaudiUpdateView

from .views.api import (
    get_plant_data,
    plant_measurements_api,
    cer_power_api,
    mqtt_status_api
)

app_name = 'core'

urlpatterns = [
    # Setup iniziale
    path('setup/', InitialSetupView.as_view(), name='initial_setup'),
    path('setup/complete/', setup_complete_view, name='setup_complete'),
    path('setup/check/', setup_check_view, name='setup_check'),
    
    # Home e Dashboard
    path('', HomeView.as_view(), name='home'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),

    # CER URLs
    path('cer/', CERListView.as_view(), name='cer_list'),
    path('cer/<int:pk>/', CERDetailView.as_view(), name='cer_detail'),
    path('cer/<int:pk>/public/', CERPublicDetailView.as_view(), name='cer_public_detail'),
    path('cer/<int:pk>/join/', CERJoinView.as_view(), name='cer_join'),
    path('cer/<int:cer_pk>/card/', MembershipCardView.as_view(), name='membership_card'),
    path('cer/<int:cer_pk>/registry/', MemberRegistryView.as_view(), name='member_registry'),
    path('cer/<int:cer_pk>/fees/', CERFeesManagementView.as_view(), name='cer_fees'),
    path('cer/fee/<int:pk>/', MembershipFeeDetailView.as_view(), name='membership_fee_detail'),
    
    # Plant URLs - Base Operations
    path('plants/', PlantListView.as_view(), name='plant_list'),
    path('plants/create/', PlantCreateView.as_view(), name='plant_create'),
    path('plants/<int:pk>/', PlantDetailView.as_view(), name='plant_detail'),
    path('plants/<int:pk>/update/', PlantUpdateView.as_view(), name='plant_update'),
    path('plants/<int:pk>/delete/', plant_delete, name='plant_delete'),

    # Plant URLs - Gaudì Operations
    path('plants/new-from-gaudi/', NewPlantFromGaudiView.as_view(), name='plant_new_from_gaudi'),
    path('plants/create-from-gaudi/', PlantCreateFromGaudiView.as_view(), name='plant_create_with_gaudi'),
    path('plants/<int:pk>/gaudi-update/', PlantGaudiUpdateView.as_view(), name='plant_gaudi_update'),

    # Plant URLs - MQTT Configuration
    path('plants/<int:pk>/mqtt/', PlantMQTTConfigView.as_view(), name='plant_mqtt_config'),
    
    # Plant URLs - Document Management
    path('plants/<int:pk>/documents/', PlantDocumentListView.as_view(), name='plant_documents'),
    path('plants/<int:pk>/documents/upload/', PlantDocumentUploadView.as_view(), name='plant_document_upload'),
    path('plants/<int:pk>/documents/<int:document_id>/delete/', 
         PlantDocumentDeleteView.as_view(), 
         name='plant_document_delete'),
    
    # API URLs - Moved these to the top of API section for clarity
    path('api/plants/<int:pk>/data/', get_plant_data, name='api_plant_data'),
    path('api/plants/<int:plant_id>/measurements/', plant_measurements_api, name='plant-measurements-api'),
    path('api/cer-power/', cer_power_api, name='cer-power-api'),
    path('api/mqtt/status/<int:plant_id>/', mqtt_status_api, name='mqtt-status-api'),
    
    # API URLs - Fees Management
    path('api/fees/set/<int:card_id>/', set_membership_fee, name='api_set_fee'),
    path('api/fees/paid/<int:card_id>/', mark_fee_paid, name='api_mark_fee_paid'),
    path('api/cer/<int:cer_pk>/bulk-fees/', bulk_set_fees, name='api_bulk_fees')
]