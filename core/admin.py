# core/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import path, reverse
from django.utils.translation import gettext_lazy as _
from .models import CERConfiguration, CERMembership, Plant, PlantMeasurement, PlantDocument, Alert, MembershipCard, MemberRegistry, CERDistributionConfiguration, GSEIncomeTracking
from .views import CerDashboardView
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.core.paginator import Paginator  # Aggiungiamo questa importazione
from django.utils.decorators import method_decorator
from django.db.models import Count, Sum, Q
from datetime import datetime, time, timedelta
from django.utils import timezone

from django.http import HttpResponseBadRequest, Http404
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import ValidationError

class CERAdminSite(admin.AdminSite):
    site_header = 'CerCollettiva Administration'
    site_title = 'CerCollettiva Admin'
    index_title = 'Amministrazione CerCollettiva'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_view(CerDashboardView.as_view()), name='admin_dashboard'),
            # Aggiungi questo URL per la lista CER
            path('cer/list/', self.admin_view(self.cer_list_view), name='cer_list'),
        ]
        return custom_urls + urls

    def cer_list_view(self, request):
        """Lista CER con ricerca e filtri"""
        # Debug log
        print(f"User: {request.user}")
        print(f"Staff: {request.user.is_staff}")
        
        search_query = request.GET.get('q', '')
        status_filter = request.GET.get('status', '')
        
        # Query base
        cer_list = CERConfiguration.objects.all()
        
        # Debug log
        print(f"Numero totale CER: {cer_list.count()}")
        
        # Applica filtri
        if search_query:
            cer_list = cer_list.filter(name__icontains=search_query)
        
        if status_filter:
            is_active = status_filter == 'active'
            cer_list = cer_list.filter(is_active=is_active)
        
        # Ordinamento
        cer_list = cer_list.order_by('-created_at')
        
        # Paginazione
        paginator = Paginator(cer_list, 10)
        page = request.GET.get('page')
        object_list = paginator.get_page(page)
        
        context = {
            'object_list': object_list,
            'search_query': search_query,
            'status_filter': status_filter,
            'total_count': CERConfiguration.objects.count(),
            'active_count': CERConfiguration.objects.filter(is_active=True).count(),
            'opts': CERConfiguration._meta,  # Importante per i template admin
            'title': 'Gestione CER',
            'cl': object_list,  # Per compatibilità con i template admin
            'is_popup': False,
            'has_add_permission': request.user.has_perm('core.add_cerconfiguration'),
            'has_change_permission': request.user.has_perm('core.change_cerconfiguration'),
            'has_delete_permission': request.user.has_perm('core.delete_cerconfiguration'),
        }
        
        return render(request, 'admin/dashboard/change_list.html', context)

    def index(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['dashboard_url'] = reverse('ceradmin:admin_dashboard')
        return super().index(request, extra_context=extra_context)


class CERConfigurationAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'primary_substation', 'is_active', 'created_at', 'get_members_count']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'code', 'primary_substation']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'updated_at']
    
    change_list_template = 'admin/dashboard/change_list.html'
    change_form_template = 'admin/dashboard/change_form.html'
    delete_confirmation_template = 'admin/dashboard/delete_confirmation.html'

    
    def get_members_count(self, obj):
        return obj.members.count()
    get_members_count.short_description = 'Numero membri'
    
    def response_add(self, request, obj, post_url_continue=None):
        """Reindirizza alla lista dopo il salvataggio"""
        return self.response_post_save_add(request, obj)
    
    def response_change(self, request, obj):
        """Reindirizza alla lista dopo la modifica"""
        return self.response_post_save_change(request, obj)
    
    def changelist_view(self, request, extra_context=None):
        """Override della vista lista per reindirizzare alla nostra vista custom"""
        return self.admin_site.cer_list_view(request)

    def get_deleted_objects(self, objs, request):
        """Personalizza gli oggetti mostrati nella pagina di conferma eliminazione"""
        deletable_objects, model_count, perms_needed, protected = super().get_deleted_objects(objs, request)
        return deletable_objects, model_count, perms_needed, protected

    def delete_view(self, request, object_id, extra_context=None):
        """Personalizza il contesto della vista di eliminazione"""
        extra_context = extra_context or {}
        extra_context.update({
            'title': 'Elimina CER',
            'is_popup': False,
            'has_change_permission': self.has_change_permission(request),
        })
        return super().delete_view(request, object_id, extra_context=extra_context)

