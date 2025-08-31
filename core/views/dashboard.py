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
        
        # Recupera gli impianti in base al ruolo
        if is_global_admin:
            # Per admin globali: tutti gli impianti
            plants = Plant.objects.filter(
                is_active=True
            ).select_related('cer_configuration', 'owner')
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
            ).distinct().select_related('cer_configuration', 'owner')

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

    def get_filtered_alerts(self, user, is_global_admin):
        """Recupera gli alert filtrati in base al ruolo dell'utente"""
        alerts_query = Alert.objects.filter(status='active')
        
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
        
        for plant in plants:
            # Calcola potenza attuale
            recent_measurements = DeviceMeasurement.objects.filter(
                plant=plant,
                timestamp__gte=time_threshold
            )
            if recent_measurements.exists():
                stats['total_power'] += recent_measurements.aggregate(
                    total=Sum('power'))['total'] or 0
                    
            # Energia giornaliera
            today_measurements = DeviceMeasurement.objects.filter(
                plant=plant,
                timestamp__gte=today_start
            )
            if today_measurements.exists():
                stats['today_energy'] += today_measurements.aggregate(
                    total=Sum('energy_total'))['total'] or 0
                    
            # Energia mensile
            month_measurements = DeviceMeasurement.objects.filter(
                plant=plant,
                timestamp__gte=month_start
            )
            if month_measurements.exists():
                stats['month_energy'] += month_measurements.aggregate(
                    total=Sum('energy_total'))['total'] or 0
                    
            # Energia annuale
            year_measurements = DeviceMeasurement.objects.filter(
                plant=plant,
                timestamp__gte=year_start
            )
            if year_measurements.exists():
                stats['year_energy'] += year_measurements.aggregate(
                    total=Sum('energy_total'))['total'] or 0
        
        # Converti potenza in kW
        stats['total_power'] = round(stats['total_power'] / 1000.0, 2)
        
        # Arrotonda i valori di energia
        stats['today_energy'] = round(stats['today_energy'], 2)
        stats['month_energy'] = round(stats['month_energy'], 2)
        stats['year_energy'] = round(stats['year_energy'], 2)
        
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
        # Ultime misurazioni energia (kWh)
        energy_types = ['DRAWN_ENERGY', 'INJECTED_ENERGY', 'PRODUCTION_ENERGY']
        context['latest_measurements'] = (
            DeviceMeasurement.objects.select_related('device', 'device__plant')
            .filter(measurement_type__in=energy_types)
            .order_by('-timestamp')[:10]
        )
        
        # Statistiche settimanali
        seven_days_ago = timezone.now() - timezone.timedelta(days=7)
        context['weekly_stats'] = self._calculate_weekly_stats(seven_days_ago)
        
        return context

    def _calculate_weekly_stats(self, start_date):
        """Calcola le statistiche degli ultimi 7 giorni"""
        measurements = DeviceMeasurement.objects.filter(timestamp__gte=start_date)
        # Somma energia totale (kWh) per gli ultimi 7 giorni
        total_energy = measurements.aggregate(total=Sum('energy_total'))['total'] or 0
        # Conta dispositivi con almeno una misurazione nel periodo (evita import diretto)
        active_devices = measurements.values('device').distinct().count()
        return {
            'total_energy': total_energy,
            'active_devices': active_devices,
            'measurements_count': measurements.count(),
        }
