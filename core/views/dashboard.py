# core/views/dashboard.py

from django.views.generic import TemplateView
from django.db.models import Sum, Count
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .base import CerBaseView
from .mixins.auth import StaffRequiredMixin
from ..models import (
    Plant, 
    CERConfiguration, 
    CERMembership,
    Alert
)

from energy.models import DeviceMeasurement

class HomeView(TemplateView):
    """Vista homepage pubblica"""
    template_name = 'core/home.html'

class DashboardView(CerBaseView):
    """Dashboard principale dell'applicazione"""
    template_name = 'core/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Determina se l'utente è staff o super admin
        is_global_admin = user.is_staff or user.is_superuser
        
        # Gestione onboarding status per utenti non admin
        onboarding_context = self._get_onboarding_context(user, is_global_admin)
        context.update(onboarding_context)
        
        # Recupera gli impianti in base al ruolo
        if is_global_admin:
            # Per admin globali: tutti gli impianti
            plants = Plant.objects.filter(
                is_active=True
            ).select_related('cer_configuration', 'owner').prefetch_related(
                'devices__measurements'
            )
        else:
            # Per admin CER: impianti delle CER amministrate + propri impianti
            administered_cer_ids = user.cer_memberships.filter(
                role='ADMIN',
                is_active=True
            ).values_list('cer_configuration_id', flat=True)
            
            plants = Plant.objects.filter(
                is_active=True
            ).filter(
                # Impianti delle CER amministrate OR impianti personali
                Q(cer_configuration_id__in=administered_cer_ids) |
                Q(owner=user)
            ).distinct().select_related('cer_configuration', 'owner').prefetch_related(
                'devices__measurements'
            )

        # Recupera le membership CER
        user_memberships = CERMembership.objects.filter(
            user=user,
            is_active=True
        ).select_related('cer_configuration')

        # Calcola statistiche avanzate per admin
        if is_global_admin or administered_cer_ids.exists():
            plants_stats = {
                'total': plants.count(),
                'active': plants.filter(is_active=True).count(),
                'with_cer': plants.exclude(cer_configuration=None).count(),
                'by_type': plants.values('plant_type').annotate(
                    count=Count('id')
                ),
                'total_power': plants.aggregate(
                    total=Sum('nominal_power')
                )['total'] or 0
            }
        else:
            plants_stats = self.get_basic_plants_stats(plants)

        # Calcolo statistiche energetiche
        time_threshold = self.get_time_threshold()
        energy_stats = self._calculate_energy_stats(plants, time_threshold)
        
        # Recupera gli alert con filtro basato sul ruolo
        active_alerts = self.get_filtered_alerts(user, is_global_admin)

        context.update({
            'plants': plants,
            'memberships': user_memberships,
            'energy_stats': energy_stats,
            'active_alerts': active_alerts,
            'plants_stats': plants_stats,
            'is_global_admin': is_global_admin,
            'cer_stats': {
                'total_memberships': user_memberships.count(),
                'active_memberships': user_memberships.filter(is_active=True).count()
            }
        })
        
        return context

    def _get_onboarding_context(self, user, is_global_admin):
        """Gestisce il contesto di onboarding per la dashboard"""
        from users.models import CustomUser
        
        # Admin e staff vedono sempre la dashboard completa
        if is_global_admin:
            return {
                'show_onboarding_cta': False,
                'onboarding_status': None,
                'onboarding_message': None,
                'onboarding_action_url': None,
                'onboarding_action_text': None
            }
        
        # Per utenti normali, gestisci lo stato di onboarding
        onboarding_status = getattr(user, 'onboarding_status', CustomUser.OnboardingStatus.REGISTRATO)
        
        if onboarding_status == CustomUser.OnboardingStatus.REGISTRATO:
            return {
                'show_onboarding_cta': True,
                'onboarding_status': onboarding_status,
                'onboarding_message': 'Completa il tuo profilo anagrafico per procedere con l\'adesione alla CER',
                'onboarding_action_url': 'users:profile_complete',
                'onboarding_action_text': 'Completa Profilo',
                'onboarding_icon': 'fas fa-user-edit',
                'onboarding_class': 'warning'
            }
        elif onboarding_status == CustomUser.OnboardingStatus.ANAGRAFICA_COMPLETA:
            return {
                'show_onboarding_cta': True,
                'onboarding_status': onboarding_status,
                'onboarding_message': 'Configura la tua partecipazione alla Comunità Energetica Rinnovabile',
                'onboarding_action_url': 'cer:onboarding_wizard',  # Da implementare
                'onboarding_action_text': 'Configura CER',
                'onboarding_icon': 'fas fa-cogs',
                'onboarding_class': 'info'
            }
        elif onboarding_status == CustomUser.OnboardingStatus.ONBOARDING_COMPLETATO:
            return {
                'show_onboarding_cta': False,
                'onboarding_status': onboarding_status,
                'onboarding_message': None,
                'onboarding_action_url': None,
                'onboarding_action_text': None
            }
        else:
            # Fallback per stati non definiti
            return {
                'show_onboarding_cta': True,
                'onboarding_status': onboarding_status,
                'onboarding_message': 'Completa la configurazione del tuo account',
                'onboarding_action_url': 'users:profile_complete',
                'onboarding_action_text': 'Completa Configurazione',
                'onboarding_icon': 'fas fa-exclamation-triangle',
                'onboarding_class': 'secondary'
            }

    def get_filtered_alerts(self, user, is_global_admin):
        """Recupera gli alert filtrati in base al ruolo dell'utente"""
        alerts_query = Alert.objects.filter(is_read=False)
        
        if is_global_admin:
            # Gli admin globali vedono tutti gli alert
            return alerts_query.order_by('-created_at')[:10]
        
        # Gli altri utenti vedono solo gli alert relativi ai propri impianti
        # o alle CER di cui sono membri
        #return alerts_query.filter(
        #    Q(plant__owner=user) |
        #    Q(plant__cer_configuration__members=user)
        #).distinct().order_by('-created_at')[:5]
    
        # Per ora, gli utenti non admin vedono solo gli ultimi 5 alert attivi
        return alerts_query.order_by('-created_at')[:5]

    def get_basic_plants_stats(self, plants):
        """
        Calcola le statistiche di base per utenti non amministratori
        """
        return {
            'total': plants.count(),
            'active': plants.filter(is_active=True).count(),
            'with_cer': plants.exclude(cer_configuration=None).count(),
            'by_type': plants.values('plant_type').annotate(
                count=Count('id')
            ),
            'total_power': plants.aggregate(
                total=Sum('nominal_power')
            )['total'] or 0
        }

    def _calculate_energy_stats(self, plants, time_threshold):
        """
        Calcola le statistiche energetiche per gli impianti selezionati
        Ottimizzato per evitare N+1 queries
        """
        stats = {
            'total_power': 0,
            'today_energy': 0,
            'month_energy': 0,
            'year_energy': 0
        }
        
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = today_start.replace(day=1)
        year_start = month_start.replace(month=1)
        
        # Ottimizzazione: usa una singola query per tutte le misurazioni
        plant_ids = [plant.id for plant in plants]
        
        # Calcola potenza attuale (ultime misurazioni)
        recent_power = DeviceMeasurement.objects.filter(
            plant_id__in=plant_ids,
            timestamp__gte=time_threshold
        ).aggregate(total=Sum('power'))['total'] or 0
        
        # Energia giornaliera
        today_energy = DeviceMeasurement.objects.filter(
            plant_id__in=plant_ids,
            timestamp__gte=today_start
        ).aggregate(total=Sum('energy_total'))['total'] or 0
        
        # Energia mensile
        month_energy = DeviceMeasurement.objects.filter(
            plant_id__in=plant_ids,
            timestamp__gte=month_start
        ).aggregate(total=Sum('energy_total'))['total'] or 0
        
        # Energia annuale
        year_energy = DeviceMeasurement.objects.filter(
            plant_id__in=plant_ids,
            timestamp__gte=year_start
        ).aggregate(total=Sum('energy_total'))['total'] or 0
        
        # Converti potenza in kW
        stats['total_power'] = round(recent_power / 1000.0, 2)
        
        # Arrotonda i valori di energia
        stats['today_energy'] = round(today_energy, 2)
        stats['month_energy'] = round(month_energy, 2)
        stats['year_energy'] = round(year_energy, 2)
        
        return stats

    def get_total_power(self, user):
            """Calcola la potenza totale degli impianti"""
            if hasattr(user, 'cer_memberships'):
                # Verifica se l'utente è amministratore di qualche CER
                is_cer_admin = user.cer_memberships.filter(
                    role='ADMIN',
                    is_active=True
                ).exists()
                
                if is_cer_admin:
                    # Se è admin, ottiene tutti gli impianti delle CER amministrate
                    administered_cers = user.cer_memberships.filter(
                        role='ADMIN',
                        is_active=True
                    ).values_list('cer_configuration_id', flat=True)
                    
                    total_power = Plant.objects.filter(
                        cer_configuration_id__in=administered_cers,
                        is_active=True
                    ).aggregate(
                        total_power=Sum('nominal_power')
                    )['total_power'] or 0
                else:
                    # Se non è admin, ottiene solo i suoi impianti
                    total_power = Plant.objects.filter(
                        owner=user,
                        is_active=True
                    ).aggregate(
                        total_power=Sum('nominal_power')
                    )['total_power'] or 0
                    
                return round(total_power, 2)
            return 0
    
