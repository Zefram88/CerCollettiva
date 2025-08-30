# core/views/economic.py

from django.views.generic import ListView, DetailView, TemplateView
from django.db.models import Sum, Count, Q, Avg
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from datetime import datetime, timedelta
from decimal import Decimal

from .base import CerBaseView
from .mixins.auth import StaffRequiredMixin
from ..models import (
    CERConfiguration, 
    CERDistributionConfiguration, 
    GSEIncomeTracking,
    CERMembership
)


class EconomicDashboardView(CerBaseView):
    """Dashboard economica per il monitoraggio degli incassi e distribuzioni"""
    template_name = 'core/economic/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Determina le CER accessibili all'utente
        accessible_cers = self.get_accessible_cers(user)
        
        # Statistiche generali
        context.update({
            'accessible_cers': accessible_cers,
            'total_cers': accessible_cers.count(),
            'economic_stats': self.get_economic_stats(accessible_cers),
            'recent_payments': self.get_recent_payments(accessible_cers),
            'overdue_payments': self.get_overdue_payments(accessible_cers),
            'monthly_summary': self.get_monthly_summary(accessible_cers),
        })
        
        return context
    
    def get_accessible_cers(self, user):
        """Restituisce le CER accessibili all'utente"""
        if user.is_superuser:
            return CERConfiguration.objects.filter(is_active=True)
        
        # Per utenti normali, solo le CER di cui sono membri
        return CERConfiguration.objects.filter(
            memberships__user=user,
            memberships__is_active=True,
            is_active=True
        ).distinct()
    
    def get_economic_stats(self, cers):
        """Calcola statistiche economiche aggregate"""
        current_year = timezone.now().year
        current_month = timezone.now().month
        
        total_income = GSEIncomeTracking.objects.filter(
            cer_configuration__in=cers,
            payment_status='RECEIVED'
        ).aggregate(
            total=Sum('net_amount')
        )['total'] or Decimal('0')
        
        year_income = GSEIncomeTracking.objects.filter(
            cer_configuration__in=cers,
            reference_year=current_year,
            payment_status='RECEIVED'
        ).aggregate(
            total=Sum('net_amount')
        )['total'] or Decimal('0')
        
        month_income = GSEIncomeTracking.objects.filter(
            cer_configuration__in=cers,
            reference_year=current_year,
            reference_month__month=current_month,
            payment_status='RECEIVED'
        ).aggregate(
            total=Sum('net_amount')
        )['total'] or Decimal('0')
        
        pending_amount = GSEIncomeTracking.objects.filter(
            cer_configuration__in=cers,
            payment_status__in=['EXPECTED', 'DELAYED']
        ).aggregate(
            total=Sum('net_amount')
        )['total'] or Decimal('0')
        
        return {
            'total_income': total_income,
            'year_income': year_income,
            'month_income': month_income,
            'pending_amount': pending_amount,
            'avg_monthly_income': year_income / 12 if year_income > 0 else Decimal('0')
        }
    
    def get_recent_payments(self, cers):
        """Ultimi 10 pagamenti ricevuti"""
        return GSEIncomeTracking.objects.filter(
            cer_configuration__in=cers,
            payment_status='RECEIVED'
        ).order_by('-actual_payment_date')[:10]
    
    def get_overdue_payments(self, cers):
        """Pagamenti in ritardo"""
        return GSEIncomeTracking.objects.filter(
            cer_configuration__in=cers,
            payment_status__in=['EXPECTED', 'DELAYED'],
            expected_payment_date__lt=timezone.now().date()
        ).order_by('expected_payment_date')
    
    def get_monthly_summary(self, cers):
        """Riassunto mensile dell'anno corrente"""
        current_year = timezone.now().year
        
        monthly_data = []
        for month in range(1, 13):
            month_payments = GSEIncomeTracking.objects.filter(
                cer_configuration__in=cers,
                reference_year=current_year,
                reference_month__month=month
            )
            
            received = month_payments.filter(payment_status='RECEIVED').aggregate(
                total=Sum('net_amount')
            )['total'] or Decimal('0')
            
            expected = month_payments.filter(payment_status='EXPECTED').aggregate(
                total=Sum('net_amount')
            )['total'] or Decimal('0')
            
            monthly_data.append({
                'month': month,
                'month_name': datetime(current_year, month, 1).strftime('%B'),
                'received': received,
                'expected': expected,
                'total': received + expected
            })
        
        return monthly_data


