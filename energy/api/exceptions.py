# energy/api/exceptions.py
from rest_framework import status
from rest_framework.exceptions import APIException


class DeviceOfflineError(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = "Il dispositivo è offline."
    default_code = "device_offline"


class BulkOperationError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Errore durante operazione bulk."
    default_code = "bulk_operation_error"


class CacheError(APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "Errore di cache."
    default_code = "cache_error"


class MeasurementValidationError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Errore nella validazione della misurazione."
    default_code = "measurement_validation_error"
