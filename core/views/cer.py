# core/views/cer.py
import logging
from django.views.generic import ListView, DetailView, CreateView, FormView
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db.models import Sum, Count, Q
from django.utils import timezone

from .base import BaseCERView
from ..models import CERConfiguration, CERMembership, Plant, PlantMeasurement
from ..forms import CERConfigurationForm, CERMembershipForm
from .mixins.gdpr import GDPRConsentRequiredMixin

logger = logging.getLogger(__name__)

class CERListView(LoginRequiredMixin, ListView):
    """Lista delle CER"""
    model = CERConfiguration
    template_name = 'core/cer_list.html'
    context_object_name = 'available_cers'
    
    def get_queryset(self):
        # Query base semplice
        queryset = CERConfiguration.objects.filter(is_active=True)
        #print(f"1. CER attive trovate: {queryset.count()}")
        
        # Aggiunge il conteggio dei membri
        queryset = queryset.annotate(
            members_count=Count('members', distinct=True)
        )
        #print(f"2. Query finale: {queryset.query}")
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Info per il bottone "Aderisci"
        context['user_memberships'] = user.cer_memberships.filter(
            is_active=True
        ).select_related('cer_configuration')
        
        # Debug info
        context.update({
            'debug': {
                'total_cers': CERConfiguration.objects.count(),
                'active_cers': CERConfiguration.objects.filter(is_active=True).count(),
                'username': user.username,
                'is_staff': user.is_staff,
                'user_memberships_count': user.cer_memberships.filter(
                    is_active=True
                ).count()
            }
        })
        
        return context
class CERPublicDetailView(LoginRequiredMixin, DetailView):
    """Vista pubblica della CER per utenti non membri"""
    model = CERConfiguration
    template_name = 'core/cer_public_detail.html'
    context_object_name = 'cer'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cer = self.object
        
        # Check if user is already a member
        is_member = CERMembership.objects.filter(
            user=self.request.user,
            cer_configuration=cer,
            is_active=True
        ).exists()
        
        # Get distribution configuration
        distribution_config = None
        try:
            distribution_config = cer.distribution_config
        except:
            pass
        
        context.update({
            'is_member': is_member,
            'distribution_config': distribution_config,
            'members_count': cer.memberships.filter(is_active=True).count(),
            'plants_count': cer.plants.filter(is_active=True).count(),
        })
        
        return context

class CERDetailView(BaseCERView):
    """Dettaglio completo della CER per membri"""
    template_name = 'core/cer_detail.html'
    context_object_name = 'cer'
    
    def dispatch(self, request, *args, **kwargs):
        """Check if user is member, otherwise redirect to public view"""
        cer = get_object_or_404(CERConfiguration, pk=kwargs['pk'])
        
        if not request.user.is_staff:
            is_member = CERMembership.objects.filter(
                user=request.user,
                cer_configuration=cer,
                is_active=True
            ).exists()
            
            if not is_member:
                # Redirect to public view
                from django.urls import reverse
                return redirect(reverse('core:cer_public_detail', kwargs={'pk': cer.pk}))
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_object(self):
        """Recupera l'oggetto CER"""
        return get_object_or_404(
            CERConfiguration,
            pk=self.kwargs['pk']
        )

    def get_context_data(self, **kwargs):
        # Ensure object is set before calling super()
        if 'object' not in kwargs:
            kwargs['object'] = self.get_object()
        
        context = super().get_context_data(**kwargs)
        cer = self.get_object()
        
        # Recupera membership dell'utente
        user_membership = None
        if not self.request.user.is_staff:
            try:
                user_membership = CERMembership.objects.get(
                    user=self.request.user,
                    cer_configuration=cer,
                    is_active=True
                )
            except CERMembership.DoesNotExist:
                # User doesn't have membership - could redirect or show limited view
                user_membership = None
        
        # Calcola statistiche energetiche
        time_threshold = self.get_time_threshold()
        energy_stats = self._calculate_cer_energy_stats(cer, time_threshold)
        
        context.update({
            'cer': cer,  # Explicitly add cer to context
            'object': cer,  # Ensure object is also set
            'membership': user_membership,  # Change key name to match template
            'energy_stats': energy_stats,
            'members': cer.memberships.filter(is_active=True).select_related('user'),
            'plants': self._get_filtered_plants(cer),
            'is_admin': self.request.user.is_staff or 
                       (user_membership and user_membership.role == 'ADMIN')
        })
        
        return context
        
    def _calculate_cer_energy_stats(self, cer, time_threshold):
        """Calcola le statistiche energetiche della CER"""
        try:
            # Usa PlantMeasurement con il campo corretto 'value'
            measurements = PlantMeasurement.objects.select_related(
                'plant'
            ).filter(
                plant__cer_configuration=cer,
                timestamp__gte=time_threshold
            )
            
            # Calcola totale produzione
            producer_total = measurements.filter(
                plant__plant_type='PRODUCER'
            ).aggregate(
                total=Sum('value')  # Usa 'value' invece di 'power'
            )['total'] or 0
            
            # Calcola totale consumo
            consumer_total = measurements.filter(
                plant__plant_type='CONSUMER'
            ).aggregate(
                total=Sum('value')  # Usa 'value' invece di 'power'
            )['total'] or 0
            
            # Ritorna le statistiche complete
            return {
                'total_production': producer_total,
                'total_consumption': abs(consumer_total),
                'net_energy': producer_total - abs(consumer_total),
                'measurement_period': {
                    'start': time_threshold,
                    'end': timezone.now()
                }
            }
            
        except Exception as e:
            logger.error(f"Errore nel calcolo delle statistiche energetiche: {str(e)}")
            return {
                'total_production': 0,
                'total_consumption': 0,
                'net_energy': 0,
                'measurement_period': {
                    'start': time_threshold,
                    'end': timezone.now()
                }
            }
    
    def _get_filtered_plants(self, cer):
        """Recupera gli impianti filtrati in base ai permessi"""
        plants = cer.plants.filter(is_active=True)
        if not self.request.user.is_staff:
            plants = plants.filter(owner=self.request.user)
        return plants.select_related('owner')

