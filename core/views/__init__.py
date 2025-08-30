# core/views/__init__.py
from .dashboard import DashboardView, HomeView, CerDashboardView
from .cer import CERListView, CERDetailView, CERJoinView, MembershipCardView, MemberRegistryView
from .fees import (
    CERFeesManagementView,
    MembershipFeeDetailView,
    MembershipFeeReportView,
    set_membership_fee,
    mark_fee_paid,
    bulk_set_fees
)
from .plant import (
    PlantListView,
    PlantDetailView,
    PlantCreateView,
    PlantUpdateView,
    PlantMQTTConfigView,
    plant_delete    
)
from .document import (
    PlantDocumentListView,
    PlantDocumentUploadView,
    PlantDocumentDeleteView
)
from .gaudi import NewPlantFromGaudiView, PlantGaudiUpdateView
from .mqtt import mqtt_reconnect_view
from .economic import (
    EconomicDashboardView,
    CERDistributionDetailView,
    GSEPaymentsListView,
    EconomicReportsView,
    distribution_simulation_ajax
)

__all__ = [
    'DashboardView',
    'HomeView',
    'CerDashboardView',
    'CERListView',
    'CERDetailView',
    'CERJoinView',
    'MembershipCardView',
    'MemberRegistryView',
    'CERFeesManagementView',
    'MembershipFeeDetailView',
    'MembershipFeeReportView',
    'set_membership_fee',
    'mark_fee_paid',
    'bulk_set_fees',
    'PlantListView',
    'PlantDetailView',
    'PlantCreateView',
    'PlantUpdateView',
    'PlantMQTTConfigView',
    'plant_delete',
    'PlantDocumentListView',
    'PlantDocumentUploadView',
    'PlantDocumentDeleteView',
    'NewPlantFromGaudiView',
    'PlantGaudiUpdateView',
    'mqtt_reconnect_view',
    'EconomicDashboardView',
    'CERDistributionDetailView',
    'GSEPaymentsListView',
    'EconomicReportsView',
    'distribution_simulation_ajax'
]