class CERMembershipAdmin(admin.ModelAdmin):
    list_display = ['user', 'cer_configuration', 'role', 'is_active', 'joined_at', 
                   'document_verified', 'get_document_status']
    list_filter = ['role', 'is_active', 'document_verified', 'joined_at']
    search_fields = ['user__username', 'user__email', 'cer_configuration__name']
    date_hierarchy = 'joined_at'
    raw_id_fields = ['user', 'cer_configuration', 'document_verified_by']
    readonly_fields = ['joined_at', 'document_verified_at']
    
    fieldsets = (
        ('Informazioni Base', {
            'fields': ('user', 'cer_configuration', 'role', 'is_active')
        }),
        ('Documenti', {
            'fields': (
                'conformity_declaration', 'gse_practice', 'panels_photo',
                'inverter_photo', 'panels_serial_list'
            )
        }),
        ('Verifica Documenti', {
            'fields': ('document_verified', 'document_verified_at', 'document_verified_by')
        })
    )

    def get_document_status(self, obj):
        if obj.document_verified:
            return format_html('<span style="color: green;">✓ Verificato</span>')
        return format_html('<span style="color: red;">✗ Non verificato</span>')
    get_document_status.short_description = 'Stato documenti'

class PlantAdmin(admin.ModelAdmin):
    list_display = ['name', 'pod_code', 'plant_type', 'owner', 'cer_configuration', 
                   'is_active', 'get_mqtt_status', 'created_at', 'updated_at']
    list_filter = ['plant_type', 'is_active', 'created_at']
    search_fields = ['name', 'pod_code', 'owner__username', 'owner__email']
    date_hierarchy = 'created_at'
    raw_id_fields = ['owner', 'cer_configuration']
    readonly_fields = ['created_at', 'updated_at']

    change_list_template = 'admin/dashboard/plant_list.html'
    delete_confirmation_template = 'admin/dashboard/delete_confirmation.html'

    def changelist_view(self, request, extra_context=None):
        """Lista impianti personalizzata"""
        extra_context = extra_context or {}
        
        # Query base
        queryset = self.model.objects.all()
        
        # Aggiungiamo le CER disponibili al contesto
        extra_context['available_cers'] = CERConfiguration.objects.filter(is_active=True)
        
        # Filtri
        search_query = request.GET.get('q', '')
        plant_type = request.GET.get('type', '')
        status_filter = request.GET.get('status', '')
        
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(pod_code__icontains=search_query) |
                Q(owner__username__icontains=search_query)
            )
            
        if plant_type:
            queryset = queryset.filter(plant_type=plant_type)
            
        if status_filter:
            is_active = status_filter == 'active'
            queryset = queryset.filter(is_active=is_active)

        # Se l'utente è superuser, mostra tutte le CER attive
        if request.user.is_superuser:
            available_cers = CERConfiguration.objects.filter(is_active=True)
        else:
            # Altrimenti mostra solo le CER di cui l'utente è membro attivo
            available_cers = CERConfiguration.objects.filter(
                memberships__user=request.user,
                memberships__is_active=True,
                is_active=True
            )
        
        # Paginazione
        paginator = Paginator(queryset, 10)
        page = request.GET.get('page')
        object_list = paginator.get_page(page)
        
        extra_context.update({
            'title': 'Gestione Impianti',
            'object_list': object_list,
            'search_query': search_query,
            'plant_type': plant_type,
            'status_filter': status_filter,
            'total_count': queryset.count(),
            'active_count': queryset.filter(is_active=True).count(),
            'is_paginated': True if paginator.num_pages > 1 else False,
            'page_obj': object_list,
            'available_cers': available_cers,  # Le CER disponibili per l'associazione
            'has_add_permission': self.has_add_permission(request),
            'has_change_permission': self.has_change_permission(request),
            'has_delete_permission': self.has_delete_permission(request),
            'has_view_permission': self.has_view_permission(request),
            'opts': self.model._meta,  # Importante per gli URL admin
        })
        
        return super().changelist_view(request, extra_context=extra_context)

    def get_mqtt_status(self, obj):
        if obj.check_mqtt_connection():
            return format_html('<span class="badge bg-success">Connesso</span>')
        return format_html('<span class="badge bg-danger">Non connesso</span>')
    get_mqtt_status.short_description = 'Stato MQTT'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/associate-cer/',
                 self.admin_site.admin_view(self.associate_plant_cer),
                 name='associate_plant_cer'),
        ]
        return custom_urls + urls

    def associate_plant_cer(self, request, object_id):
        """Vista per gestire l'associazione di un impianto a una CER"""
        if request.method != 'POST':
            return HttpResponseBadRequest('Metodo non consentito')

        plant = self.get_object(request, object_id)
        if plant is None:
            raise Http404('Impianto non trovato')

        cer_id = request.POST.get('cer_id')
        
        try:
            if cer_id:
                # Verifica che la CER sia attiva
                cer = CERConfiguration.objects.filter(
                    id=cer_id, 
                    is_active=True
                ).first()
                
                if not cer:
                    messages.error(request, 'CER non trovata o non attiva')
                    return redirect('ceradmin:core_plant_changelist')

                # Se l'utente è admin, può associare liberamente
                if request.user.is_superuser:
                    # Verifica se il proprietario è già membro
                    membership = CERMembership.objects.filter(
                        user=plant.owner,
                        cer_configuration=cer,
                        is_active=True
                    ).first()
                    
                    # Se non è membro, lo aggiungiamo automaticamente
                    if not membership:
                        membership = CERMembership.objects.create(
                            user=plant.owner,
                            cer_configuration=cer,
                            role='MEMBER',
                            is_active=True,
                        )
                        messages.info(
                            request,
                            f'Il proprietario è stato automaticamente aggiunto come membro '
                            f'della CER "{cer.name}"'
                        )
                
                else:
                    # Per utenti non admin, verifica che siano membri attivi della CER
                    membership = CERMembership.objects.filter(
                        user=request.user,
                        cer_configuration=cer,
                        is_active=True
                    ).first()
                    
                    if not membership:
                        messages.error(
                            request,
                            'Non sei un membro attivo di questa CER'
                        )
                        return redirect('ceradmin:core_plant_changelist')

                # Associa l'impianto alla CER
                plant.cer_configuration = cer
                plant.save()
                messages.success(
                    request,
                    f'Impianto associato con successo alla CER "{cer.name}"'
                )
            
            else:
                # Rimozione associazione
                old_cer = plant.cer_configuration
                if old_cer:
                    plant.cer_configuration = None
                    plant.save()
                    messages.success(
                        request,
                        f'Associazione con la CER "{old_cer.name}" rimossa con successo'
                    )
                else:
                    messages.warning(request, 'L\'impianto non era associato a nessuna CER')

        except ValidationError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Errore durante l\'associazione: {str(e)}')

        return redirect('ceradmin:core_plant_changelist')
        

    def can_associate_cer(self, request, plant, cer):
        """Verifica se l'utente può associare l'impianto alla CER"""
        if request.user.is_superuser:
            return True
            
        # Per utenti non admin, verifica membership
        return CERMembership.objects.filter(
            user=plant.owner,
            cer_configuration=cer,
            is_active=True
        ).exists()

