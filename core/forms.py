# core/forms.py
from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm
from .models import CERConfiguration, CERMembership, Plant, PlantDocument
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field, HTML, Div
from crispy_forms.bootstrap import FormActions

User = get_user_model()


class InitialSuperUserForm(UserCreationForm):
    """
    Form per creare il primo superuser durante il setup iniziale
    """
    username = forms.CharField(
        label="Nome utente",
        max_length=150,
        help_text="Username per l'accesso amministrativo",
        widget=forms.TextInput(attrs={
            'placeholder': 'admin',
            'class': 'form-control'
        })
    )
    
    first_name = forms.CharField(
        label="Nome",
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Mario',
            'class': 'form-control'
        })
    )
    
    last_name = forms.CharField(
        label="Cognome",
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Rossi',
            'class': 'form-control'
        })
    )
    
    email = forms.EmailField(
        label="Email",
        required=True,
        help_text="Email per recupero password e notifiche",
        widget=forms.EmailInput(attrs={
            'placeholder': 'admin@example.com',
            'class': 'form-control'
        })
    )
    
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Password sicura',
            'class': 'form-control'
        }),
        help_text="La password deve essere lunga almeno 8 caratteri"
    )
    
    password2 = forms.CharField(
        label="Conferma password",
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Ripeti la password',
            'class': 'form-control'
        })
    )
    
    # Campo per il nome della CER iniziale
    cer_name = forms.CharField(
        label="Nome CER",
        max_length=255,
        required=True,
        help_text="Nome della Comunità Energetica Rinnovabile",
        widget=forms.TextInput(attrs={
            'placeholder': 'CER Demo',
            'class': 'form-control'
        })
    )
    
    cer_code = forms.CharField(
        label="Codice CER",
        max_length=50,
        required=True,
        help_text="Codice identificativo della CER",
        widget=forms.TextInput(attrs={
            'placeholder': 'CER001',
            'class': 'form-control'
        })
    )
    
    create_demo_cer = forms.BooleanField(
        label="Crea CER di esempio",
        required=False,
        initial=True,
        help_text="Crea automaticamente una CER di esempio per iniziare",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'needs-validation'
        self.helper.attrs = {'novalidate': ''}
        
        self.helper.layout = Layout(
            HTML("""
                <div class="card">
                    <div class="card-header bg-primary text-white">
                        <h4 class="mb-0">
                            <i class="fas fa-user-shield me-2"></i>
                            Setup Iniziale - Amministratore Sistema
                        </h4>
                    </div>
                    <div class="card-body">
                        <div class="alert alert-info">
                            <i class="fas fa-info-circle me-2"></i>
                            Benvenuto! Per iniziare a usare CerCollettiva, crea il primo account amministratore.
                        </div>
            """),
            Row(
                Column(Field('username'), css_class='col-md-6'),
                Column(Field('email'), css_class='col-md-6'),
            ),
            Row(
                Column(Field('first_name'), css_class='col-md-6'),
                Column(Field('last_name'), css_class='col-md-6'),
            ),
            Row(
                Column(Field('password1'), css_class='col-md-6'),
                Column(Field('password2'), css_class='col-md-6'),
            ),
            HTML("""
                        <hr class="my-4">
                        <h5><i class="fas fa-solar-panel me-2"></i>Configurazione CER Iniziale</h5>
            """),
            Field('create_demo_cer'),
            Div(
                Row(
                    Column(Field('cer_name'), css_class='col-md-6'),
                    Column(Field('cer_code'), css_class='col-md-6'),
                ),
                css_id='cer-fields',
                css_class='mt-3'
            ),
            HTML("""
                    </div>
                    <div class="card-footer">
            """),
            FormActions(
                Submit(
                    'submit', 
                    'Crea Amministratore e Avvia Sistema',
                    css_class='btn btn-primary btn-lg w-100'
                )
            ),
            HTML("""
                    </div>
                </div>
                
                <script>
                document.addEventListener('DOMContentLoaded', function() {
                    const createCerCheckbox = document.getElementById('id_create_demo_cer');
                    const cerFields = document.getElementById('cer-fields');
                    
                    function toggleCerFields() {
                        if (createCerCheckbox.checked) {
                            cerFields.style.display = 'block';
                        } else {
                            cerFields.style.display = 'none';
                        }
                    }
                    
                    createCerCheckbox.addEventListener('change', toggleCerFields);
                    toggleCerFields(); // Inizializza lo stato
                });
                </script>
            """)
        )
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Un utente con questa email esiste già.")
        return email
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("Un utente con questo nome utente esiste già.")
        return username
    
    def clean_cer_code(self):
        """Valida il codice CER solo se la creazione CER è abilitata"""
        cer_code = self.cleaned_data.get('cer_code')
        create_demo_cer = self.cleaned_data.get('create_demo_cer')
        
        if create_demo_cer and cer_code:
            if CERConfiguration.objects.filter(code=cer_code).exists():
                raise ValidationError("Una CER con questo codice esiste già.")
        
        return cer_code
    
    def save(self, commit=True):
        """Salva l'utente e crea la CER se richiesto"""
        user = super().save(commit=False)
        
        # Imposta come superuser e staff
        user.is_superuser = True
        user.is_staff = True
        user.is_active = True
        
        # Imposta i campi del CustomUser
        user.legal_type = 'PRIVATE'
        user.profit_type = 'NON_PROFIT'
        
        if commit:
            user.save()
            
            # Crea CER demo se richiesto
            if self.cleaned_data.get('create_demo_cer'):
                cer_name = self.cleaned_data.get('cer_name')
                cer_code = self.cleaned_data.get('cer_code')
                
                if cer_name and cer_code:
                    cer = CERConfiguration.objects.create(
                        name=cer_name,
                        code=cer_code,
                        primary_substation="Substation Demo",
                        is_active=True
                    )
                    
                    # Crea membership per l'admin
                    CERMembership.objects.create(
                        user=user,
                        cer_configuration=cer,
                        role='ADMIN',
                        is_active=True,
                        document_verified=True,
                        document_verified_by=user
                    )
        
        return user


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
    """Form per la gestione dell'adesione a una CER con documenti dinamici"""
    
    # Campi aggiuntivi per tutti
    pod_code = forms.CharField(
        label="Codice POD",
        max_length=15,
        required=False,  # Validazione nel clean()
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'IT001E12345678',
            'data-pod-input': '',  # Per JavaScript lookup
        }),
        help_text="Codice del punto di prelievo (visibile in bolletta) - alternativo all'indirizzo"
    )
    
    address = forms.CharField(
        label="Indirizzo di Fornitura",
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Via Roma 123, Milano, MI',
            'data-address-input': '',  # Per JavaScript lookup
        }),
        help_text="Indirizzo dove hai la fornitura elettrica (alternativo al POD)"
    )
    
    annual_consumption = forms.IntegerField(
        label="Consumo Annuo Stimato (kWh)",
        required=False,
        validators=[MinValueValidator(0)],
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '3000',
            'min': '0'
        }),
        help_text="Consumo elettrico annuo stimato in kWh"
    )
    
    # Campi specifici per produttori
    annual_production = forms.IntegerField(
        label="Produzione Annua Stimata (kWh)",
        required=False,
        validators=[MinValueValidator(0)],
        widget=forms.NumberInput(attrs={
            'class': 'form-control producer-field',
            'placeholder': '5000',
            'min': '0',
            'style': 'display: none;'  # Nascosto inizialmente
        }),
        help_text="Produzione elettrica annua stimata in kWh"
    )
    
    plant_power = forms.DecimalField(
        label="Potenza Impianto (kW)",
        required=False,
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        widget=forms.NumberInput(attrs={
            'class': 'form-control producer-field',
            'placeholder': '6.0',
            'min': '0',
            'step': '0.01',
            'style': 'display: none;'  # Nascosto inizialmente
        }),
        help_text="Potenza nominale dell'impianto fotovoltaico"
    )
    
    installation_date = forms.DateField(
        label="Data Installazione Impianto",
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control producer-field',
            'type': 'date',
            'style': 'display: none;'  # Nascosto inizialmente
        }),
        help_text="Data di installazione dell'impianto fotovoltaico"
    )
    
    # Documenti comuni
    identity_document = forms.FileField(
        label="Documento di Identità",
        required=True,
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png'
        }),
        help_text="Copia documento di identità valido (PDF, JPG, PNG)"
    )
    
    fiscal_code_document = forms.FileField(
        label="Codice Fiscale",
        required=True,
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png'
        }),
        help_text="Copia codice fiscale (PDF, JPG, PNG)"
    )
    
    # Documenti specifici per produttori (inizialmente nascosti)
    gaudi_document = forms.FileField(
        label="Attestato GAUDÌ",
        required=False,
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control producer-field',
            'accept': '.pdf',
            'style': 'display: none;'
        }),
        help_text="Attestato GAUDÌ dell'impianto (PDF) - OBBLIGATORIO per produttori"
    )
    
    plant_authorization = forms.FileField(
        label="Autorizzazione Impianto",
        required=False,
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control producer-field',
            'accept': '.pdf',
            'style': 'display: none;'
        }),
        help_text="Autorizzazione installazione impianto (PDF) - OBBLIGATORIO per produttori"
    )
    
    # Consensi GDPR
    privacy_consent = forms.BooleanField(
        label="Consenso Privacy",
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Accetto l'informativa sulla privacy e autorizzo il trattamento dei dati personali"
    )
    
    data_processing_consent = forms.BooleanField(
        label="Trattamento Dati Energetici",
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Autorizzo il trattamento dei dati di consumo/produzione per la gestione CER"
    )
    
    marketing_consent = forms.BooleanField(
        label="Consenso Marketing",
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Acconsento all'invio di comunicazioni promozionali (facoltativo)"
    )
    
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
            'member_type': forms.Select(attrs={
                'class': 'form-control',
                'id': 'member_type_select'  # Per JavaScript
            }),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'panels_serial_list': forms.Textarea(attrs={
                'class': 'form-control producer-field',
                'rows': 3,
                'placeholder': 'Inserire i numeri seriali dei pannelli, uno per riga',
                'style': 'display: none;'  # Nascosto inizialmente
            }),
            'conformity_declaration': forms.ClearableFileInput(attrs={
                'class': 'form-control producer-field',
                'accept': '.pdf',
                'style': 'display: none;'  # Nascosto inizialmente
            }),
            'gse_practice': forms.ClearableFileInput(attrs={
                'class': 'form-control producer-field',
                'accept': '.pdf',
                'style': 'display: none;'  # Nascosto inizialmente
            }),
            'panels_photo': forms.ClearableFileInput(attrs={
                'class': 'form-control producer-field',
                'accept': 'image/*',
                'style': 'display: none;'  # Nascosto inizialmente
            }),
            'inverter_photo': forms.ClearableFileInput(attrs={
                'class': 'form-control producer-field',
                'accept': 'image/*',
                'style': 'display: none;'  # Nascosto inizialmente
            }),
        }
        help_texts = {
            'member_type': 'Seleziona il tipo di partecipazione nella CER',
            'conformity_declaration': 'Dichiarazione di conformità dell\'impianto (PDF) - OBBLIGATORIO per produttori',
            'gse_practice': 'Documentazione GSE completa (PDF) - OBBLIGATORIO per produttori',
            'panels_photo': 'Foto dei pannelli installati - OBBLIGATORIA per produttori',
            'inverter_photo': 'Foto dell\'inverter installato - OBBLIGATORIA per produttori',
            'panels_serial_list': 'Numeri seriali dei pannelli - OBBLIGATORIO per produttori',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Inizialmente imposta tutti i campi producer come non richiesti
        # La validazione vera avviene nel clean()
        producer_fields = [
            'conformity_declaration', 'gse_practice', 'panels_photo', 
            'inverter_photo', 'panels_serial_list', 'gaudi_document', 
            'plant_authorization', 'annual_production', 'plant_power', 
            'installation_date'
        ]
        
        for field_name in producer_fields:
            if field_name in self.fields:
                self.fields[field_name].required = False

    def clean(self):
        cleaned_data = super().clean()
        member_type = cleaned_data.get('member_type')
        
        # Validazione documenti comuni (sempre richiesti)
        if not cleaned_data.get('identity_document'):
            self.add_error('identity_document', 'Il documento di identità è obbligatorio per tutti i tipi di membri')
        
        if not cleaned_data.get('fiscal_code_document'):
            self.add_error('fiscal_code_document', 'Il codice fiscale è obbligatorio per tutti i tipi di membri')
            
        # Validazione POD code o indirizzo (almeno uno richiesto)
        pod_code = cleaned_data.get('pod_code')
        address = cleaned_data.get('address')
        
        if not pod_code and not address:
            self.add_error('pod_code', 'È necessario fornire il codice POD o l\'indirizzo di fornitura')
            self.add_error('address', 'È necessario fornire il codice POD o l\'indirizzo di fornitura')
        
        # Validazioni specifiche per tipo di membro
        if member_type in ['PRODUCER', 'PROSUMER']:
            # Documenti obbligatori per produttori
            producer_docs = {
                'gaudi_document': 'Attestato GAUDÌ',
                'plant_authorization': 'Autorizzazione impianto',
                'conformity_declaration': 'Dichiarazione di conformità',
                'gse_practice': 'Documentazione GSE',
                'panels_photo': 'Foto dei pannelli',
                'inverter_photo': 'Foto dell\'inverter'
            }
            
            for field_name, field_label in producer_docs.items():
                if not cleaned_data.get(field_name):
                    self.add_error(field_name, f'{field_label} è obbligatorio per {self.get_member_type_label(member_type)}')
            
            # Campi numerici obbligatori per produttori
            if not cleaned_data.get('annual_production'):
                self.add_error('annual_production', 'La produzione annua stimata è obbligatoria per i produttori')
                
            if not cleaned_data.get('plant_power'):
                self.add_error('plant_power', 'La potenza dell\'impianto è obbligatoria per i produttori')
                
            if not cleaned_data.get('installation_date'):
                self.add_error('installation_date', 'La data di installazione è obbligatoria per i produttori')
        
        elif member_type == 'CONSUMER':
            # Per i consumatori, il consumo annuo è utile ma non obbligatorio
            pass
        
        return cleaned_data
        
    def get_member_type_label(self, member_type):
        """Restituisce la label leggibile del tipo di membro"""
        type_labels = {
            'CONSUMER': 'consumatori',
            'PRODUCER': 'produttori', 
            'PROSUMER': 'prosumer'
        }
        return type_labels.get(member_type, member_type.lower())

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

class MembershipFeeForm(forms.Form):
    """Form per la gestione delle quote associative"""
    
    fee_amount = forms.DecimalField(
        label=_("Importo Quota"),
        max_digits=8,
        decimal_places=2,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00',
            'step': '0.01'
        }),
        help_text=_("Importo della quota associativa in euro")
    )
    
    payment_method = forms.ChoiceField(
        label=_("Metodo Pagamento"),
        choices=[
            ('CASH', _('Contanti')),
            ('BANK_TRANSFER', _('Bonifico')),
            ('CARD', _('Carta')),
            ('OTHER', _('Altro'))
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )
    
    notes = forms.CharField(
        label=_("Note"),
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Note aggiuntive sul pagamento...'
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.card = kwargs.pop('card', None)
        super().__init__(*args, **kwargs)
        
        if self.card:
            self.fields['fee_amount'].initial = self.card.fee_amount

class BulkFeeForm(forms.Form):
    """Form per l'impostazione di quote multiple"""
    
    fee_amount = forms.DecimalField(
        label=_("Importo Quota"),
        max_digits=8,
        decimal_places=2,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00',
            'step': '0.01'
        }),
        help_text=_("Importo da applicare a tutti i membri selezionati")
    )
    
    member_type = forms.ChoiceField(
        label=_("Tipologia Membri"),
        choices=[
            ('all', _('Tutti i membri')),
            ('CONSUMER', _('Solo Consumatori')),
            ('PRODUCER', _('Solo Produttori')),
            ('PROSUMER', _('Solo Prosumer'))
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text=_("Seleziona a chi applicare la quota")
    )
    
    apply_to_existing = forms.BooleanField(
        label=_("Sovrascrivi quote esistenti"),
        required=False,
        initial=False,
        help_text=_("Se selezionato, sovrascrive anche le quote già impostate")
    )