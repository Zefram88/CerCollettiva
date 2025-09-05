"""
URL Patterns per Monitoring API - CerCollettiva
Definisce gli endpoint per i sistemi di monitoring
"""

from django.urls import path
from .views.api.monitoring import (
    PerformanceMetricsView,
    DeviceInfoView,
    AccessibilityAuditView,
    UserFeedbackView,
    SessionDataView,
    ABTestingParticipationView,
    ABTestingEventView
)

app_name = 'monitoring'

urlpatterns = [
    # Performance Monitoring
    path('api/performance-metrics/', PerformanceMetricsView.as_view(), name='performance_metrics'),
    
    # Device Detection
    path('api/device-info/', DeviceInfoView.as_view(), name='device_info'),
    
    # Accessibility Audit
    path('api/accessibility-audit/', AccessibilityAuditView.as_view(), name='accessibility_audit'),
    
    # User Feedback
    path('api/user-feedback/', UserFeedbackView.as_view(), name='user_feedback'),
    
    # Session Data
    path('api/session-data/', SessionDataView.as_view(), name='session_data'),
    
    # A/B Testing
    path('api/ab-testing/participation/', ABTestingParticipationView.as_view(), name='ab_testing_participation'),
    path('api/ab-testing/event/', ABTestingEventView.as_view(), name='ab_testing_event'),
]