class CERDistributionDetailView(CerBaseView, DetailView):
    """Dettaglio della configurazione di ripartizione di una CER"""
    model = CERDistributionConfiguration
    template_name = 'core/economic/distribution_detail.html'
    context_object_name = 'distribution_config'
    
    def get_object(self):
        cer_id = self.kwargs.get('cer_id')
        cer = get_object_or_404(CERConfiguration, id=cer_id)
        
        # Verifica accesso utente alla CER
        if not self.can_access_cer(self.request.user, cer):
            raise PermissionDenied("Non hai accesso a questa CER")
        
        # Ottiene o crea la configurazione di distribuzione
        config, created = CERDistributionConfiguration.objects.get_or_create(
            cer_configuration=cer,
            defaults={
                'producer_percentage': Decimal('45.00'),
                'consumer_percentage': Decimal('30.00'),
                'management_percentage': Decimal('20.00'),
                'investment_fund_percentage': Decimal('3.00'),
                'solidarity_fund_percentage': Decimal('2.00'),
                'is_active': True
            }
        )
        return config
    
    def can_access_cer(self, user, cer):
        """Verifica se l'utente può accedere alla CER"""
        if user.is_superuser:
            return True
        
        return CERMembership.objects.filter(
            user=user,
            cer_configuration=cer,
            is_active=True
        ).exists()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Calcola statistiche di distribuzione
        config = self.get_object()
        cer = config.cer_configuration
        
        # Ultimi 6 mesi di incassi per simulazione ripartizione
        recent_payments = GSEIncomeTracking.objects.filter(
            cer_configuration=cer,
            payment_status='RECEIVED'
        ).order_by('-reference_month')[:6]
        
        distributions = []
        for payment in recent_payments:
            distribution = payment.calculate_distribution()
            if distribution:
                distributions.append({
                    'payment': payment,
                    'distribution': distribution
                })
        
        # Membri per categoria
        members_stats = {
            'producers': CERMembership.objects.filter(
                cer_configuration=cer,
                member_type__in=['PRODUCER', 'PROSUMER'],
                is_active=True
            ).count(),
            'consumers': CERMembership.objects.filter(
                cer_configuration=cer,
                member_type__in=['CONSUMER', 'PROSUMER'],
                is_active=True
            ).count(),
            'total': CERMembership.objects.filter(
                cer_configuration=cer,
                is_active=True
            ).count()
        }
        
        context.update({
            'cer': cer,
            'recent_distributions': distributions,
            'members_stats': members_stats,
            'can_edit': self.can_edit_config(self.request.user, cer)
        })
        
        return context
    
    def can_edit_config(self, user, cer):
        """Verifica se l'utente può modificare la configurazione"""
        if user.is_superuser:
            return True
        
        return CERMembership.objects.filter(
            user=user,
            cer_configuration=cer,
            role='ADMIN',
            is_active=True
        ).exists()


