# core/forms.py
from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from .models import CERConfiguration, CERMembership, Plant, PlantDocument

class PlantDocumentForm(forms.ModelForm):
    class Meta:
        model = PlantDocument
        fields = ['name', 'document', 'document_type']

class CERConfigurationForm(forms.ModelForm):
    """Form per la configurazione di una Comunità Energetica Rinnovabile"""
    
    class Meta:
        model = CERConfiguration
        fields = ['name', 'code', 'primary_substation']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome della CER'
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Codice identificativo univoco'
            }),
            'primary_substation': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome della cabina primaria'
            }),
        }
        help_texts = {
            'name': 'Nome identificativo della Comunità Energetica',
            'code': 'Codice univoco assegnato alla CER',
            'primary_substation': 'Nome della cabina primaria di riferimento'
        }

class CERMembershipForm(forms.ModelForm):
    """Form per la gestione dell'adesione a una CER"""
    
    class Meta:
        model = CERMembership
        fields = [
            'member_type',
            'role',
            'conformity_declaration',
            'gse_practice',
            'panels_photo',
            'inverter_photo',
            'panels_serial_list'
        ]
        widgets = {
            'member_type': forms.Select(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'panels_serial_list': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Inserire i numeri seriali dei pannelli, uno per riga'
            }),
        }
        help_texts = {
            'member_type': 'Seleziona il tipo di partecipazione nella CER',
            'conformity_declaration': 'Dichiarazione di conformità dell\'impianto (PDF) - Solo per produttori',
            'gse_practice': 'Documentazione GSE completa (PDF) - Solo per produttori',
            'panels_photo': 'Foto dei pannelli installati (JPG/PNG) - Solo per produttori',
            'inverter_photo': 'Foto dell\'inverter installato (JPG/PNG) - Solo per produttori',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Inizialmente nascondi i campi di produzione
        self.fields['conformity_declaration'].required = False
        self.fields['gse_practice'].required = False
        self.fields['panels_photo'].required = False
        self.fields['inverter_photo'].required = False
        self.fields['panels_serial_list'].required = False

    def clean(self):
        cleaned_data = super().clean()
        member_type = cleaned_data.get('member_type')
        
        # Se è un produttore o prosumer, richiedi i documenti
        if member_type in ['PRODUCER', 'PROSUMER']:
            required_docs = ['conformity_declaration', 'gse_practice', 'panels_photo', 'inverter_photo']
            
            for field_name in required_docs:
                if not cleaned_data.get(field_name):
                    self.add_error(field_name, f'Questo documento è obbligatorio per {self.fields["member_type"].choices[member_type]}')
        
        return cleaned_data

    def clean_conformity_declaration(self):
        file = self.cleaned_data.get('conformity_declaration')
        if file and not file.name.endswith('.pdf'):
            raise forms.ValidationError("Il file deve essere in formato PDF")
        return file

class ConsumerMembershipForm(forms.ModelForm):
    """Form semplificato per consumatori senza impianti di produzione"""
    
    class Meta:
        model = CERMembership
        fields = ['role']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Imposta automaticamente come consumatore
        self.fields['role'].initial = 'MEMBER'
        # Limita le scelte del ruolo per i consumatori
        self.fields['role'].choices = [
            ('MEMBER', 'Membro'),
        ]
    
    def save(self, commit=True):
        membership = super().save(commit=False)
        # Imposta automaticamente il tipo come consumatore
        membership.member_type = 'CONSUMER'
        if commit:
            membership.save()
            # Auto-approvazione per consumatori
            membership.auto_approve_consumer()
        return membership

class PlantForm(forms.ModelForm):
    """Form per la gestione degli impianti con supporto dati Gaudì"""
    
    class Meta:
        model = Plant
        fields = [
            'name',
            'pod_code',
            'plant_type',
            'nominal_power',
            'expected_yearly_production',
            'connection_voltage',
            'address',
            'city',
            'province',
            'zip_code',
            'installation_date',
            'validation_date',
            'expected_operation_date'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Nome impianto')
            }),
            'pod_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'IT001E00000000'
            }),
            'plant_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'nominal_power': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': _('kW')
            }),
            'expected_yearly_production': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': _('kWh/anno')
            }),
            'connection_voltage': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '230'
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'province': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'VE'
            }),
            'zip_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '30100'
            }),
            'installation_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'validation_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'expected_operation_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            })
        }
        labels = {
            'name': _('Nome Impianto'),
            'pod_code': _('Codice POD'),
            'plant_type': _('Tipologia'),
            'nominal_power': _('Potenza Nominale (kW)'),
            'expected_yearly_production': _('Produzione Annua Attesa (kWh)'),
            'connection_voltage': _('Tensione di Connessione (V)'),
            'address': _('Indirizzo'),
            'city': _('Città'),
            'province': _('Provincia'),
            'zip_code': _('CAP'),
            'installation_date': _('Data Installazione'),
            'validation_date': _('Data Validazione'),
            'expected_operation_date': _('Data Prevista Esercizio')
        }
        help_texts = {
            'pod_code': _('Codice identificativo del punto di prelievo (14-15 caratteri)'),
            'nominal_power': _('Potenza nominale dell\'impianto in kW'),
            'expected_yearly_production': _('Stima della produzione annuale in kWh'),
            'connection_voltage': _('Tensione di connessione alla rete (default 230V)')
        }

    def __init__(self, *args, from_gaudi=False, **kwargs):
        super().__init__(*args, **kwargs)
        if from_gaudi:
            # Se il form viene usato per impianti da Gaudì, mostra solo il campo tipologia
            for field in list(self.fields.keys()):
                if field != 'plant_type':
                    self.fields[field].widget = forms.HiddenInput()
                    self.fields[field].required = False

    def clean_pod_code(self):
        pod_code = self.cleaned_data.get('pod_code')
        if pod_code:
            pod_code = pod_code.upper()
            if not pod_code.startswith('IT'):
                raise forms.ValidationError(_("Il codice POD deve iniziare con 'IT'"))
            if Plant.objects.filter(pod_code=pod_code).exclude(id=self.instance.id if self.instance else None).exists():
                raise forms.ValidationError(_("Questo codice POD è già in uso"))
        return pod_code

    def clean_nominal_power(self):
        power = self.cleaned_data.get('nominal_power')
        if power and power <= 0:
            raise forms.ValidationError(_("La potenza nominale deve essere maggiore di 0"))
        return power

    def clean_expected_yearly_production(self):
        production = self.cleaned_data.get('expected_yearly_production')
        if production and production < 0:
            raise forms.ValidationError(_("La produzione annua attesa non può essere negativa"))
        return production

    def clean(self):
        cleaned_data = super().clean()
        
        # Validazione date correlate
        expected_operation_date = cleaned_data.get('expected_operation_date')
        validation_date = cleaned_data.get('validation_date')

        if validation_date and expected_operation_date:
            if expected_operation_date < validation_date:
                self.add_error('expected_operation_date', 
                    _("La data prevista di esercizio non può essere anteriore alla data di validazione"))

        return cleaned_data