class CERJoinView(BaseCERView, GDPRConsentRequiredMixin):
    """Vista per l'adesione a una CER"""
    template_name = 'core/cer_join.html'
    form_class = CERMembershipForm
    
    def get_object(self):
        return get_object_or_404(
            CERConfiguration,
            pk=self.kwargs['pk'],
            is_active=True
        )
    
    def dispatch(self, request, *args, **kwargs):
        # Verifica autenticazione prima
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
            
        cer = self.get_object()
        
        # Verifica se l'utente è già membro
        if CERMembership.objects.filter(
            user=request.user,
            cer_configuration=cer
        ).exists():
            messages.warning(request, _("Sei già membro di questa CER"))
            return redirect('core:cer_detail', pk=cer.pk)
            
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cer = self.get_object()
        
        # Add member and plant counts for the sidebar
        members_count = CERMembership.objects.filter(
            cer_configuration=cer, is_active=True
        ).count()
        plants_count = Plant.objects.filter(
            cer_configuration=cer, is_active=True
        ).count()
        
        context.update({
            'cer': cer,
            'object': cer,
            'members_count': members_count,
            'plants_count': plants_count
        })
        
        return context
    
    def get(self, request, *args, **kwargs):
        """Handle GET request - display the form"""
        form = self.form_class()
        context = self.get_context_data(form=form)
        return self.render_to_response(context)
    
    def post(self, request, *args, **kwargs):
        """Handle POST request - process the form"""
        form = self.form_class(request.POST, request.FILES)
        if form.is_valid():
            return self.form_valid(form)
        else:
            context = self.get_context_data(form=form)
            return self.render_to_response(context)
    
    def form_valid(self, form):
        membership = form.save(commit=False)
        membership.user = self.request.user
        membership.cer_configuration = self.get_object()
        membership.save()
        
        # Gestione differenziata per tipologia membro
        if membership.member_type == 'CONSUMER':
            # Auto-approvazione per consumatori
            membership.auto_approve_consumer()
            # Crea tessera e registrazione automaticamente
            card, registry = membership.complete_membership_setup()
            messages.success(
                self.request, 
                _(f"Adesione completata! Tessera n. {card.card_number} generata automaticamente.")
            )
        else:
            # Per produttori/prosumer: workflow normale con approvazione manuale
            messages.success(
                self.request, 
                _("Richiesta di adesione inviata. I documenti verranno verificati dall'amministrazione.")
            )
        
        return redirect('core:cer_detail', pk=self.get_object().pk)

class MembershipCardView(LoginRequiredMixin, DetailView):
    """Vista per visualizzare la tessera del membro"""
    template_name = 'core/membership_card.html'
    context_object_name = 'card'
    
    def get_object(self):
        membership = get_object_or_404(
            CERMembership,
            user=self.request.user,
            cer_configuration_id=self.kwargs['cer_pk'],
            is_active=True
        )
        
        # Se non ha tessera, la crea
        if not hasattr(membership, 'card'):
            card, _ = membership.complete_membership_setup()
            return card
        
        return membership.card
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        card = self.get_object()
        
        context.update({
            'membership': card.membership,
            'cer': card.membership.cer_configuration,
            'registry_entry': getattr(card.membership, 'registry_entry', None)
        })
        return context

class MemberRegistryView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Vista per il registro soci (solo admin)"""
    template_name = 'core/member_registry.html'
    context_object_name = 'registry_entries'
    paginate_by = 20
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get_queryset(self):
        cer = get_object_or_404(CERConfiguration, pk=self.kwargs['cer_pk'])
        
        queryset = cer.member_registry.select_related(
            'membership__user', 
            'membership__cer_configuration'
        ).prefetch_related('membership__card')
        
        # Filtri
        member_type = self.request.GET.get('member_type')
        if member_type:
            queryset = queryset.filter(membership__member_type=member_type)
        
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(membership__user__username__icontains=search) |
                Q(membership__user__fiscal_code__icontains=search) |
                Q(membership__user__legal_name__icontains=search)
            )
        
        return queryset.order_by('progressive_number')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cer = get_object_or_404(CERConfiguration, pk=self.kwargs['cer_pk'])
        
        context.update({
            'cer': cer,
            'total_members': cer.member_registry.count(),
            'member_types': [
                ('CONSUMER', 'Solo Consumatori'),
                ('PRODUCER', 'Produttori'),
                ('PROSUMER', 'Prosumer')
            ],
            'current_filter': self.request.GET.get('member_type', ''),
            'search_query': self.request.GET.get('search', '')
        })
        
        # Statistiche per tipo
        stats = {}
        for member_type, _ in context['member_types']:
            stats[member_type] = cer.member_registry.filter(
                membership__member_type=member_type
            ).count()
        context['stats'] = stats
        
        return context