class GSEPaymentsListView(CerBaseView, ListView):
    """Lista dei pagamenti GSE con filtri"""
    model = GSEIncomeTracking
    template_name = 'core/economic/payments_list.html'
    context_object_name = 'payments'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = GSEIncomeTracking.objects.select_related('cer_configuration')
        
        # Filtra per CER accessibili
        user = self.request.user
        if not user.is_superuser:
            accessible_cer_ids = CERMembership.objects.filter(
                user=user,
                is_active=True
            ).values_list('cer_configuration_id', flat=True)
            queryset = queryset.filter(cer_configuration_id__in=accessible_cer_ids)
        
        # Applica filtri dalla query string
        cer_id = self.request.GET.get('cer')
        if cer_id:
            queryset = queryset.filter(cer_configuration_id=cer_id)
        
        payment_type = self.request.GET.get('type')
        if payment_type:
            queryset = queryset.filter(payment_type=payment_type)
        
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(payment_status=status)
        
        year = self.request.GET.get('year')
        if year:
            queryset = queryset.filter(reference_year=int(year))
        
        return queryset.order_by('-reference_year', '-reference_month', '-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Opzioni per i filtri
        user = self.request.user
        if user.is_superuser:
            accessible_cers = CERConfiguration.objects.filter(is_active=True)
        else:
            accessible_cers = CERConfiguration.objects.filter(
                memberships__user=user,
                memberships__is_active=True,
                is_active=True
            ).distinct()
        
        context.update({
            'accessible_cers': accessible_cers,
            'payment_types': GSEIncomeTracking.PAYMENT_TYPES,
            'payment_statuses': GSEIncomeTracking.PAYMENT_STATUS,
            'years': range(2020, timezone.now().year + 2),
            'current_filters': {
                'cer': self.request.GET.get('cer', ''),
                'type': self.request.GET.get('type', ''),
                'status': self.request.GET.get('status', ''),
                'year': self.request.GET.get('year', '')
            }
        })
        
        return context


class EconomicReportsView(CerBaseView):
    """Generazione di report economici"""
    template_name = 'core/economic/reports.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        user = self.request.user
        accessible_cers = self.get_accessible_cers(user)
        
        # Report data per grafici
        context.update({
            'accessible_cers': accessible_cers,
            'report_data': self.generate_report_data(accessible_cers),
        })
        
        return context
    
    def get_accessible_cers(self, user):
        """Restituisce le CER accessibili all'utente"""
        if user.is_superuser:
            return CERConfiguration.objects.filter(is_active=True)
        
        return CERConfiguration.objects.filter(
            memberships__user=user,
            memberships__is_active=True,
            is_active=True
        ).distinct()
    
    def generate_report_data(self, cers):
        """Genera dati per i report"""
        current_year = timezone.now().year
        
        # Andamento mensile
        monthly_trend = []
        for month in range(1, 13):
            month_income = GSEIncomeTracking.objects.filter(
                cer_configuration__in=cers,
                reference_year=current_year,
                reference_month__month=month,
                payment_status='RECEIVED'
            ).aggregate(
                total=Sum('net_amount')
            )['total'] or Decimal('0')
            
            monthly_trend.append({
                'month': month,
                'income': float(month_income)
            })
        
        # Ripartizione per CER
        cer_breakdown = []
        for cer in cers:
            cer_income = GSEIncomeTracking.objects.filter(
                cer_configuration=cer,
                payment_status='RECEIVED'
            ).aggregate(
                total=Sum('net_amount')
            )['total'] or Decimal('0')
            
            cer_breakdown.append({
                'name': cer.name,
                'income': float(cer_income)
            })
        
        # Ripartizione per tipo di pagamento
        payment_type_breakdown = []
        for payment_type, display_name in GSEIncomeTracking.PAYMENT_TYPES:
            type_income = GSEIncomeTracking.objects.filter(
                cer_configuration__in=cers,
                payment_type=payment_type,
                payment_status='RECEIVED'
            ).aggregate(
                total=Sum('net_amount')
            )['total'] or Decimal('0')
            
            payment_type_breakdown.append({
                'type': display_name,
                'income': float(type_income)
            })
        
        return {
            'monthly_trend': monthly_trend,
            'cer_breakdown': cer_breakdown,
            'payment_type_breakdown': payment_type_breakdown
        }


def distribution_simulation_ajax(request, cer_id):
    """Vista AJAX per simulare la ripartizione di un importo"""
    if not request.is_ajax() or request.method != 'POST':
        return JsonResponse({'error': 'Richiesta non valida'}, status=400)
    
    try:
        cer = get_object_or_404(CERConfiguration, id=cer_id)
        amount = Decimal(request.POST.get('amount', 0))
        
        if amount <= 0:
            return JsonResponse({'error': 'Importo non valido'}, status=400)
        
        # Ottieni la configurazione di distribuzione
        try:
            config = cer.distribution_config
        except CERDistributionConfiguration.DoesNotExist:
            return JsonResponse({'error': 'Configurazione di distribuzione non trovata'}, status=404)
        
        # Calcola la ripartizione
        distribution = config.get_distribution_breakdown(float(amount))
        
        # Informazioni sui membri
        members_info = {
            'producers_count': CERMembership.objects.filter(
                cer_configuration=cer,
                member_type__in=['PRODUCER', 'PROSUMER'],
                is_active=True
            ).count(),
            'consumers_count': CERMembership.objects.filter(
                cer_configuration=cer,
                member_type__in=['CONSUMER', 'PROSUMER'],
                is_active=True
            ).count()
        }
        
        return JsonResponse({
            'success': True,
            'distribution': distribution,
            'members_info': members_info
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)