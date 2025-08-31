#energy/views/mqtt_views.py
import logging

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods

from ..models import MQTTBroker, MQTTAuditLog, DeviceConfiguration
from ..mqtt.client import get_mqtt_client
from ..mqtt.core import get_mqtt_service
from django.http import JsonResponse
from django.utils import timezone

logger = logging.getLogger(__name__)

@login_required
def mqtt_settings(request):
    # Verifica che l'utente sia staff
    if not request.user.is_staff:
        messages.error(request, 'Accesso non autorizzato')
        return redirect('energy:dashboard')
        
    if request.method == 'POST':
        try:
            broker = MQTTBroker.objects.get_or_create(id=request.POST.get('id'))[0]
            
            # Aggiorna i campi del broker
            broker.name = request.POST.get('name')
            broker.host = request.POST.get('host')
            broker.port = int(request.POST.get('port', 1883))
            broker.username = request.POST.get('username')
            
            # Aggiorna password solo se fornita
            if request.POST.get('password'):
                broker.password = request.POST.get('password')
                
            broker.use_tls = request.POST.get('use_tls') == 'on'
            broker.verify_cert = request.POST.get('verify_cert') == 'on'
            
            # Gestione certificato CA
            if request.FILES.get('ca_cert'):
                broker.ca_cert = request.FILES['ca_cert']
                
            broker.is_active = True
            broker.save()
            
            messages.success(request, 'Configurazione MQTT salvata con successo')
            
            # Riavvia il client MQTT con la nuova configurazione
            client = get_mqtt_client()
            if client.is_connected:
                client.stop()
            client.configure(
                host=broker.host,
                port=broker.port,
                username=broker.username,
                password=broker.password,
                use_tls=broker.use_tls
            )
            client.start()
            
        except Exception as e:
            error_msg = f'Errore nel salvataggio della configurazione: {str(e)}'
            messages.error(request, error_msg)
            logger.error(f'Errore configurazione MQTT: {str(e)}')
            
        return redirect('energy:mqtt_settings')
    
    # Recupera i log e calcola le statistiche
    recent_logs = MQTTAuditLog.objects.all().order_by('-timestamp')[:5]
    
    # Mappa le operazioni ai livelli di log appropriati
    operation_levels = {
        'CONNECT': 'success',
        'DISCONNECT': 'warning',
        'MESSAGE': 'info',
        'PUBLISH': 'info',
        'SUBSCRIBE': 'info',
        'ERROR': 'error'
    }
    
    # Arricchisci i log con livello e messaggio
    for log in recent_logs:
        # Imposta il livello in base all'operazione e allo status
        log.level = operation_levels.get(log.operation, 'info')
        if not log.status:
            log.level = 'error'
            
        # Genera un messaggio descrittivo
        if log.operation == 'CONNECT':
            log.message = 'Connessione al broker MQTT ' + ('riuscita' if log.status else 'fallita')
        elif log.operation == 'DISCONNECT':
            log.message = 'Disconnesso dal broker MQTT'
        elif log.operation == 'MESSAGE':
            log.message = f'Messaggio ricevuto sul topic {log.topic or "N/A"}'
        elif log.operation == 'PUBLISH':
            log.message = f'Messaggio pubblicato sul topic {log.topic or "N/A"}'
        elif log.operation == 'SUBSCRIBE':
            log.message = f'Sottoscrizione al topic {log.topic or "N/A"}'
        else:
            log.message = log.details.get('message', 'Nessun dettaglio disponibile') if log.details else 'Nessun dettaglio disponibile'

    client = get_mqtt_client()
    mqtt_status = "Connesso" if client.is_connected else "Disconnesso"
    logger.info(f"Stato connessione MQTT: {mqtt_status}")

    context = {
        'mqtt_config': MQTTBroker.objects.filter(is_active=True).first(),
        'system_logs': recent_logs,
        'stats': {
            'total_connections': MQTTAuditLog.objects.filter(operation='CONNECT', status=True).count(),
            'failed_connections': MQTTAuditLog.objects.filter(operation='CONNECT', status=False).count(),
            'total_messages': MQTTAuditLog.objects.filter(operation='MESSAGE').count()
        },
        'is_connected': client.is_connected,
        'mqtt_status': mqtt_status
    }
    
    return render(request, 'energy/settings/main.html', context)


@login_required
@require_http_methods(["POST"])
def save_mqtt_settings(request):
    try:
        broker = MQTTBroker.objects.get(id=request.POST.get('id')) if request.POST.get('id') else MQTTBroker()
        
        broker.name = request.POST.get('name')
        broker.host = request.POST.get('host')
        broker.port = int(request.POST.get('port', 1883))
        broker.username = request.POST.get('username')
        
        if request.POST.get('password'):
            broker.password = request.POST.get('password')
            
        broker.use_tls = request.POST.get('use_tls') == 'on'
        broker.verify_cert = request.POST.get('verify_cert') == 'on'
        
        if request.FILES.get('ca_cert'):
            broker.ca_cert = request.FILES['ca_cert']
            
        broker.is_active = True
        broker.save()
        
        messages.success(request, 'Configurazione MQTT salvata con successo')
    except Exception as e:
        messages.error(request, f'Errore nel salvataggio della configurazione: {str(e)}')
        
    return redirect('energy:mqtt_settings')

@login_required
def mqtt_control(request):
    if not request.user.is_staff:
        messages.error(request, 'Accesso non autorizzato')
        return redirect('energy:dashboard')
        
    if request.method == 'POST':
        action = request.POST.get('action')
        client = get_mqtt_client()
        
        try:
            if action == 'connect':
                success = client.connect()
                if success:
                    messages.success(request, 'Connessione MQTT avviata')
                else:
                    messages.error(request, 'Errore connessione MQTT')
            elif action == 'disconnect':
                client.disconnect()
                messages.success(request, 'Connessione MQTT terminata')
            else:
                messages.warning(request, 'Azione non valida')
        except Exception as e:
            logger.error(f'Errore durante {action}: {str(e)}')
            messages.error(request, f'Errore durante l\'operazione: {str(e)}')
    
    return redirect('energy:mqtt_settings')


@login_required
def mqtt_status_overview(request):
    """API overview per stato MQTT richiesto da static/js/mqtt-status.js"""
    try:
        client = get_mqtt_client()
        svc = get_mqtt_service()
        is_connected = bool(getattr(client, 'is_connected', False) or getattr(svc, 'is_connected', False))
        now = timezone.now()
        five_minutes_ago = now - timezone.timedelta(minutes=5)
        connected_devices = DeviceConfiguration.objects.filter(
            is_active=True,
            last_seen__gte=five_minutes_ago
        ).count()

        data = {
            'connection': 'connected' if is_connected else 'disconnected',
            'messages_processed': int(getattr(client, '_message_count', 0) or getattr(svc, 'messages_received', 0)),
            'connected_devices': connected_devices,
            'last_error': getattr(svc, 'last_error', None),
            'performance': {
                'message_rate': 0.0,
                'average_processing_time': 0.0,
            }
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({
            'connection': 'error',
            'messages_processed': 0,
            'connected_devices': 0,
            'last_error': str(e),
            'performance': {
                'message_rate': 0.0,
                'average_processing_time': 0.0,
            }
        }, status=500)
