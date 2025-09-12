# core/views/__init__.py
from .cer import (
    CERDetailView,
    CERJoinView,
    CERListView,
    MemberRegistryView,
    MembershipCardView,
)
from .dashboard import CerDashboardView, DashboardView, HomeView
from .document import (
    PlantDocumentDeleteView,
    PlantDocumentListView,
    PlantDocumentUploadView,
)
from .economic import (
    CERDistributionDetailView,
    EconomicDashboardView,
    EconomicReportsView,
    GSEPaymentsListView,
    distribution_simulation_ajax,
)
from .fees import (
    CERFeesManagementView,
    MembershipFeeDetailView,
    MembershipFeeReportView,
    bulk_set_fees,
    mark_fee_paid,
    set_membership_fee,
)
from .gaudi import NewPlantFromGaudiView, PlantGaudiUpdateView
from .mqtt import mqtt_reconnect_view
from .plant import (
    PlantCreateView,
    PlantDetailView,
    PlantListView,
    PlantMQTTConfigView,
    PlantUpdateView,
    plant_delete,
)

__all__ = [
    "DashboardView",
    "HomeView",
    "CerDashboardView",
    "CERListView",
    "CERDetailView",
    "CERJoinView",
    "MembershipCardView",
    "MemberRegistryView",
    "CERFeesManagementView",
    "MembershipFeeDetailView",
    "MembershipFeeReportView",
    "set_membership_fee",
    "mark_fee_paid",
    "bulk_set_fees",
    "PlantListView",
    "PlantDetailView",
    "PlantCreateView",
    "PlantUpdateView",
    "PlantMQTTConfigView",
    "plant_delete",
    "PlantDocumentListView",
    "PlantDocumentUploadView",
    "PlantDocumentDeleteView",
    "NewPlantFromGaudiView",
    "PlantGaudiUpdateView",
    "mqtt_reconnect_view",
    "EconomicDashboardView",
    "CERDistributionDetailView",
    "GSEPaymentsListView",
    "EconomicReportsView",
    "distribution_simulation_ajax",
]
