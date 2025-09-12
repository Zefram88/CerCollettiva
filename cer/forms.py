# cer/forms.py
from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from .models import MemberProfile
from core.main_models import CERConfiguration, CERMembership, Plant
from users.models import CustomUser


class OnboardingStep0Form(forms.Form):
    """Step 0: Selezione tipo di membro CER"""
    
    MEMBER_ROLE_CHOICES = [
        ('PRODUCER', _('Produttore')),
        ('CONSUMER', _('Consumer')),
        ('PROSUMER', _('Prosumer')),
        ('SUPPORTER', _('Sostenitori')),
    ]
    
    member_role = forms.ChoiceField(
        label=_('Tipo di Membro CER'),
        choices=MEMBER_ROLE_CHOICES,
        required=True,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        help_text=_('Seleziona il tipo di membro che vuoi diventare nella CER')
    )
    
    def clean_member_role(self):
        """Validazione tipo membro"""
        member_role = self.cleaned_data.get('member_role')
        if not member_role:
            raise ValidationError(_('Devi selezionare un tipo di membro.'))
        return member_role


class OnboardingStep1Form(forms.ModelForm):
    """Step 1: Verifica e correzione dati anagrafici"""
    
    class Meta:
        model = CustomUser
        fields = [
            'legal_type', 'profit_type', 'fiscal_code',
            'first_name', 'last_name', 'phone', 'address',
            'vat_number', 'legal_name', 'pec', 'sdi_code',
            'registration_number', 'statute_date', 'religious_entity_code'
        ]
        widgets = {
            'legal_type': forms.Select(attrs={'class': 'form-control'}),
            'profit_type': forms.Select(attrs={'class': 'form-control'}),
            'fiscal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'vat_number': forms.TextInput(attrs={'class': 'form-control'}),
            'legal_name': forms.TextInput(attrs={'class': 'form-control'}),
            'pec': forms.EmailInput(attrs={'class': 'form-control'}),
            'sdi_code': forms.TextInput(attrs={'class': 'form-control'}),
            'registration_number': forms.TextInput(attrs={'class': 'form-control'}),
            'statute_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'religious_entity_code': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Imposta label personalizzate
        self.fields['legal_type'].label = _('Tipo di Soggetto')
        self.fields['profit_type'].label = _('Finalità')
        self.fields['fiscal_code'].label = _('Codice Fiscale')
        self.fields['first_name'].label = _('Nome')
        self.fields['last_name'].label = _('Cognome')
        self.fields['phone'].label = _('Telefono')
        self.fields['address'].label = _('Indirizzo')
        self.fields['vat_number'].label = _('Partita IVA')
        self.fields['legal_name'].label = _('Denominazione')
        self.fields['pec'].label = _('PEC')
        self.fields['sdi_code'].label = _('Codice SDI')
        self.fields['registration_number'].label = _('Numero Registrazione')
        self.fields['statute_date'].label = _('Data Statuto')
        self.fields['religious_entity_code'].label = _('Codice Ente Religioso')
        
        # Aggiungi help text
        self.fields['legal_type'].help_text = _('Verifica il tipo di soggetto selezionato')
        self.fields['profit_type'].help_text = _('Verifica la finalità del soggetto')
        self.fields['fiscal_code'].help_text = _('Verifica il codice fiscale')
        self.fields['first_name'].help_text = _('Verifica il nome')
        self.fields['last_name'].help_text = _('Verifica il cognome')
        self.fields['phone'].help_text = _('Verifica il numero di telefono')
        self.fields['address'].help_text = _('Verifica l\'indirizzo')
        
        # Rendi i campi condizionali in base al tipo di soggetto
        if self.instance and self.instance.legal_type:
            self._update_required_fields(self.instance.legal_type)
    
    def _update_required_fields(self, legal_type):
        """Aggiorna i campi richiesti in base al tipo di soggetto"""
        if legal_type in ['BUSINESS', 'ASSOCIATION']:
            self.fields['vat_number'].required = True
            self.fields['pec'].required = True
            self.fields['legal_name'].required = True
        elif legal_type in ['PUBLIC', 'CHURCH']:
            self.fields['legal_name'].required = True
        elif legal_type == 'PRIVATE':
            self.fields['first_name'].required = True
            self.fields['last_name'].required = True
    
    def clean(self):
        cleaned_data = super().clean()
        legal_type = cleaned_data.get('legal_type')
        
        if legal_type == 'PRIVATE':
            cleaned_data['profit_type'] = 'NON_PROFIT'
            if not cleaned_data.get('first_name'):
                self.add_error('first_name', _('Il nome è obbligatorio per gli utenti privati'))
            if not cleaned_data.get('last_name'):
                self.add_error('last_name', _('Il cognome è obbligatorio per gli utenti privati'))
        elif legal_type in ['BUSINESS', 'ASSOCIATION']:
            if not cleaned_data.get('vat_number'):
                self.add_error('vat_number', _('La Partita IVA è obbligatoria'))
            if not cleaned_data.get('pec'):
                self.add_error('pec', _('La PEC è obbligatoria'))
            if not cleaned_data.get('legal_name'):
                self.add_error('legal_name', _('La denominazione è obbligatoria'))
        
        return cleaned_data


class OnboardingStep2Form(forms.Form):
    """Step 2: Validazione POD e iscrizione alla CER"""
    
    pod_code = forms.CharField(
        label=_('Codice POD'),
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('IT001E12345678'),
            'autocomplete': 'off',
            'id': 'id_pod_code'
        }),
        help_text=_('Codice del Punto di Prelievo (POD) della tua utenza elettrica (14-15 caratteri)')
    )
    
    pod_address = forms.CharField(
        label=_('Indirizzo POD'),
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Via Roma 123, Milano'),
            'autocomplete': 'street-address'
        }),
        help_text=_('Indirizzo del punto di prelievo')
    )
    
    def clean_pod_code(self):
        """Validazione del codice POD"""
        pod_code = self.cleaned_data.get('pod_code', '').strip().upper()
        if not pod_code:
            raise ValidationError(_('Il codice POD è obbligatorio'))
        
        # Validazione formato base (IT + 12-13 caratteri alfanumerici)
        if not pod_code.startswith('IT'):
            raise ValidationError(_('Il codice POD deve iniziare con "IT"'))
        
        if len(pod_code) < 14 or len(pod_code) > 15:
            raise ValidationError(_('Il codice POD deve avere 14-15 caratteri totali'))
        
        # Verifica caratteri validi (lettere e numeri)
        import re
        if not re.match(r'^IT[A-Z0-9]+$', pod_code):
            raise ValidationError(_('Il codice POD può contenere solo lettere e numeri'))
        
        return pod_code


