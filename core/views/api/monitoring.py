"""
API Views per Monitoring Systems - CerCollettiva
Gestisce endpoint per performance, device, accessibility, feedback e A/B testing
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from django.utils import timezone
import json
import logging
from datetime import datetime
from datetime import timezone as dt_timezone

# Import monitoring models
from core.models import (
    PerformanceMetrics,
    DeviceInfo,
    AccessibilityAudit,
    UserFeedback,
    SessionData,
    ABTestingParticipation,
    ABTestingEvent
)

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class PerformanceMetricsView(View):
    """Endpoint per ricevere metriche performance"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            # Log delle metriche ricevute
            logger.info(f"Performance metrics received: {data}")
            
            # Salva le metriche nel database
            performance = PerformanceMetrics.objects.create(
                session_id=data.get('sessionId', 'unknown'),
                url=data.get('url', ''),
                lcp=data.get('lcp'),
                fid=data.get('fid'),
                cls=data.get('cls'),
                fcp=data.get('fcp'),
                ttfb=data.get('ttfb'),
                memory_used=data.get('memory', {}).get('used'),
                memory_total=data.get('memory', {}).get('total'),
                memory_limit=data.get('memory', {}).get('limit'),
                raw_data=data
            )
            
            logger.info(f"Performance metrics saved with ID: {performance.id}")
            
            return JsonResponse({
                'status': 'success',
                'message': 'Performance metrics received and saved',
                'id': performance.id,
                'timestamp': datetime.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            logger.error(f"Error processing performance metrics: {e}")
            return JsonResponse({
                'status': 'error',
                'message': 'Internal server error'
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class DeviceInfoView(View):
    """Endpoint per ricevere informazioni dispositivo"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            # Log delle informazioni dispositivo
            logger.info(f"Device info received: {data}")
            
            return JsonResponse({
                'status': 'success',
                'message': 'Device info received',
                'timestamp': datetime.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            logger.error(f"Error processing device info: {e}")
            return JsonResponse({
                'status': 'error',
                'message': 'Internal server error'
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class AccessibilityAuditView(View):
    """Endpoint per ricevere risultati audit accessibilità"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            # Log dei risultati audit
            logger.info(f"Accessibility audit results received: {data}")
            
            return JsonResponse({
                'status': 'success',
                'message': 'Accessibility audit results received',
                'timestamp': datetime.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            logger.error(f"Error processing accessibility audit: {e}")
            return JsonResponse({
                'status': 'error',
                'message': 'Internal server error'
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class UserFeedbackView(View):
    """Endpoint per ricevere feedback utenti"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            # Log del feedback utente
            logger.info(f"User feedback received: {data}")
            
            return JsonResponse({
                'status': 'success',
                'message': 'User feedback received',
                'timestamp': datetime.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            logger.error(f"Error processing user feedback: {e}")
            return JsonResponse({
                'status': 'error',
                'message': 'Internal server error'
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class SessionDataView(View):
    """Endpoint per ricevere dati sessione utente"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            # Log dei dati sessione
            logger.info(f"Session data received: {data}")
            
            # Salva o aggiorna i dati sessione
            session_data, created = SessionData.objects.update_or_create(
                session_id=data.get('sessionId', 'unknown'),
                defaults={
                    'start_time': timezone.datetime.fromtimestamp(data.get('startTime', 0) / 1000, tz=dt_timezone.utc),
                    'end_time': timezone.datetime.fromtimestamp(data.get('endTime', 0) / 1000, tz=dt_timezone.utc) if data.get('endTime') else None,
                    'session_duration': data.get('sessionDuration'),
                    'page_time': data.get('pageTime', 0),
                    'interactions_count': data.get('interactions', 0),
                    'user_agent': data.get('userAgent', ''),
                    'referrer': data.get('referrer', ''),
                    'screen_resolution': data.get('screenResolution', ''),
                    'viewport_size': data.get('viewportSize', ''),
                    'performance_rating': data.get('performanceRating', ''),
                    'issues_count': data.get('issues', 0),
                    'raw_data': data
                }
            )
            
            action = 'created' if created else 'updated'
            logger.info(f"Session data {action} with ID: {session_data.id}")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Session data received and {action}',
                'id': session_data.id,
                'created': created,
                'timestamp': datetime.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            logger.error(f"Error processing session data: {e}")
            return JsonResponse({
                'status': 'error',
                'message': 'Internal server error'
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class ABTestingParticipationView(View):
    """Endpoint per ricevere partecipazioni A/B testing"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            # Log della partecipazione A/B test
            logger.info(f"A/B testing participation received: {data}")
            
            return JsonResponse({
                'status': 'success',
                'message': 'A/B testing participation received',
                'timestamp': datetime.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            logger.error(f"Error processing A/B testing participation: {e}")
            return JsonResponse({
                'status': 'error',
                'message': 'Internal server error'
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class ABTestingEventView(View):
    """Endpoint per ricevere eventi A/B testing"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            # Log dell'evento A/B test
            logger.info(f"A/B testing event received: {data}")
            
            # Salva l'evento nel database
            event = ABTestingEvent.objects.create(
                session_id=data.get('userId', 'unknown'),
                event_type=data.get('eventType', 'unknown'),
                event_data=data.get('eventData', {}),
                experiments=data.get('experiments', {}),
                url=data.get('url', ''),
                raw_data=data
            )
            
            logger.info(f"A/B testing event saved with ID: {event.id}")
            
            return JsonResponse({
                'status': 'success',
                'message': 'A/B testing event received and saved',
                'id': event.id,
                'timestamp': datetime.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            logger.error(f"Error processing A/B testing event: {e}")
            return JsonResponse({
                'status': 'error',
                'message': 'Internal server error'
            }, status=500)