class PlantMeasurementAdmin(admin.ModelAdmin):
    list_display = ['plant', 'timestamp', 'value', 'variable_type', 'quality']
    list_filter = ['variable_type', 'quality', 'timestamp']
    search_fields = ['plant__name', 'plant__pod_code']
    date_hierarchy = 'timestamp'

class PlantDocumentAdmin(admin.ModelAdmin):
    list_display = ['plant', 'name', 'document_type', 'uploaded_at']
    list_filter = ['document_type', 'uploaded_at']
    search_fields = ['plant__name', 'name']
    date_hierarchy = 'uploaded_at'

# Creazione dell'istanza del sito admin personalizzato
admin_site = CERAdminSite(name='ceradmin')

# Registrazione dei modelli con il sito admin personalizzato
@admin.register(MembershipCard, site=admin_site)
class MembershipCardAdmin(admin.ModelAdmin):
    list_display = ['card_number', 'membership_user', 'membership_cer', 'issue_date', 'expiry_date', 'is_valid_status', 'fee_paid_status']
    list_filter = ['is_active', 'membership_fee_paid', 'issue_date', 'expiry_date']
    search_fields = ['card_number', 'membership__user__username', 'membership__cer_configuration__name']
    readonly_fields = ['issue_date']
    
    fieldsets = (
        ('Informazioni Tessera', {
            'fields': ('card_number', 'membership', 'issue_date', 'expiry_date', 'is_active')
        }),
        ('Gestione Quote', {
            'fields': ('membership_fee_paid', 'fee_amount', 'fee_payment_date', 'payment_method'),
            'classes': ['collapse']
        })
    )
    
    def membership_user(self, obj):
        return obj.membership.user.username
    membership_user.short_description = 'Utente'
    
    def membership_cer(self, obj):
        return obj.membership.cer_configuration.name
    membership_cer.short_description = 'CER'
    
    def is_valid_status(self, obj):
        if obj.is_valid:
            return format_html('<span style="color: green;">✓ Valida</span>')
        else:
            return format_html('<span style="color: red;">✗ Non valida</span>')
    is_valid_status.short_description = 'Stato'
    
    def fee_paid_status(self, obj):
        if obj.membership_fee_paid:
            return format_html('<span style="color: green;">✓ Pagata</span>')
        else:
            return format_html('<span style="color: orange;">⏳ In attesa</span>')
    fee_paid_status.short_description = 'Quota'
    
    actions = ['renew_cards', 'mark_fee_paid']
    
    def renew_cards(self, request, queryset):
        for card in queryset:
            card.renew()
        self.message_user(request, f"{queryset.count()} tessere rinnovate con successo.")
    renew_cards.short_description = "Rinnova tessere selezionate"
    
    def mark_fee_paid(self, request, queryset):
        updated = queryset.update(membership_fee_paid=True)
        self.message_user(request, f"{updated} quote segnate come pagate.")
    mark_fee_paid.short_description = "Segna quote come pagate"

