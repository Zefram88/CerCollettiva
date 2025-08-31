# users/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from .models import CustomUser
from django.contrib.auth import get_user_model


User = get_user_model()

class UserLoginForm(forms.Form):
    """Form per il login degli utenti"""
    username = forms.CharField(
        label=_('Username'),
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': _('Nome utente'),
            'autocomplete': 'username'
        })
    )
    password = forms.CharField(
        label=_('Password'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control', 
            'placeholder': _('Password'),
            'autocomplete': 'current-password'
        })
    )

class UserRegistrationForm(UserCreationForm):
    """Form personalizzato per la registrazione degli utenti con GDPR"""
    LEGAL_TYPES = [
        ('PRIVATE', _('Privato')),
        ('BUSINESS', _('Azienda')),
        ('ASSOCIATION', _('Associazione')),
        ('CHURCH', _('Ente Religioso')),
        ('PUBLIC', _('Ente Pubblico')),
    ]
    
    PROFIT_TYPES = [
        ('PROFIT', _('Con scopo di lucro')),
        ('NON_PROFIT', _('Senza scopo di lucro')),
    ]

    # Campi base
    username = forms.CharField(
        label=_('Username'),
        help_text=_('Richiesto. 150 caratteri o meno. Solo lettere, numeri e @/./+/-/_'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'autocomplete': 'username'
        })
    )
    
    email = forms.EmailField(
        label=_('Email'),
        required=True,
        help_text=_('Inserisci un indirizzo email valido'),
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'autocomplete': 'email'
        })
    )

    # Campi tipologia
    legal_type = forms.ChoiceField(
        label=_('Tipo Soggetto'),
        choices=LEGAL_TYPES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    profit_type = forms.ChoiceField(
        label=_('Finalità'),
        choices=PROFIT_TYPES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    # Dati anagrafici/fiscali
    fiscal_code = forms.CharField(
        label=_('Codice Fiscale'),
        max_length=16,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'autocomplete': 'off'
        })
    )
    
    phone = forms.CharField(
        label=_('Telefono'),
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': '+39',
            'autocomplete': 'tel'
        })
    )
    
    address = forms.CharField(
        label=_('Indirizzo'),
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'autocomplete': 'street-address'
        })
    )

    # Campi per aziende/enti
    legal_name = forms.CharField(
        label=_('Denominazione'),
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'autocomplete': 'organization'
        })
    )
    
    vat_number = forms.CharField(
        label=_('Partita IVA'),
        max_length=11,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'autocomplete': 'off'
        })
    )
    
    pec = forms.EmailField(
        label=_('PEC'),
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'autocomplete': 'email'
        })
    )

    # Consensi GDPR
    privacy_policy = forms.BooleanField(
        label=_('Privacy Policy'),
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Ho letto e accetto l'informativa sulla privacy")
    )
    
    data_processing = forms.BooleanField(
        label=_('Trattamento Dati'),
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_('Acconsento al trattamento dei dati personali')
    )

    #privacy_accepted = forms.BooleanField(required=True, label="Accetto la privacy policy")

    first_name = forms.CharField(
        label=_('Nome'),
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'autocomplete': 'given-name'
        })
    )
    
    last_name = forms.CharField(
        label=_('Cognome'),
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'autocomplete': 'family-name'
        })
    )

    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name',  # Prima nome e cognome
            'username', 'email',  # Poi le credenziali di accesso
            'legal_type', 'profit_type',  # Poi i tipi
            'legal_name','address', 'phone',  # Dati personaliS
            'fiscal_code', 'vat_number', 'pec', 'sdi_code',  # Dati fiscali
            'registration_number', 'statute_date',  # Dati associazione
            'religious_entity_code',  # Dati enti religiosi
            'password1', 'password2',  # Password alla fine
            'privacy_policy', 'data_processing'  # Consensi GDPR
        ]
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Rendi il campo profit_type non richiesto perché verrà gestito automaticamente
        self.fields['profit_type'].required = False
       
        # Se c'è già un legal_type impostato e è PRIVATE, disabilita profit_type
        if self.data.get('legal_type') == 'PRIVATE':
            self.fields['profit_type'].disabled = True
            self.fields['profit_type'].initial = 'NON_PROFIT'

        # Configurazione password
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control password-input',
            'autocomplete': 'new-password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control password-input',
            'autocomplete': 'new-password'
        })
        
        # Help text personalizzati
        self.fields['password1'].help_text = _('La password deve contenere almeno 8 caratteri')
        self.fields['fiscal_code'].help_text = _('Codice fiscale (16 caratteri)')
        
        # Aggiornamento campi richiesti se c'è legal_type nei dati
        if self.data.get('legal_type'):
            self._update_required_fields(self.data.get('legal_type'))

    def clean_fiscal_code(self):
        fiscal_code = self.cleaned_data.get('fiscal_code')
        legal_type = self.cleaned_data.get('legal_type')
        
        if not fiscal_code:
            raise forms.ValidationError(_('Il codice fiscale è obbligatorio'))
            
        fiscal_code = fiscal_code.upper()
        
        if legal_type == 'PRIVATE':
            # Per persone fisiche: 16 caratteri alfanumerici
            if len(fiscal_code) != 16:
                raise forms.ValidationError(_('Il codice fiscale per persone fisiche deve essere di 16 caratteri'))
            # Qui potresti aggiungere ulteriori validazioni per il formato del codice fiscale
        elif legal_type in ['BUSINESS', 'ASSOCIATION', 'PUBLIC']:
            # Per aziende e altri soggetti: 11 caratteri numerici
            if len(fiscal_code) != 11:
                raise forms.ValidationError(_('Il codice fiscale per aziende deve essere di 11 caratteri numerici'))
            if not fiscal_code.isdigit():
                raise forms.ValidationError(_('Il codice fiscale per aziende deve contenere solo numeri'))

        return fiscal_code

    def clean_vat_number(self):
        vat_number = self.cleaned_data.get('vat_number')
        legal_type = self.cleaned_data.get('legal_type')
        
        if legal_type in ['BUSINESS', 'ASSOCIATION'] and not vat_number:
            raise forms.ValidationError(_('La Partita IVA è obbligatoria'))
        
        if vat_number and len(vat_number) != 11:
            raise forms.ValidationError(_('La Partita IVA deve essere di 11 cifre'))
        
        return vat_number

    def clean_privacy_policy(self):
        privacy_policy = self.cleaned_data.get('privacy_policy')
        if not privacy_policy:
            raise forms.ValidationError(_('Devi accettare la privacy policy per registrarti.'))
        return privacy_policy

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
        # Se non è privato ma manca profit_type, solleva errore
        elif not cleaned_data.get('profit_type'):
            raise ValidationError({
                'profit_type': 'Questo campo è obbligatorio per i soggetti non privati.'
            })

        return cleaned_data

    def _update_required_fields(self, legal_type):
        """Aggiorna i campi richiesti in base al tipo di soggetto"""
        if legal_type in ['BUSINESS', 'ASSOCIATION']:
            self.fields['vat_number'].required = True
            self.fields['pec'].required = True
            self.fields['legal_name'].required = True
        elif legal_type in ['PUBLIC', 'CHURCH']:
            self.fields['legal_name'].required = True

