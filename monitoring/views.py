"""
Health check and monitoring views for CerCollettiva
"""
import time
import psutil
import json
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views import View
from django.db import connection
from django.core.cache import cache
from django.utils import timezone
from django.conf import settings
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator


class HealthStatus:
    """Health status constants"""
    HEALTHY = 'healthy'
    DEGRADED = 'degraded'
    UNHEALTHY = 'unhealthy'


@method_decorator(never_cache, name='dispatch')
class HealthCheckView(View):
    """Basic health check endpoint"""
    
    def get(self, request):
        """Return basic health status"""
        start_time = time.time()
        
        health_data = {
            'status': HealthStatus.HEALTHY,
            'timestamp': timezone.now().isoformat(),
            'version': getattr(settings, 'VERSION', '1.0.0'),
            'environment': getattr(settings, 'ENVIRONMENT', 'development'),
            'uptime': self._get_uptime(),
            'response_time_ms': None  # Will be set at the end
        }
        
        # Calculate response time
        health_data['response_time_ms'] = round((time.time() - start_time) * 1000, 2)
        
        return JsonResponse(health_data)
    
    def _get_uptime(self):
        """Get system uptime"""
        try:
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            return str(uptime).split('.')[0]  # Remove microseconds
        except:
            return 'unknown'


@method_decorator(never_cache, name='dispatch')
class DatabaseHealthView(View):
    """Database connectivity health check"""
    
    def get(self, request):
        """Check database health"""
        start_time = time.time()
        status = HealthStatus.HEALTHY
        error_message = None
        query_time = None
        
        try:
            # Test database connection with a simple query
            with connection.cursor() as cursor:
                query_start = time.time()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                query_time = round((time.time() - query_start) * 1000, 2)
                
                if result[0] != 1:
                    raise Exception("Unexpected database response")
                
                # Check query performance
                if query_time > 100:  # More than 100ms is degraded
                    status = HealthStatus.DEGRADED
                    error_message = f"Slow database response: {query_time}ms"
                    
        except Exception as e:
            status = HealthStatus.UNHEALTHY
            error_message = str(e)
        
        response_data = {
            'service': 'database',
            'status': status,
            'timestamp': timezone.now().isoformat(),
            'response_time_ms': round((time.time() - start_time) * 1000, 2),
            'query_time_ms': query_time,
            'database': {
                'vendor': connection.vendor,
                'version': connection.Database.version if hasattr(connection.Database, 'version') else 'unknown'
            }
        }
        
        if error_message:
            response_data['error'] = error_message
        
        # Set appropriate status code
        status_code = 200 if status == HealthStatus.HEALTHY else 503 if status == HealthStatus.UNHEALTHY else 207
        
        return JsonResponse(response_data, status=status_code)


@method_decorator(never_cache, name='dispatch')
class MQTTHealthView(View):
    """MQTT broker connectivity health check"""
    
    def get(self, request):
        """Check MQTT broker + service health"""
        from energy.models import MQTTBroker, DeviceConfiguration
        from energy.mqtt.core import get_mqtt_service
        
        start_time = time.time()
        status = HealthStatus.HEALTHY
        error_message = None
        broker_info = {}
        
        try:
            # Broker attivo
            active_broker = MQTTBroker.objects.filter(is_active=True).first()
            if not active_broker:
                status = HealthStatus.DEGRADED
                error_message = "No active MQTT broker configured"
            else:
                broker_info = {
                    'name': active_broker.name,
                    'host': active_broker.host,
                    'port': active_broker.port,
                    'use_tls': active_broker.use_tls
                }

            # Stato servizio MQTT
            svc = get_mqtt_service()
            is_connected = getattr(svc, 'is_connected', False)
            messages_received = getattr(svc, 'messages_received', 0)
            last_error = getattr(svc, 'last_error', None)

            # Dispositivi online negli ultimi 5 minuti
            five_minutes_ago = timezone.now() - timezone.timedelta(minutes=5)
            online_devices = DeviceConfiguration.objects.filter(
                is_active=True,
                last_seen__gte=five_minutes_ago
            ).count()

            if not is_connected:
                status = HealthStatus.DEGRADED if status != HealthStatus.UNHEALTHY else status
                if not error_message:
                    error_message = 'MQTT service disconnected'
                        
        except Exception as e:
            status = HealthStatus.UNHEALTHY
            error_message = str(e)
        
        response_data = {
            'service': 'mqtt',
            'status': status,
            'timestamp': timezone.now().isoformat(),
            'response_time_ms': round((time.time() - start_time) * 1000, 2),
            'broker': broker_info,
            'client': {
                'connected': is_connected if 'is_connected' in locals() else None,
                'messages_received': messages_received if 'messages_received' in locals() else 0,
                'last_error': last_error if 'last_error' in locals() else None,
            },
            'devices': {
                'online_last_5m': online_devices if 'online_devices' in locals() else 0,
            }
        }
        
        if error_message:
            response_data['error'] = error_message
        
        status_code = 200 if status == HealthStatus.HEALTHY else 503 if status == HealthStatus.UNHEALTHY else 207
        
        return JsonResponse(response_data, status=status_code)


