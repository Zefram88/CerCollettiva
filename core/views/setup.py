# core/views/setup.py

import logging
from django.shortcuts import render, redirect
from django.views.generic import FormView
from django.contrib.auth import get_user_model, login
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import Http404
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from ..forms import InitialSuperUserForm

logger = logging.getLogger(__name__)
User = get_user_model()


@method_decorator([csrf_protect, never_cache], name='dispatch')
class InitialSetupView(FormView):
    """
    Vista per il setup iniziale del sistema.
    Permette di creare il primo superuser quando non ce ne sono.
    """
    template_name = 'core/setup/initial_setup.html'
    form_class = InitialSuperUserForm
    success_url = reverse_lazy('core:dashboard')
    
    def dispatch(self, request, *args, **kwargs):
        # Skip durante i test
        if getattr(settings, 'TESTING', False):
            return super().dispatch(request, *args, **kwargs)
        
        # Verifica se ci sono già superuser attivi
        has_superuser = User.objects.filter(is_superuser=True, is_active=True).exists()
        
        if has_superuser:
            logger.warning(f"Tentativo di accesso al setup con superuser già esistente da IP {request.META.get('REMOTE_ADDR')}")
            messages.info(request, "Il sistema è già configurato.")
            return redirect('core:dashboard')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Setup Iniziale CerCollettiva',
            'show_navbar': False,  # Nasconde la navbar durante il setup
            'is_setup': True,
        })
        return context
    
    def form_valid(self, form):
        """
        Salva il superuser e fa login automaticamente
        """
        try:
            # Salva l'utente (e la CER se richiesta)
            user = form.save()
            
            # Log del setup completato
            logger.info(f"Setup iniziale completato. Superuser creato: {user.username}")
            
            # Login automatico
            login(self.request, user)
            
            # Messaggio di successo
            messages.success(
                self.request,
                f"Benvenuto {user.first_name}! Il sistema è stato configurato con successo."
            )
            
            # Log dettagli CER se creata
            if form.cleaned_data.get('create_demo_cer'):
                cer_name = form.cleaned_data.get('cer_name')
                logger.info(f"CER demo creata: {cer_name}")
                messages.info(
                    self.request,
                    f"CER '{cer_name}' creata e configurata per l'utilizzo."
                )
            
            return super().form_valid(form)
            
        except Exception as e:
            logger.error(f"Errore durante il setup iniziale: {str(e)}")
            messages.error(
                self.request,
                "Errore durante la configurazione. Riprova o contatta l'assistenza."
            )
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        """
        Gestisce errori di validazione del form
        """
        logger.warning(f"Errori di validazione nel setup: {form.errors}")
        messages.error(
            self.request,
            "Errori nella configurazione. Controlla i campi evidenziati."
        )
        return super().form_invalid(form)


def setup_complete_view(request):
    """
    Vista mostrata dopo il completamento del setup
    """
    # Verifica che ci sia effettivamente un superuser
    if not User.objects.filter(is_superuser=True, is_active=True).exists():
        return redirect('core:initial_setup')
    
    context = {
        'title': 'Setup Completato',
        'user': request.user,
    }
    
    return render(request, 'core/setup/setup_complete.html', context)


def setup_check_view(request):
    """
    Vista per verificare lo stato del setup (utile per debugging)
    """
    # Solo in DEBUG mode
    if not settings.DEBUG:
        raise Http404("Pagina non disponibile")
    
    context = {
        'superuser_count': User.objects.filter(is_superuser=True).count(),
        'active_superuser_count': User.objects.filter(is_superuser=True, is_active=True).count(),
        'total_users': User.objects.count(),
        'setup_required': not User.objects.filter(is_superuser=True, is_active=True).exists(),
    }
    
    return render(request, 'core/setup/setup_check.html', context)