class UserUpdateForm(forms.ModelForm):
    """Form per l'aggiornamento del profilo utente"""
    
    class Meta:
        model = CustomUser
        fields = [
            'first_name',
            'last_name',
            'email',
            'phone',
            'address'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Nome')
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Cognome')
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': _('Email')
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('+39...')
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Indirizzo completo')
            })
        }

def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Rendi il campo profit_type non richiesto perché verrà gestito automaticamente
        self.fields['profit_type'].required = False
       
        # Se c'è già un legal_type impostato, gestisci profit_type e help text di conseguenza
        if self.data.get('legal_type') == 'PRIVATE':
            self.fields['profit_type'].disabled = True
            self.fields['profit_type'].initial = 'NON_PROFIT'
            self.fields['fiscal_code'].help_text = _('Codice fiscale persona fisica (16 caratteri)')
        elif self.data.get('legal_type') in ['BUSINESS', 'ASSOCIATION', 'PUBLIC']:
            self.fields['profit_type'].disabled = True
            self.fields['profit_type'].initial = 'PROFIT'
            self.fields['fiscal_code'].help_text = _('Codice fiscale/Partita IVA (11 caratteri numerici)')
        else:
            self.fields['fiscal_code'].help_text = _('Codice fiscale')

        # Configurazione password
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
        
        # Altri help text personalizzati
        self.fields['password1'].help_text = _('La password deve contenere almeno 8 caratteri')
        self.fields['first_name'].help_text = _('Inserisci il tuo nome')
        self.fields['last_name'].help_text = _('Inserisci il tuo cognome')
        
        # Aggiornamento campi richiesti se c'è legal_type nei dati
        if self.data.get('legal_type'):
            self._update_required_fields(self.data.get('legal_type'))

