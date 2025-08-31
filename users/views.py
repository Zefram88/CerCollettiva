# Core Django imports
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import PasswordChangeView
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.db.models import Q
from django.views.generic import UpdateView, TemplateView, ListView, DetailView
# Local imports
from .forms import (
    UserRegistrationForm, 
    UserLoginForm, 
    UserUpdateForm,
    BusinessProfileForm, 
    PrivateProfileForm, 
    UserProfileForm
)
from .models import CustomUser

# Logging
import logging
logger = logging.getLogger('access_logger')


def register(request):
    """Vista per la registrazione di nuovi utenti"""
    if request.method == 'POST':
        print("=== DEBUG REGISTRAZIONE ===")
        print(f"Dati POST ricevuti: {list(request.POST.keys())}")
        print(f"Password1 presente: {'password1' in request.POST}")
        print(f"Password2 presente: {'password2' in request.POST}")
        if 'password1' in request.POST and 'password2' in request.POST:
            print(f"Password1 length: {len(request.POST['password1'])}")
            print(f"Password2 length: {len(request.POST['password2'])}")
            print(f"Passwords match: {request.POST['password1'] == request.POST['password2']}")
        
        form = UserRegistrationForm(request.POST)
        print(f"Form is valid: {form.is_valid()}")
        
        if not form.is_valid():
            print("Form errors:", form.errors)
            for field, errors in form.errors.items():
                print(f"  {field}: {errors}")
        
        if form.is_valid():
            # Verifica che la privacy policy sia stata accettata
            if form.cleaned_data.get('privacy_policy', False):
                user = form.save(commit=False)
                user.set_password(form.cleaned_data['password1'])
                # Imposta esplicitamente i campi relativi alla privacy
                user.privacy_accepted = True  # Aggiungi questa riga
                user.privacy_acceptance_date = timezone.now()
                user.save()
                messages.success(request, 'Registrazione completata. Puoi ora effettuare il login.')
                return redirect('users:login')
            else:
                messages.error(request, 'Devi accettare la privacy policy per registrarti.')
        else:
            messages.error(request, 'Ci sono errori nel form. Controlla i campi evidenziati.')
    else:
        form = UserRegistrationForm()
        
    context = {
        'form': form,
        'form_errors': form.errors if hasattr(form, 'errors') else None
    }
    return render(request, 'users/register.html', context)

def login_view(request):
    """Vista per il login degli utenti"""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('core:home')  # o qualsiasi altra pagina dopo il login
        else:
            # Non aggiungere messaggi qui, lascia che sia il form a gestire gli errori
            # Rimuovi qualsiasi chiamata a messages.error o messages.add_message
            pass
    else:
        form = AuthenticationForm()
    
    return render(request, 'users/login.html', {'form': form})

@login_required
def logout_view(request):
    if request.method == 'POST':
        username = request.user.username
        ip = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT')
        
        logout(request)
        
        logger.info(
            f"Logout effettuato - Utente: {username} - "
            f"IP: {ip} - User Agent: {user_agent}"
        )
        
        return redirect('users:login')  # Usa il namespace completo
    
    return redirect('core:home')