@method_decorator(never_cache, name='dispatch')
class CacheHealthView(View):
    """Cache (Redis) connectivity health check"""
    
    def get(self, request):
        """Check cache health"""
        start_time = time.time()
        status = HealthStatus.HEALTHY
        error_message = None
        cache_time = None
        
        try:
            # Test cache operations
            test_key = 'health_check_test'
            test_value = timezone.now().isoformat()
            
            # Test write
            write_start = time.time()
            cache.set(test_key, test_value, 10)
            
            # Test read
            retrieved_value = cache.get(test_key)
            cache_time = round((time.time() - write_start) * 1000, 2)
            
            if retrieved_value != test_value:
                raise Exception("Cache read/write mismatch")
            
            # Clean up
            cache.delete(test_key)
            
            # Check performance
            if cache_time > 50:  # More than 50ms is degraded
                status = HealthStatus.DEGRADED
                error_message = f"Slow cache response: {cache_time}ms"
                
        except Exception as e:
            status = HealthStatus.UNHEALTHY
            error_message = str(e)
        
        response_data = {
            'service': 'cache',
            'status': status,
            'timestamp': timezone.now().isoformat(),
            'response_time_ms': round((time.time() - start_time) * 1000, 2),
            'operation_time_ms': cache_time,
            'backend': getattr(settings, 'CACHE_BACKEND', 'default')
        }
        
        if error_message:
            response_data['error'] = error_message
        
        status_code = 200 if status == HealthStatus.HEALTHY else 503 if status == HealthStatus.UNHEALTHY else 207
        
        return JsonResponse(response_data, status=status_code)


@method_decorator(never_cache, name='dispatch')
class SystemHealthView(View):
    """System resources health check"""
    
    def get(self, request):
        """Check system resources"""
        start_time = time.time()
        status = HealthStatus.HEALTHY
        warnings = []
        
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            if cpu_percent > 80:
                status = HealthStatus.DEGRADED
                warnings.append(f"High CPU usage: {cpu_percent}%")
            elif cpu_percent > 95:
                status = HealthStatus.UNHEALTHY
                warnings.append(f"Critical CPU usage: {cpu_percent}%")
            
            # Memory usage
            memory = psutil.virtual_memory()
            if memory.percent > 80:
                status = HealthStatus.DEGRADED
                warnings.append(f"High memory usage: {memory.percent}%")
            elif memory.percent > 95:
                status = HealthStatus.UNHEALTHY
                warnings.append(f"Critical memory usage: {memory.percent}%")
            
            # Disk usage
            disk = psutil.disk_usage('/')
            if disk.percent > 80:
                status = HealthStatus.DEGRADED
                warnings.append(f"High disk usage: {disk.percent}%")
            elif disk.percent > 95:
                status = HealthStatus.UNHEALTHY
                warnings.append(f"Critical disk usage: {disk.percent}%")
            
            response_data = {
                'service': 'system',
                'status': status,
                'timestamp': timezone.now().isoformat(),
                'response_time_ms': round((time.time() - start_time) * 1000, 2),
                'metrics': {
                    'cpu': {
                        'percent': cpu_percent,
                        'cores': psutil.cpu_count()
                    },
                    'memory': {
                        'percent': memory.percent,
                        'available_gb': round(memory.available / (1024**3), 2),
                        'total_gb': round(memory.total / (1024**3), 2)
                    },
                    'disk': {
                        'percent': disk.percent,
                        'free_gb': round(disk.free / (1024**3), 2),
                        'total_gb': round(disk.total / (1024**3), 2)
                    }
                }
            }
            
            if warnings:
                response_data['warnings'] = warnings
            
        except Exception as e:
            status = HealthStatus.UNHEALTHY
            response_data = {
                'service': 'system',
                'status': status,
                'timestamp': timezone.now().isoformat(),
                'response_time_ms': round((time.time() - start_time) * 1000, 2),
                'error': str(e)
            }
        
        status_code = 200 if status == HealthStatus.HEALTHY else 503 if status == HealthStatus.UNHEALTHY else 207
        
        return JsonResponse(response_data, status=status_code)