@admin.register(MemberRegistry, site=admin_site)  
class MemberRegistryAdmin(admin.ModelAdmin):
    list_display = ['progressive_display', 'user_info', 'cer_name', 'member_type_display', 'registration_date', 'has_card']
    list_filter = ['cer_configuration', 'membership__member_type', 'registration_date']
    search_fields = ['membership__user__username', 'membership__user__fiscal_code', 'cer_configuration__name']
    readonly_fields = ['progressive_number', 'registration_date']
    ordering = ['cer_configuration', 'progressive_number']
    
    def progressive_display(self, obj):
        return f"{obj.cer_configuration.code}-{obj.progressive_number:04d}"
    progressive_display.short_description = 'N. Registro'
    
    def user_info(self, obj):
        user = obj.membership.user
        return f"{user.username} ({user.get_legal_type_display()})"
    user_info.short_description = 'Utente'
    
    def cer_name(self, obj):
        return obj.cer_configuration.name
    cer_name.short_description = 'CER'
    
    def member_type_display(self, obj):
        return obj.membership.get_member_type_display()
    member_type_display.short_description = 'Tipo Membro'
    
    def has_card(self, obj):
        if hasattr(obj.membership, 'card'):
            return format_html('<span style="color: green;">✓</span>')
        else:
            return format_html('<span style="color: red;">✗</span>')
    has_card.short_description = 'Tessera'

@admin.register(CERDistributionConfiguration, site=admin_site)
class CERDistributionConfigurationAdmin(admin.ModelAdmin):
    list_display = [
        'cer_configuration', 'producer_percentage', 'consumer_percentage', 
        'management_percentage', 'investment_fund_percentage', 'solidarity_fund_percentage',
        'total_percentage_display', 'is_active', 'updated_at'
    ]
    list_filter = ['is_active', 'created_at', 'updated_at']
    search_fields = ['cer_configuration__name', 'cer_configuration__code']
    readonly_fields = ['created_at', 'updated_at', 'total_percentage']
    
    fieldsets = (
        ('CER di Riferimento', {
            'fields': ('cer_configuration', 'is_active')
        }),
        ('Percentuali di Ripartizione', {
            'fields': (
                ('producer_percentage', 'consumer_percentage'),
                ('management_percentage', 'investment_fund_percentage', 'solidarity_fund_percentage'),
                'total_percentage'
            ),
            'description': 'La somma delle percentuali deve essere esattamente 100%'
        }),
        ('Descrizioni e Note', {
            'fields': ('management_description', 'investment_description', 'solidarity_description'),
            'classes': ['collapse']
        }),
        ('Informazioni Sistema', {
            'fields': ('created_at', 'updated_at'),
            'classes': ['collapse']
        })
    )
    
    def total_percentage_display(self, obj):
        total = obj.total_percentage
        if abs(total - 100) > 0.01:
            return format_html('<span style="color: red; font-weight: bold;">{}%</span>', total)
        return format_html('<span style="color: green;">{}%</span>', total)
    total_percentage_display.short_description = 'Totale %'
    
    def save_model(self, request, obj, form, change):
        try:
            obj.full_clean()
            super().save_model(request, obj, form, change)
            messages.success(request, 'Configurazione ripartizione salvata con successo.')
        except ValidationError as e:
            messages.error(request, f'Errore di validazione: {e}')
    
    actions = ['duplicate_configuration']
    
    def duplicate_configuration(self, request, queryset):
        for config in queryset:
            config.pk = None
            config.is_active = False
            config.save()
        self.message_user(request, f"{queryset.count()} configurazioni duplicate (impostate come non attive).")
    duplicate_configuration.short_description = "Duplica configurazioni selezionate"

