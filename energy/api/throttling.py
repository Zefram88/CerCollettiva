# energy/throttling.py
from rest_framework.throttling import UserRateThrottle


class BurstRateThrottle(UserRateThrottle):
    scope = "burst"
    rate = "60/minute"  # 60 richieste al minuto


class SustainedRateThrottle(UserRateThrottle):
    scope = "sustained"
    rate = "1000/hour"  # 1000 richieste all'ora


class HighFrequencyMeasurementThrottle(UserRateThrottle):
    scope = "measurements"
    rate = "100/minute"  # 100 misurazioni al minuto


class AggregateCalculationThrottle(UserRateThrottle):
    scope = "aggregates"
    rate = "30/minute"  # 30 calcoli al minuto


class BulkOperationThrottle(UserRateThrottle):
    scope = "bulk"
    rate = "10/minute"  # 10 operazioni bulk al minuto


class DeviceConfigurationThrottle(UserRateThrottle):
    scope = "device_config"
    rate = "20/minute"  # 20 modifiche configurazione al minuto