@method_decorator(never_cache, name='dispatch')
class StatusView(View):
    """Aggregated status endpoint"""
    
    def get(self, request):
        """Return aggregated status of all services"""
        start_time = time.time()
        
        # Check all services
        services = {
            'database': self._check_database(),
            'mqtt': self._check_mqtt(),
            'cache': self._check_cache(),
            'system': self._check_system()
        }
        
        # Determine overall status
        if any(s['status'] == HealthStatus.UNHEALTHY for s in services.values()):
            overall_status = HealthStatus.UNHEALTHY
        elif any(s['status'] == HealthStatus.DEGRADED for s in services.values()):
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY
        
        response_data = {
            'status': overall_status,
            'timestamp': timezone.now().isoformat(),
            'version': getattr(settings, 'VERSION', '1.0.0'),
            'environment': getattr(settings, 'ENVIRONMENT', 'development'),
            'services': services,
            'response_time_ms': round((time.time() - start_time) * 1000, 2)
        }
        
        # Add detailed mode if requested
        if request.GET.get('detailed') == 'true':
            response_data['details'] = {
                'django_version': __import__('django').VERSION,
                'python_version': __import__('sys').version,
                'debug_mode': settings.DEBUG,
                'time_zone': settings.TIME_ZONE,
                'language_code': settings.LANGUAGE_CODE
            }
        
        status_code = 200 if overall_status == HealthStatus.HEALTHY else 503 if overall_status == HealthStatus.UNHEALTHY else 207
        
        return JsonResponse(response_data, status=status_code)
    
    def _check_database(self):
        """Quick database check"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                return {'status': HealthStatus.HEALTHY}
        except:
            return {'status': HealthStatus.UNHEALTHY}
    
    def _check_mqtt(self):
        """Quick MQTT check"""
        try:
            from energy.models import MQTTBroker
            if MQTTBroker.objects.filter(is_active=True).exists():
                return {'status': HealthStatus.HEALTHY}
            return {'status': HealthStatus.DEGRADED}
        except:
            return {'status': HealthStatus.UNHEALTHY}
    
    def _check_cache(self):
        """Quick cache check"""
        try:
            cache.set('health_check', 'ok', 1)
            if cache.get('health_check') == 'ok':
                return {'status': HealthStatus.HEALTHY}
            return {'status': HealthStatus.DEGRADED}
        except:
            return {'status': HealthStatus.UNHEALTHY}
    
    def _check_system(self):
        """Quick system check"""
        try:
            cpu = psutil.cpu_percent(interval=0.1)
            mem = psutil.virtual_memory().percent
            
            if cpu > 95 or mem > 95:
                return {'status': HealthStatus.UNHEALTHY}
            elif cpu > 80 or mem > 80:
                return {'status': HealthStatus.DEGRADED}
            return {'status': HealthStatus.HEALTHY}
        except:
            return {'status': HealthStatus.UNHEALTHY}


class MetricsView(View):
    """Prometheus-compatible metrics endpoint"""
    
    def get(self, request):
        """Return metrics in Prometheus format"""
        metrics = []
        
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        metrics.append(f'# HELP system_cpu_usage_percent CPU usage percentage')
        metrics.append(f'# TYPE system_cpu_usage_percent gauge')
        metrics.append(f'system_cpu_usage_percent {cpu_percent}')
        
        metrics.append(f'# HELP system_memory_usage_percent Memory usage percentage')
        metrics.append(f'# TYPE system_memory_usage_percent gauge')
        metrics.append(f'system_memory_usage_percent {memory.percent}')
        
        metrics.append(f'# HELP system_disk_usage_percent Disk usage percentage')
        metrics.append(f'# TYPE system_disk_usage_percent gauge')
        metrics.append(f'system_disk_usage_percent {disk.percent}')
        
        # Application metrics
        try:
            from core.models import Plant, CERConfiguration
            from energy.models import DeviceConfiguration
            
            plant_count = Plant.objects.filter(is_active=True).count()
            cer_count = CERConfiguration.objects.filter(is_active=True).count()
            device_count = DeviceConfiguration.objects.filter(is_active=True).count()
            
            metrics.append(f'# HELP app_active_plants_total Number of active plants')
            metrics.append(f'# TYPE app_active_plants_total gauge')
            metrics.append(f'app_active_plants_total {plant_count}')
            
            metrics.append(f'# HELP app_active_cers_total Number of active CERs')
            metrics.append(f'# TYPE app_active_cers_total gauge')
            metrics.append(f'app_active_cers_total {cer_count}')
            
            metrics.append(f'# HELP app_active_devices_total Number of active devices')
            metrics.append(f'# TYPE app_active_devices_total gauge')
            metrics.append(f'app_active_devices_total {device_count}')
            
        except Exception as e:
            # Log error but don't fail the metrics endpoint
            pass
        
        return JsonResponse(
            '\n'.join(metrics),
            safe=False,
            content_type='text/plain; version=0.0.4'
        )
