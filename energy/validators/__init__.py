# energy/validators/__init__.py
"""
Validatori Pydantic per il modulo energy
Sistema centralizzato di validazione input per prevenire injection e corruzione dati
"""

from .device_validators import (
    DeviceCreateValidator,
    DeviceUpdateValidator,
    DeviceConfigurationCreateValidator,
    DeviceConfigurationUpdateValidator
)
from .measurement_validators import (
    MeasurementCreateValidator,
    MeasurementUpdateValidator,
    DeviceMeasurementDetailValidator
)
from documents.validators.document_validators import (
    DocumentCreateValidator,
    DocumentUpdateValidator,
    DocumentAccessValidator,
    DocumentFileValidator,
    DocumentSearchValidator
)

# Import validatori legacy per compatibilità
try:
    from ..validators import (
        MQTT_VALIDATOR, 
        MEASUREMENT_VALIDATOR,
        DEVICE_VALIDATOR,
        API_REQUEST_VALIDATOR,
        EnergyValidationMixin,
        EnergyAPIValidationMixin
    )
except ImportError:
    # Fallback per evitare circular import
    MQTT_VALIDATOR = None
    MEASUREMENT_VALIDATOR = None
    DEVICE_VALIDATOR = None
    API_REQUEST_VALIDATOR = None
    EnergyValidationMixin = None
    EnergyAPIValidationMixin = None

__all__ = [
    'DeviceCreateValidator',
    'DeviceUpdateValidator', 
    'DeviceConfigurationCreateValidator',
    'DeviceConfigurationUpdateValidator',
    'MeasurementCreateValidator',
    'MeasurementUpdateValidator',
    'DeviceMeasurementDetailValidator',
    'DocumentCreateValidator',
    'DocumentUpdateValidator',
    'DocumentAccessValidator',
    'DocumentFileValidator',
    'DocumentSearchValidator',
    'MQTT_VALIDATOR',
    'MEASUREMENT_VALIDATOR',
    'DEVICE_VALIDATOR',
    'API_REQUEST_VALIDATOR',
    'EnergyValidationMixin',
    'EnergyAPIValidationMixin'
]