class PlantMQTTConfigForm(forms.ModelForm):
    """Form per la configurazione MQTT di un impianto"""
    
    mqtt_broker = forms.CharField(
        label=_("Broker MQTT"),
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'mqtt.example.com'
        }),
        help_text=_("Indirizzo del broker MQTT")
    )
    
    mqtt_port = forms.IntegerField(
        label=_("Porta MQTT"),
        required=True,
        initial=1883,
        validators=[MinValueValidator(1)],
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text=_("Porta del broker (1883 standard, 8883 SSL/TLS)")
    )
    
    mqtt_username = forms.CharField(
        label=_("Username MQTT"),
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text=_("Username per l'autenticazione (opzionale)")
    )
    
    mqtt_password = forms.CharField(
        label=_("Password MQTT"),
        max_length=255,
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text=_("Password per l'autenticazione (opzionale)")
    )
    
    mqtt_topic_prefix = forms.CharField(
        label=_("Prefisso Topic"),
        max_length=255,
        initial="cercollettiva",
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text=_("Prefisso per i topic MQTT")
    )
    
    use_ssl = forms.BooleanField(
        label=_("Usa SSL/TLS"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Attiva la connessione sicura SSL/TLS")
    )

    class Meta:
        model = Plant
        fields = [
            'mqtt_broker',
            'mqtt_port',
            'mqtt_username',
            'mqtt_password',
            'mqtt_topic_prefix',
            'use_ssl'
        ]

    def clean(self):
        cleaned_data = super().clean()
        
        # Aggiustamento porta SSL
        if cleaned_data.get('use_ssl') and cleaned_data.get('mqtt_port') == 1883:
            cleaned_data['mqtt_port'] = 8883
        
        # Normalizzazione topic prefix
        topic_prefix = cleaned_data.get('mqtt_topic_prefix', '').strip('/')
        if topic_prefix:
            cleaned_data['mqtt_topic_prefix'] = f"{topic_prefix}/"
        
        # Validazione credenziali
        if cleaned_data.get('mqtt_username') and not cleaned_data.get('mqtt_password'):
            self.add_error('mqtt_password', _('Password richiesta con username'))
        
        return cleaned_data

class GDPRConsentForm(forms.Form):
    """Form per la gestione dei consensi GDPR"""
    
    privacy_policy = forms.BooleanField(
        label=_("Privacy Policy"),
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Ho letto e accetto l'informativa sulla privacy")
    )
    
    data_processing = forms.BooleanField(
        label=_("Trattamento Dati"),
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Acconsento al trattamento dei dati personali")
    )
    
    energy_data_processing = forms.BooleanField(
        label=_("Dati Energetici"),
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Acconsento al trattamento dei dati energetici")
    )
    
    marketing = forms.BooleanField(
        label=_("Marketing"),
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Acconsento all'invio di comunicazioni commerciali")
    )

class InitialGaudiUploadForm(forms.Form):
    """Form per il caricamento iniziale dell'attestato Gaudì"""
    
    gaudi_file = forms.FileField(
        label=_("Attestato Gaudì"),
        required=True,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf'
        }),
        help_text=_("Carica l'attestato Gaudì per precompilare i dati dell'impianto")
    )

    class Meta:
        help_texts = {
            'gaudi_file': _('Il file deve essere in formato PDF')
        }

    def clean_gaudi_file(self):
        file = self.cleaned_data.get('gaudi_file')
        if file:
            if not file.name.endswith('.pdf'):
                raise forms.ValidationError(_("È possibile caricare solo file PDF"))
            if file.size > 10 * 1024 * 1024:  # 10MB
                raise forms.ValidationError(_("Il file non può superare i 10MB"))
        return file

class PlantGaudiUpdateForm(forms.Form):
    """Form per l'aggiornamento di un impianto da attestato Gaudì"""
    
    gaudi_file = forms.FileField(
        label=_("Attestato Gaudì"),
        required=True,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf'
        }),
        help_text=_("Carica l'attestato Gaudì per aggiornare i dati dell'impianto")
    )

    def clean_gaudi_file(self):
        file = self.cleaned_data.get('gaudi_file')
        if file:
            if not file.name.endswith('.pdf'):
                raise forms.ValidationError(_("È possibile caricare solo file PDF"))
            if file.size > 10 * 1024 * 1024:  # 10MB
                raise forms.ValidationError(_("Il file non può superare i 10MB"))
        return file