# core/middleware.py

import logging
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.http import HttpResponseRedirect
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger('gaudi')
setup_logger = logging.getLogger(__name__)

User = get_user_model()

class GaudiLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if 'gaudi' in request.path.lower():
            # Log dettagli richiesta
            logger.info(
                f"Operazione Gaudì - "
                f"Timestamp: {timezone.now().isoformat()}, "
                f"User: {request.user}, "
                f"IP: {request.META.get('REMOTE_ADDR')}, "
                f"Method: {request.method}, "
                f"Path: {request.path}"
            )
            
            # Log contenuti richiesta per debug se necessario
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"POST Data: {request.POST}")
                logger.debug(f"Files: {request.FILES}")

        response = self.get_response(request)

        # Log risposta per operazioni Gaudì
        if 'gaudi' in request.path.lower():
            logger.info(
                f"Risposta Gaudì - "
                f"Status: {response.status_code}, "
                f"Path: {request.path}"
            )

        return response


class SuperUserSetupMiddleware:
    """
    Middleware che rileva se non esiste alcun superuser nel sistema
    e reindirizza alla pagina di setup iniziale per crearlo.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Skip durante i test
        if getattr(settings, 'TESTING', False):
            return self.get_response(request)
        
        # Skip per richieste AJAX e API
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return self.get_response(request)
        
        if request.path.startswith('/api/'):
            return self.get_response(request)
        
        # Skip per file statici e media
        if (request.path.startswith('/static/') or 
            request.path.startswith('/media/') or
            request.path.startswith('/favicon.ico')):
            return self.get_response(request)
        
        # Skip se siamo già nella pagina di setup
        try:
            setup_url = reverse('core:initial_setup')
            if request.path == setup_url:
                return self.get_response(request)
        except:
            # Se l'URL non esiste ancora, continua
            pass
        
        # Verifica se esistono superuser
        try:
            has_superuser = User.objects.filter(is_superuser=True, is_active=True).exists()
            
            if not has_superuser:
                setup_logger.info("Nessun superuser attivo trovato, reindirizzo al setup iniziale")
                try:
                    setup_url = reverse('core:initial_setup')
                    return HttpResponseRedirect(setup_url)
                except:
                    # Se l'URL non è ancora disponibile, continua senza reindirizzare
                    pass
                
        except Exception as e:
            # Se c'è un errore (es. database non ancora migrato), 
            # lascia passare la richiesta per non bloccare le migrazioni
            setup_logger.warning(f"Errore nel controllo superuser: {e}")
            pass
        
        return self.get_response(request)


class FirstInstallationMiddleware:
    """
    Middleware alternativo più leggero che controlla solo al primo accesso
    alla homepage se il sistema è configurato.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Skip durante i test
        if getattr(settings, 'TESTING', False):
            return self.get_response(request)
        
        # Controlla solo per la homepage
        if request.path in ['/', '', '/dashboard/']:
            try:
                # Verifica se esistono superuser attivi
                has_superuser = User.objects.filter(is_superuser=True, is_active=True).exists()
                
                if not has_superuser:
                    try:
                        setup_url = reverse('core:initial_setup')
                        setup_logger.info("Prima installazione rilevata, reindirizzo al setup")
                        return HttpResponseRedirect(setup_url)
                    except:
                        # Se l'URL non è disponibile, continua
                        pass
                    
            except Exception as e:
                # Ignora errori (es. durante le migrazioni)
                setup_logger.warning(f"Errore nel controllo prima installazione: {e}")
                pass
        
        return self.get_response(request)