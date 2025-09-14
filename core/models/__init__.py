# core/models/__init__.py
# Import delle classi principali da core.models.py
# Usa import diretto dal file per evitare conflitti con la directory
# import os
# import sys
from importlib import import_module

# from .audit import CERDocumentAudit, EconomicTransactionAudit, UserActionAudit
# from .economic import EconomicTransaction, TransactionApproval

# Import diretto del modulo core.main_models.py
models_module = import_module("core.main_models")

# Esporta le classi principali
CERConfiguration = models_module.CERConfiguration
CERMembership = models_module.CERMembership
Plant = models_module.Plant
PlantMeasurement = models_module.PlantMeasurement
PlantDocument = models_module.PlantDocument
Alert = models_module.Alert
MembershipCard = models_module.MembershipCard
MemberRegistry = models_module.MemberRegistry
CERDistributionConfiguration = models_module.CERDistributionConfiguration
GSEIncomeTracking = models_module.GSEIncomeTracking

# Esporta funzioni
generate_mqtt_client_id = models_module.generate_mqtt_client_id
