"""
URL configuration for monitoring endpoints
"""
from django.urls import path
from .views import (
    HealthCheckView,
    DatabaseHealthView,
    MQTTHealthView,
    CacheHealthView,
    SystemHealthView,
    StatusView,
    MetricsView
)

app_name = 'monitoring'

urlpatterns = [
    # Basic health check
    path('health/', HealthCheckView.as_view(), name='health'),
    
    # Service-specific health checks
    path('health/database/', DatabaseHealthView.as_view(), name='health_database'),
    path('health/mqtt/', MQTTHealthView.as_view(), name='health_mqtt'),
    path('health/cache/', CacheHealthView.as_view(), name='health_cache'),
    path('health/system/', SystemHealthView.as_view(), name='health_system'),
    
    # Aggregated status
    path('status/', StatusView.as_view(), name='status'),
    
    # Prometheus metrics
    path('metrics/', MetricsView.as_view(), name='metrics'),
]