class BusinessProfileForm(forms.ModelForm):
    """Form per l'aggiornamento dei dati aziendali"""
    
    class Meta:
        model = CustomUser
        fields = [
            'legal_name',
            'vat_number',
            'pec',
            'fiscal_code',
            'email',
            'sdi_code',
        ]
        widgets = {
            'legal_name': forms.TextInput(attrs={'class': 'form-control'}),
            'vat_number': forms.TextInput(attrs={'class': 'form-control'}),
            'pec': forms.EmailInput(attrs={'class': 'form-control'}),
            'fiscal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'sdi_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Codice SDI',
                'maxlength': '7'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Rendi obbligatori i campi necessari per le aziende
        self.fields['legal_name'].required = True
        self.fields['vat_number'].required = True
        self.fields['pec'].required = True
        self.fields['fiscal_code'].required = True
        
        # Aggiungi help text
        self.fields['vat_number'].help_text = 'Inserisci la partita IVA (11 caratteri)'
        self.fields['pec'].help_text = 'Inserisci l\'indirizzo PEC aziendale'

    def clean_vat_number(self):
        """Validazione partita IVA"""
        vat_number = self.cleaned_data.get('vat_number')
        if vat_number and len(vat_number) != 11:
            raise forms.ValidationError(_('La partita IVA deve essere di 11 caratteri'))
        return vat_number
    
    def privacy_policy(request):
        #Vista per mostrare la privacy policy
        return render(request, 'users/privacy_policy.html')

class PrivateProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = [
            'first_name',
            'last_name',
            'fiscal_code',
            'email',
            'phone',
        ]
        
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'fiscal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Rendi obbligatori i campi necessari per i privati
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['fiscal_code'].required = True

class UserProfileForm(forms.ModelForm):
    """Form unificato per la modifica del profilo"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Rendi tutti i campi bootstrap-friendly
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
        
        # Aggiungi/rimuovi campi in base al tipo di utente
        user = kwargs.get('instance')
        if user:
            if user.is_private:
                self.fields['first_name'].required = True
                self.fields['last_name'].required = True
            else:  # Per business e altri tipi
                self.fields['legal_name'].required = True
                self.fields['vat_number'].required = True
                self.fields['pec'].required = True

    class Meta:
        model = CustomUser
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'legal_type', 'fiscal_code', 'phone', 'address',
            'legal_name', 'vat_number', 'pec', 'sdi_code'
        ]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'legal_type': forms.Select(attrs={'class': 'form-control'}),
            'fiscal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'legal_name': forms.TextInput(attrs={'class': 'form-control'}),
            'vat_number': forms.TextInput(attrs={'class': 'form-control'}),
            'pec': forms.EmailInput(attrs={'class': 'form-control'}),
            'sdi_code': forms.TextInput(attrs={'class': 'form-control'})
        }

class RegistrationForm(forms.ModelForm):
    privacy_acceptance = forms.BooleanField(
        required=True,
        label="Accetto la Privacy Policy",
        error_messages={
            'required': 'È necessario accettare la Privacy Policy per procedere'
        }
    )

    def save(self, commit=True):
        user = super().save(commit=False)
        # Imposta i campi della privacy se è stata accettata
        if self.cleaned_data.get('privacy_policy'):
            user.privacy_accepted = True
            user.privacy_acceptance_date = timezone.now()
        if commit:
            user.save()
        return user