class OnboardingStep3Form(forms.Form):
    """Step 3: Dettagli impianto fotovoltaico (condizionale)"""
    
    has_plant = forms.BooleanField(
        label=_('Hai un impianto fotovoltaico?'),
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_('Seleziona se possiedi un impianto di produzione di energia rinnovabile')
    )
    
    plant_power = forms.DecimalField(
        label=_('Potenza Impianto (kW)'),
        max_digits=8,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '3.0',
            'step': '0.1',
            'min': '0'
        }),
        help_text=_('Potenza nominale dell\'impianto in kilowatt')
    )
    
    plant_installation_date = forms.DateField(
        label=_('Data Installazione'),
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        help_text=_('Data di installazione dell\'impianto')
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # I campi impianto sono condizionali
        self.fields['plant_power'].widget.attrs['disabled'] = True
        self.fields['plant_installation_date'].widget.attrs['disabled'] = True
    
    def clean(self):
        cleaned_data = super().clean()
        has_plant = cleaned_data.get('has_plant')
        
        if has_plant:
            # Se ha impianto, i campi sono obbligatori
            if not cleaned_data.get('plant_power'):
                self.add_error('plant_power', _('La potenza dell\'impianto è obbligatoria'))
            if not cleaned_data.get('plant_installation_date'):
                self.add_error('plant_installation_date', _('La data di installazione è obbligatoria'))
        
        return cleaned_data


class OnboardingStep4Form(forms.Form):
    """Step 4: Upload documenti"""
    
    identity_document = forms.FileField(
        label=_('Documento di Identità'),
        required=True,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png'
        }),
        help_text=_('Carica una copia del tuo documento di identità (PDF, JPG, PNG)')
    )
    
    electricity_bill = forms.FileField(
        label=_('Bolletta Elettrica'),
        required=True,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png'
        }),
        help_text=_('Carica una copia della tua ultima bolletta elettrica')
    )
    
    def clean_identity_document(self):
        """Validazione documento identità"""
        file = self.cleaned_data.get('identity_document')
        if file:
            # Validazione dimensione (max 5MB)
            if file.size > 5 * 1024 * 1024:
                raise ValidationError(_('Il file non può superare i 5MB'))
            
            # Validazione tipo file
            allowed_types = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png']
            if file.content_type not in allowed_types:
                raise ValidationError(_('Formato file non supportato. Usa PDF, JPG o PNG'))
        
        return file
    
    def clean_electricity_bill(self):
        """Validazione bolletta elettrica"""
        file = self.cleaned_data.get('electricity_bill')
        if file:
            # Validazione dimensione (max 5MB)
            if file.size > 5 * 1024 * 1024:
                raise ValidationError(_('Il file non può superare i 5MB'))
            
            # Validazione tipo file
            allowed_types = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png']
            if file.content_type not in allowed_types:
                raise ValidationError(_('Formato file non supportato. Usa PDF, JPG o PNG'))
        
        return file


