# core/views/fees.py
import logging
from decimal import Decimal
from django.views.generic import ListView, DetailView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json

from ..models import CERConfiguration, CERMembership, MembershipCard, MemberRegistry
from ..forms import MembershipFeeForm

logger = logging.getLogger(__name__)

class CERFeesManagementView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Vista per la gestione delle quote associative di una CER (solo admin)"""
    template_name = 'core/cer_fees.html'
    context_object_name = 'cards'
    paginate_by = 20
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get_queryset(self):
        cer = get_object_or_404(CERConfiguration, pk=self.kwargs['cer_pk'])
        
        queryset = MembershipCard.objects.filter(
            membership__cer_configuration=cer
        ).select_related(
            'membership__user', 
            'membership__cer_configuration'
        ).order_by('-issue_date')
        
        # Filtri
        status = self.request.GET.get('status')
        if status == 'paid':
            queryset = queryset.filter(membership_fee_paid=True)
        elif status == 'pending':
            queryset = queryset.filter(membership_fee_paid=False)
        
        member_type = self.request.GET.get('member_type')
        if member_type:
            queryset = queryset.filter(membership__member_type=member_type)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cer = get_object_or_404(CERConfiguration, pk=self.kwargs['cer_pk'])
        
        # Statistiche quote
        all_cards = MembershipCard.objects.filter(membership__cer_configuration=cer)
        
        total_amount = all_cards.aggregate(Sum('fee_amount'))['fee_amount__sum'] or 0
        paid_amount = all_cards.filter(membership_fee_paid=True).aggregate(Sum('fee_amount'))['fee_amount__sum'] or 0
        pending_amount = total_amount - paid_amount
        
        paid_count = all_cards.filter(membership_fee_paid=True).count()
        pending_count = all_cards.filter(membership_fee_paid=False).count()
        
        context.update({
            'cer': cer,
            'stats': {
                'total_cards': all_cards.count(),
                'paid_count': paid_count,
                'pending_count': pending_count,
                'total_amount': total_amount,
                'paid_amount': paid_amount,
                'pending_amount': pending_amount,
            },
            'current_filter': self.request.GET.get('status', ''),
            'member_type_filter': self.request.GET.get('member_type', ''),
        })
        
        return context

class MembershipFeeDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Vista per gestire una singola quota associativa"""
    model = MembershipCard
    template_name = 'core/membership_fee_detail.html'
    context_object_name = 'card'
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        card = self.get_object()
        
        context.update({
            'cer': card.membership.cer_configuration,
            'membership': card.membership,
            'payment_methods': [
                ('CASH', 'Contanti'),
                ('BANK_TRANSFER', 'Bonifico'),
                ('CARD', 'Carta'),
                ('OTHER', 'Altro')
            ]
        })
        
        return context

@login_required
@require_POST
def set_membership_fee(request, card_id):
    """API per impostare l'importo della quota"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Permessi insufficienti'}, status=403)
    
    try:
        card = get_object_or_404(MembershipCard, pk=card_id)
        data = json.loads(request.body)
        
        amount = Decimal(str(data.get('amount', 0)))
        if amount < 0:
            return JsonResponse({'error': 'L\'importo deve essere positivo'}, status=400)
        
        card.fee_amount = amount
        card.save(update_fields=['fee_amount'])
        
        return JsonResponse({
            'success': True,
            'message': f'Quota impostata a €{amount} per {card.membership.user.username}'
        })
        
    except Exception as e:
        logger.error(f"Errore nell'impostazione quota: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required 
@require_POST
def mark_fee_paid(request, card_id):
    """API per segnare una quota come pagata"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Permessi insufficienti'}, status=403)
    
    try:
        card = get_object_or_404(MembershipCard, pk=card_id)
        data = json.loads(request.body)
        
        payment_method = data.get('payment_method', 'BANK_TRANSFER')
        amount = data.get('amount')
        
        if amount:
            card.pay_fee(Decimal(str(amount)), payment_method)
        else:
            card.pay_fee(card.fee_amount, payment_method)
        
        return JsonResponse({
            'success': True,
            'message': f'Quota segnata come pagata per {card.membership.user.username}',
            'payment_date': card.fee_payment_date.strftime('%d/%m/%Y %H:%M')
        })
        
    except Exception as e:
        logger.error(f"Errore nella registrazione pagamento: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_POST  
def bulk_set_fees(request, cer_pk):
    """API per impostare quote multiple"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Permessi insufficienti'}, status=403)
    
    try:
        cer = get_object_or_404(CERConfiguration, pk=cer_pk)
        data = json.loads(request.body)
        
        amount = Decimal(str(data.get('amount', 0)))
        member_type = data.get('member_type', 'all')
        
        if amount < 0:
            return JsonResponse({'error': 'L\'importo deve essere positivo'}, status=400)
        
        # Filtra le tessere da aggiornare
        cards = MembershipCard.objects.filter(
            membership__cer_configuration=cer
        )
        
        if member_type != 'all':
            cards = cards.filter(membership__member_type=member_type)
        
        updated = cards.update(fee_amount=amount)
        
        return JsonResponse({
            'success': True,
            'message': f'Quota di €{amount} impostata per {updated} tessere',
            'updated_count': updated
        })
        
    except Exception as e:
        logger.error(f"Errore nell'impostazione quote multiple: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

class MembershipFeeReportView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Vista per il report delle quote associative"""
    template_name = 'core/membership_fee_report.html'
    context_object_name = 'cards'
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get_queryset(self):
        cer = get_object_or_404(CERConfiguration, pk=self.kwargs['cer_pk'])
        
        return MembershipCard.objects.filter(
            membership__cer_configuration=cer
        ).select_related(
            'membership__user',
            'membership__cer_configuration'
        ).order_by('membership__user__username')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cer = get_object_or_404(CERConfiguration, pk=self.kwargs['cer_pk'])
        
        # Statistiche dettagliate per tipo membro
        stats_by_type = {}
        for member_type, display in [('CONSUMER', 'Consumatori'), ('PRODUCER', 'Produttori'), ('PROSUMER', 'Prosumer')]:
            cards_type = self.get_queryset().filter(membership__member_type=member_type)
            
            stats_by_type[member_type] = {
                'display': display,
                'total_count': cards_type.count(),
                'paid_count': cards_type.filter(membership_fee_paid=True).count(),
                'pending_count': cards_type.filter(membership_fee_paid=False).count(),
                'total_amount': cards_type.aggregate(Sum('fee_amount'))['fee_amount__sum'] or 0,
                'paid_amount': cards_type.filter(membership_fee_paid=True).aggregate(Sum('fee_amount'))['fee_amount__sum'] or 0,
            }
            stats_by_type[member_type]['pending_amount'] = stats_by_type[member_type]['total_amount'] - stats_by_type[member_type]['paid_amount']
        
        context.update({
            'cer': cer,
            'stats_by_type': stats_by_type,
            'export_format': self.request.GET.get('export', None)
        })
        
        return context