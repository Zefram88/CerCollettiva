# energy/validators/__init__.py
"""
Validatori Pydantic per il modulo energy
Sistema centralizzato di validazione input per prevenire injection e corruzione dati
"""

from documents.validators.document_validators import (
    DocumentAccessValidator,
    DocumentCreateValidator,
    DocumentFileValidator,
    DocumentSearchValidator,
    DocumentUpdateValidator,
)

from .device_validators import (
    DeviceConfigurationCreateValidator,
    DeviceConfigurationUpdateValidator,
    DeviceCreateValidator,
    DeviceUpdateValidator,
)
from .measurement_validators import (
    DeviceMeasurementDetailValidator,
    MeasurementCreateValidator,
    MeasurementUpdateValidator,
)

# Import validatori legacy per compatibilità
try:
    from ..validators import (
        API_REQUEST_VALIDATOR,
        DEVICE_VALIDATOR,
        MEASUREMENT_VALIDATOR,
        MQTT_VALIDATOR,
        EnergyAPIValidationMixin,
        EnergyValidationMixin,
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
    "DeviceCreateValidator",
    "DeviceUpdateValidator",
    "DeviceConfigurationCreateValidator",
    "DeviceConfigurationUpdateValidator",
    "MeasurementCreateValidator",
    "MeasurementUpdateValidator",
    "DeviceMeasurementDetailValidator",
    "DocumentCreateValidator",
    "DocumentUpdateValidator",
    "DocumentAccessValidator",
    "DocumentFileValidator",
    "DocumentSearchValidator",
    "MQTT_VALIDATOR",
    "MEASUREMENT_VALIDATOR",
    "DEVICE_VALIDATOR",
    "API_REQUEST_VALIDATOR",
    "EnergyValidationMixin",
    "EnergyAPIValidationMixin",
]