class ProfileView(LoginRequiredMixin, View):
    """Vista per la gestione del profilo utente"""
    model = CustomUser
    template_name = 'users/profile.html'
    success_url = reverse_lazy('users:profile')

    def get(self, request):
        # Preparazione dei form
        user_form = UserUpdateForm(instance=request.user)
        business_form = BusinessProfileForm(instance=request.user) if request.user.legal_type == 'BUSINESS' else None
        
        # Context base
        context = {
            'user_form': user_form,
            'business_form': business_form,
        }
        
        # Statistiche utente
        context.update({
            'total_logins': request.user.logins.count() if hasattr(request.user, 'logins') else 0,
            'total_documents': request.user.documents.count() if hasattr(request.user, 'documents') else 0,
            'total_plants': request.user.plants.count() if hasattr(request.user, 'plants') else 0,
        })
        
        # Informazioni GDPR
        context.update({
            'privacy_status': {
                'accepted': getattr(request.user, 'privacy_accepted', False),
                'acceptance_date': getattr(request.user, 'privacy_acceptance_date', None),
                'last_update': getattr(request.user, 'last_privacy_update', None),
            }
        })

        # Dati aziendali se necessario
        if request.user.is_business:
            context.update({
                'business_info': {
                    'legal_name': getattr(request.user, 'legal_name', ''),
                    'vat_number': getattr(request.user, 'vat_number', ''),
                    'pec': getattr(request.user, 'pec', ''),
                    'sdi_code': getattr(request.user, 'sdi_code', ''),
                }
            })
            
            # Documenti aziendali
            if hasattr(request.user, 'documents'):
                context['business_documents'] = request.user.documents.all().order_by('-upload_date')
        
        # Attività recenti
        context['recent_activity'] = {
            'last_login': request.user.last_login,
            'date_joined': request.user.date_joined,
            'profile_updates': getattr(request.user, 'profile_updates', 0),
        }
        
        return render(request, self.template_name, context)

    def post(self, request):
        user_form = UserUpdateForm(request.POST, instance=request.user)
        business_form = None
        
        if request.user.legal_type == 'BUSINESS':
            business_form = BusinessProfileForm(request.POST, instance=request.user)
            if user_form.is_valid() and business_form.is_valid():
                user_form.save()
                business_form.save()
                messages.success(request, 'Profilo aziendale aggiornato con successo.')
                return redirect('users:profile')
        else:
            if user_form.is_valid():
                user_form.save()
                messages.success(request, 'Profilo personale aggiornato con successo.')
                return redirect('users:profile')

        context = {
            'user_form': user_form,
            'business_form': business_form,
            'privacy_status': {
                'accepted': getattr(request.user, 'privacy_accepted', False),
                'acceptance_date': getattr(request.user, 'privacy_acceptance_date', None),
                'last_update': getattr(request.user, 'last_privacy_update', None),
            },
        }
        
        messages.error(request, 'Si prega di correggere gli errori nel form.')
        return render(request, self.template_name, context)

class PrivacyPolicyView(TemplateView):
    """Vista per visualizzare la privacy policy"""
    template_name = 'users/privacy_policy.html'

class CustomPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    """Vista per il cambio password"""
    template_name = 'users/password_change.html'
    success_url = reverse_lazy('users:profile')

    def form_valid(self, form):
        messages.success(self.request, 'Password modificata con successo.')
        return super().form_valid(form)

class DeleteAccountView(LoginRequiredMixin, View):
    """Vista per l'eliminazione dell'account"""
    template_name = 'users/delete_account.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        # Log dell'eliminazione account per GDPR
        user_id = request.user.id
        request.user.delete()
        messages.success(request, 'Account eliminato con successo.')
        # Qui potresti aggiungere la logica per conservare i dati necessari per GDPR
        return redirect('home')

class UserManagementView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = CustomUser
    template_name = 'users/gestione_utenti.html'
    context_object_name = 'users'
    paginate_by = 10
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(fiscal_code__icontains=search) |
                Q(legal_name__icontains=search)
            )
        return queryset.order_by('-date_joined')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['show_sensitive'] = self.request.GET.get('show_sensitive', False)
        context['search'] = self.request.GET.get('search', '')
        context['legal_type_labels'] = dict(CustomUser.LEGAL_TYPES)
        return context
    
class AdminUserProfileView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = CustomUser
    template_name = 'users/admin_profile.html'
    form_class = UserProfileForm
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get_success_url(self):
        return reverse_lazy('users:management')
        
    def form_valid(self, form):
        messages.success(self.request, 'Profilo utente aggiornato con successo')
        return super().form_valid(form)
    
class UserDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
   model = CustomUser
   template_name = 'users/user_detail.html'
   context_object_name = 'profile_user'

   def test_func(self):
       return self.request.user.is_staff

   def get_context_data(self, **kwargs):
       context = super().get_context_data(**kwargs)
       context['plants'] = self.object.plants.all()
       return context