class OnboardingStep5Form(forms.Form):
    """Step 5: Motivazioni adesione (opzionale)"""
    
    motivation = forms.CharField(
        label=_('Motivazioni Adesione'),
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': _('Descrivi brevemente perché vuoi aderire alla CER...')
        }),
        help_text=_('Condividi le tue motivazioni per aderire alla Comunità Energetica (opzionale)')
    )
    
    newsletter_consent = forms.BooleanField(
        label=_('Consenso Newsletter'),
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_('Desidero ricevere aggiornamenti sulla CER via email')
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['motivation'].widget.attrs.update({'maxlength': '500'})


class ProfileCompletionForm(forms.ModelForm):
    """Form per il completamento del profilo anagrafico"""
    
    # Selezione tipo soggetto
    legal_type = forms.ChoiceField(
        label=_('Tipo di Soggetto'),
        choices=[
            ('PRIVATE', _('Persona Fisica')),
            ('BUSINESS', _('Azienda')),
            ('ASSOCIATION', _('Associazione')),
            ('CHURCH', _('Ente Religioso')),
            ('PUBLIC', _('Ente Pubblico')),
        ],
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'id_legal_type',
            'onchange': 'toggleFields()'
        }),
        help_text=_('Seleziona il tipo di soggetto per visualizzare i campi appropriati')
    )
    
    class Meta:
        model = MemberProfile
        fields = [
            'fiscal_code', 'phone', 'address', 'city', 'zip_code', 'province',
            'vat_number', 'legal_name', 'pec', 'sdi_code'
        ]
        widgets = {
            'fiscal_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'es. RSSMRA80A01H501U'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'es. +39 123 456 7890'
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Via Roma 123'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Milano'
            }),
            'zip_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '20100'
            }),
            'province': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'MI',
                'maxlength': '2'
            }),
            'vat_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '12345678901'
            }),
            'legal_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Denominazione azienda'
            }),
            'pec': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'azienda@pec.it'
            }),
            'sdi_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'ABCDEFG',
                'maxlength': '7'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Imposta valore iniziale per legal_type se disponibile
        if self.user and hasattr(self.user, 'legal_type'):
            self.fields['legal_type'].initial = self.user.legal_type
        
        # Imposta campi obbligatori in base al tipo di utente
        if self.user and self.user.legal_type == 'PRIVATE':
            self._setup_private_fields()
        elif self.user and self.user.legal_type in ['BUSINESS', 'ASSOCIATION']:
            self._setup_business_fields()
        elif self.user and self.user.legal_type == 'PUBLIC':
            self._setup_public_fields()
        else:
            # Default: mostra tutti i campi ma non obbligatori
            self._setup_default_fields()
    
    def _setup_private_fields(self):
        """Configura campi per persona fisica"""
        self.fields['fiscal_code'].required = True
        self.fields['phone'].required = True
        self.fields['address'].required = True
        self.fields['city'].required = True
        self.fields['zip_code'].required = True
        self.fields['province'].required = True
        
        # Nascondi campi per aziende
        self.fields['vat_number'].widget = forms.HiddenInput()
        self.fields['legal_name'].widget = forms.HiddenInput()
        self.fields['pec'].widget = forms.HiddenInput()
        self.fields['sdi_code'].widget = forms.HiddenInput()
    
    def _setup_business_fields(self):
        """Configura campi per azienda/associazione"""
        self.fields['vat_number'].required = True
        self.fields['legal_name'].required = True
        self.fields['pec'].required = True
        self.fields['fiscal_code'].required = True
        self.fields['phone'].required = True
        self.fields['address'].required = True
        self.fields['city'].required = True
        self.fields['zip_code'].required = True
        self.fields['province'].required = True
    
    def _setup_public_fields(self):
        """Configura campi per ente pubblico"""
        self.fields['legal_name'].required = True
        self.fields['phone'].required = True
        self.fields['address'].required = True
        self.fields['city'].required = True
        self.fields['zip_code'].required = True
        self.fields['province'].required = True
        
        # Nascondi campi per aziende
        self.fields['vat_number'].widget = forms.HiddenInput()
        self.fields['fiscal_code'].widget = forms.HiddenInput()
        self.fields['pec'].widget = forms.HiddenInput()
        self.fields['sdi_code'].widget = forms.HiddenInput()
    
    def _setup_default_fields(self):
        """Configura campi di default (tutti visibili ma non obbligatori)"""
        pass
    
    def clean_fiscal_code(self):
        fiscal_code = self.cleaned_data.get('fiscal_code')
        if fiscal_code and self.user and self.user.legal_type == 'PRIVATE':
            if len(fiscal_code) != 16:
                raise forms.ValidationError(_('Il codice fiscale per persone fisiche deve essere di 16 caratteri.'))
        return fiscal_code
    
    def clean_vat_number(self):
        vat_number = self.cleaned_data.get('vat_number')
        if vat_number and len(vat_number) != 11:
            raise forms.ValidationError(_('La partita IVA deve essere di 11 caratteri numerici.'))
        return vat_number
    
    def clean_province(self):
        province = self.cleaned_data.get('province')
        if province and len(province) != 2:
            raise forms.ValidationError(_('La provincia deve essere di 2 caratteri (es. MI, RM).'))
        return province.upper() if province else province
    
    def clean(self):
        """Validazione campi obbligatori in base al tipo di soggetto"""
        cleaned_data = super().clean()
        legal_type = self.user.legal_type if self.user else None
        
        if legal_type in ['BUSINESS', 'ASSOCIATION', 'CHURCH', 'PUBLIC']:
            # Per aziende, associazioni, enti religiosi e pubblici
            if not cleaned_data.get('vat_number'):
                self.add_error('vat_number', _('La partita IVA è obbligatoria per questo tipo di soggetto'))
            if not cleaned_data.get('legal_name'):
                self.add_error('legal_name', _('La denominazione è obbligatoria per questo tipo di soggetto'))
            if not cleaned_data.get('pec'):
                self.add_error('pec', _('La PEC è obbligatoria per questo tipo di soggetto'))
        
        return cleaned_data