class CerDashboardView(CerBaseView, StaffRequiredMixin):
    """Dashboard amministrativa per le CER"""
    template_name = 'admin/dashboard/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Statistiche CER
        context['total_cer'] = CERConfiguration.objects.count()
        context['active_cer'] = CERConfiguration.objects.filter(
            is_active=True
        ).count()
        
        # Statistiche impianti
        context['total_plants'] = Plant.objects.count()
        context['active_plants'] = Plant.objects.filter(
            is_active=True
        ).count()
        
        # Ultime misurazioni
        context['latest_measurements'] = DeviceMeasurement.objects.select_related(
            'device', 'device__plant', 'device__plant__owner'
        ).order_by('-timestamp')[:10]
        
        # Statistiche settimanali
        seven_days_ago = timezone.now() - timezone.timedelta(days=7)
        context['weekly_stats'] = self._calculate_weekly_stats(seven_days_ago)
        
        return context

    def _calculate_weekly_stats(self, start_date):
        """Calcola le statistiche degli ultimi 7 giorni"""
        measurements = DeviceMeasurement.objects.filter(
            timestamp__gte=start_date
        )
        
        return {
            'total_energy': measurements.aggregate(
                total=Sum('value')
            )['total'] or 0,
            'active_devices': DeviceConfiguration.objects.filter(
                measurements__timestamp__gte=start_date
            ).distinct().count(),
            'measurements_count': measurements.count()
        }