@admin.register(GSEIncomeTracking, site=admin_site)  
class GSEIncomeTrackingAdmin(admin.ModelAdmin):
    list_display = [
        'cer_configuration', 'payment_type_display', 'reference_period', 
        'gross_amount', 'net_amount', 'payment_status', 'payment_status_display',
        'expected_payment_date', 'actual_payment_date', 'days_overdue_display'
    ]
    list_filter = [
        'payment_type', 'payment_status', 'reference_year', 'reference_month',
        'expected_payment_date', 'actual_payment_date'
    ]
    search_fields = [
        'cer_configuration__name', 'cer_configuration__code', 
        'gse_practice_number', 'notes'
    ]
    date_hierarchy = 'reference_month'
    readonly_fields = ['created_at', 'updated_at', 'is_overdue', 'days_overdue']
    
    fieldsets = (
        ('Informazioni Base', {
            'fields': (
                'cer_configuration', 'payment_type', 
                ('reference_month', 'reference_year'),
                'gse_practice_number'
            )
        }),
        ('Importi', {
            'fields': (
                ('gross_amount', 'taxes_amount', 'net_amount'),
            )
        }),
        ('Date e Stato', {
            'fields': (
                'payment_status',
                ('expected_payment_date', 'actual_payment_date'),
                ('is_overdue', 'days_overdue')
            )
        }),
        ('Dettagli Tecnici', {
            'fields': (
                ('shared_energy_kwh', 'energy_tariff'),
                'notes'
            ),
            'classes': ['collapse']
        }),
        ('Allegati', {
            'fields': ('gse_communication',),
            'classes': ['collapse']
        }),
        ('Informazioni Sistema', {
            'fields': ('created_at', 'updated_at'),
            'classes': ['collapse']
        })
    )
    
    def payment_type_display(self, obj):
        colors = {
            'ADVANCE': 'primary',
            'SETTLEMENT': 'success', 
            'ADJUSTMENT': 'warning'
        }
        color = colors.get(obj.payment_type, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>', 
            color, obj.get_payment_type_display()
        )
    payment_type_display.short_description = 'Tipo'
    
    def reference_period(self, obj):
        return f"{obj.reference_month.strftime('%m/%Y')}"
    reference_period.short_description = 'Periodo'
    
    def payment_status_display(self, obj):
        colors = {
            'EXPECTED': 'secondary',
            'RECEIVED': 'success',
            'DELAYED': 'warning',
            'DISPUTED': 'danger'
        }
        color = colors.get(obj.payment_status, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>', 
            color, obj.get_payment_status_display()
        )
    payment_status_display.short_description = 'Stato'
    
    def days_overdue_display(self, obj):
        if obj.is_overdue:
            return format_html('<span style="color: red; font-weight: bold;">+{} giorni</span>', obj.days_overdue)
        return '-'
    days_overdue_display.short_description = 'Ritardo'
    
    actions = ['mark_as_received', 'calculate_distributions', 'export_to_excel']
    
    def mark_as_received(self, request, queryset):
        updated = 0
        for payment in queryset.filter(payment_status__in=['EXPECTED', 'DELAYED']):
            payment.mark_as_received()
            updated += 1
        self.message_user(request, f"{updated} pagamenti segnati come ricevuti.")
    mark_as_received.short_description = "Segna come ricevuti"
    
    def calculate_distributions(self, request, queryset):
        results = []
        for payment in queryset.filter(payment_status='RECEIVED'):
            distribution = payment.calculate_distribution()
            if distribution:
                results.append(f"{payment}: €{distribution['total']:.2f}")
        
        if results:
            message = "Ripartizioni calcolate:\n" + "\n".join(results)
            self.message_user(request, message)
        else:
            self.message_user(request, "Nessuna ripartizione calcolabile per i pagamenti selezionati.")
    calculate_distributions.short_description = "Calcola ripartizioni"
    
    def export_to_excel(self, request, queryset):
        # Qui si potrebbe implementare l'export Excel
        self.message_user(request, f"Export Excel di {queryset.count()} record (funzionalità da implementare)")
    export_to_excel.short_description = "Esporta in Excel"

admin_site.register(CERConfiguration, CERConfigurationAdmin)
admin_site.register(CERMembership, CERMembershipAdmin)
admin_site.register(Plant, PlantAdmin)
admin_site.register(PlantMeasurement, PlantMeasurementAdmin)
admin_site.register(PlantDocument, PlantDocumentAdmin)