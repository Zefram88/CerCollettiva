# STORY-04.1: Estensione Modello Utente per Onboarding CER

## 📋 Panoramica

**Epic:** EPIC-04: Sistema di Onboarding CER  
**Sprint:** Sprint 1  
**Priorità:** Alta  
**Stima:** 3-5 giorni  
**Complessità:** Media  

## 🎯 Obiettivo

Estendere il modello `CustomUser` con campi per gestire il flusso di onboarding CER e implementare la registrazione minimale per ridurre l'attrito di iscrizione.

## 👤 User Story

**Come** nuovo utente interessato alla CER  
**Voglio** registrarmi rapidamente con solo i dati essenziali  
**Per** iniziare il processo di adesione senza barriere

## ✅ Criteri di Accettazione

### **Estensione Modello Utente**
- [x] Aggiungere campo `cer_role` con scelte: ISCRITTO, SOCIO_ORDINARIO, SOCIO_SOSTENITORE
- [x] Aggiungere campo `onboarding_status` con scelte: REGISTRATO, ANAGRAFICA_COMPLETA, ONBOARDING_COMPLETATO
- [x] Impostare valori di default: `cer_role=ISCRITTO`, `onboarding_status=REGISTRATO`
- [x] Creare migrazione database per nuovi campi
- [x] Mantenere compatibilità con tutti i campi esistenti

### **Registrazione Minimale**
- [x] Creare `MinimalRegistrationForm` con solo: nome, cognome, email, password, privacy
- [x] Validazione email univoca
- [x] Validazione password conforme a standard Django
- [x] Checkbox obbligatoria per accettazione privacy
- [x] Creazione utente con valori di default per nuovi campi
- [x] Login automatico dopo registrazione
- [x] Redirect automatico a `/profilo/completa-anagrafica`

### **Compatibilità Sistema Esistente**
- [x] Tutti i test esistenti continuano a passare
- [x] Form di registrazione esistente rimane funzionante
- [x] Admin interface mostra nuovi campi
- [x] API esistenti non vengono compromesse

## 🔧 Implementazione Tecnica

### **Modifiche `users/models.py`**

```python
# Aggiungere dopo i campi esistenti in CustomUser
class CERRole(models.TextChoices):
    ISCRITTO = 'ISCRITTO', 'Iscritto'
    SOCIO_ORDINARIO = 'SOCIO_ORDINARIO', 'Socio Ordinario'
    SOCIO_SOSTENITORE = 'SOCIO_SOSTENITORE', 'Socio Sostenitore'

class OnboardingStatus(models.TextChoices):
    REGISTRATO = 'REGISTRATO', 'Registrato'
    ANAGRAFICA_COMPLETA = 'ANAGRAFICA_COMPLETA', 'Anagrafica Completa'
    ONBOARDING_COMPLETATO = 'ONBOARDING_COMPLETATO', 'Onboarding Completato'

# Campi da aggiungere alla classe CustomUser
cer_role = models.CharField(
    max_length=20,
    choices=CERRole.choices,
    default=CERRole.ISCRITTO,
    verbose_name="Ruolo CER",
    help_text="Ruolo dell'utente nel sistema CER"
)

onboarding_status = models.CharField(
    max_length=20,
    choices=OnboardingStatus.choices,
    default=OnboardingStatus.REGISTRATO,
    verbose_name="Stato Onboarding",
    help_text="Stato del processo di onboarding CER"
)

# Aggiungere proprietà per gestione stati
@property
def is_iscritto(self):
    """Verifica se l'utente è solo iscritto"""
    return self.cer_role == 'ISCRITTO'

@property
def is_socio_ordinario(self):
    """Verifica se l'utente è socio ordinario"""
    return self.cer_role == 'SOCIO_ORDINARIO'

@property
def is_socio_sostenitore(self):
    """Verifica se l'utente è socio sostenitore"""
    return self.cer_role == 'SOCIO_SOSTENITORE'

@property
def needs_anagrafica(self):
    """Verifica se l'utente deve completare l'anagrafica"""
    return self.onboarding_status == 'REGISTRATO'

@property
def needs_onboarding(self):
    """Verifica se l'utente deve completare l'onboarding"""
    return self.onboarding_status == 'ANAGRAFICA_COMPLETA'

@property
def onboarding_completed(self):
    """Verifica se l'onboarding è completato"""
    return self.onboarding_status == 'ONBOARDING_COMPLETATO'
```

### **Modifiche `users/forms.py`**

```python
# Aggiungere nuovo form per registrazione minimale
class MinimalRegistrationForm(UserCreationForm):
    """Form per registrazione minimale con solo dati essenziali"""
    
    first_name = forms.CharField(
        label=_('Nome'),
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'autocomplete': 'given-name',
            'placeholder': _('Inserisci il tuo nome')
        })
    )
    
    last_name = forms.CharField(
        label=_('Cognome'),
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'autocomplete': 'family-name',
            'placeholder': _('Inserisci il tuo cognome')
        })
    )
    
    email = forms.EmailField(
        label=_('Email'),
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'autocomplete': 'email',
            'placeholder': _('Inserisci la tua email')
        })
    )
    
    privacy_policy = forms.BooleanField(
        label=_('Privacy Policy'),
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Ho letto e accetto l'informativa sulla privacy")
    )
    
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'password1', 'password2', 'privacy_policy']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurazione password
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'autocomplete': 'new-password',
            'placeholder': _('Inserisci una password sicura')
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'autocomplete': 'new-password',
            'placeholder': _('Conferma la password')
        })
        
        # Help text personalizzati
        self.fields['password1'].help_text = _('La password deve contenere almeno 8 caratteri')
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError(_('Un utente con questa email esiste già.'))
        return email
    
    def clean_privacy_policy(self):
        privacy_policy = self.cleaned_data.get('privacy_policy')
        if not privacy_policy:
            raise forms.ValidationError(_('Devi accettare la privacy policy per registrarti.'))
        return privacy_policy
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        # Imposta valori di default per onboarding
        user.cer_role = 'ISCRITTO'
        user.onboarding_status = 'REGISTRATO'
        
        # Imposta privacy
        if self.cleaned_data.get('privacy_policy'):
            user.privacy_accepted = True
            user.privacy_acceptance_date = timezone.now()
        
        if commit:
            user.save()
        return user
```

### **Modifiche `users/views.py`**

```python
# Modificare la view register per supportare registrazione minimale
def register(request):
    """Vista per la registrazione di nuovi utenti"""
    if request.method == 'POST':
        form = MinimalRegistrationForm(request.POST)
        
        if form.is_valid():
            try:
                # Validazione email univoca
                EMAIL_UNIQUE_VALIDATOR(form.cleaned_data['email'])
                
                user = form.save()
                
                # Login automatico
                login(request, user)
                
                logger.info(f"Nuovo utente registrato - Username: {user.username} - Email: {user.email} - Ruolo CER: {user.cer_role} - Stato: {user.onboarding_status}")
                
                messages.success(request, 'Registrazione completata! Completa ora il tuo profilo anagrafico.')
                return redirect('cer:profile_complete')  # Redirect a completamento anagrafico
                
            except ValidationError as e:
                form.add_error('email', str(e))
                messages.error(request, 'Email già esistente.')
        else:
            messages.error(request, 'Ci sono errori nel form. Controlla i campi evidenziati.')
    else:
        form = MinimalRegistrationForm()
        
    context = {
        'form': form,
        'form_errors': form.errors if hasattr(form, 'errors') else None
    }
    return render(request, 'users/register.html', context)
```

### **Migrazione Database**

```python
# users/migrations/0002_add_cer_onboarding_fields.py
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='cer_role',
            field=models.CharField(
                choices=[
                    ('ISCRITTO', 'Iscritto'),
                    ('SOCIO_ORDINARIO', 'Socio Ordinario'),
                    ('SOCIO_SOSTENITORE', 'Socio Sostenitore')
                ],
                default='ISCRITTO',
                help_text='Ruolo dell\'utente nel sistema CER',
                max_length=20,
                verbose_name='Ruolo CER'
            ),
        ),
        migrations.AddField(
            model_name='customuser',
            name='onboarding_status',
            field=models.CharField(
                choices=[
                    ('REGISTRATO', 'Registrato'),
                    ('ANAGRAFICA_COMPLETA', 'Anagrafica Completa'),
                    ('ONBOARDING_COMPLETATO', 'Onboarding Completato')
                ],
                default='REGISTRATO',
                help_text='Stato del processo di onboarding CER',
                max_length=20,
                verbose_name='Stato Onboarding'
            ),
        ),
    ]
```

## 🧪 Testing

### **Test Unitari**

```python
# tests/test_user_model_extension.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()

class CustomUserExtensionTest(TestCase):
    def test_cer_role_default(self):
        """Test che il ruolo CER di default sia ISCRITTO"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        self.assertEqual(user.cer_role, 'ISCRITTO')
    
    def test_onboarding_status_default(self):
        """Test che lo stato onboarding di default sia REGISTRATO"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        self.assertEqual(user.onboarding_status, 'REGISTRATO')
    
    def test_cer_role_properties(self):
        """Test delle proprietà per i ruoli CER"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        
        self.assertTrue(user.is_iscritto)
        self.assertFalse(user.is_socio_ordinario)
        self.assertFalse(user.is_socio_sostenitore)
        
        user.cer_role = 'SOCIO_ORDINARIO'
        user.save()
        
        self.assertFalse(user.is_iscritto)
        self.assertTrue(user.is_socio_ordinario)
        self.assertFalse(user.is_socio_sostenitore)
    
    def test_onboarding_status_properties(self):
        """Test delle proprietà per gli stati onboarding"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        
        self.assertTrue(user.needs_anagrafica)
        self.assertFalse(user.needs_onboarding)
        self.assertFalse(user.onboarding_completed)
        
        user.onboarding_status = 'ANAGRAFICA_COMPLETA'
        user.save()
        
        self.assertFalse(user.needs_anagrafica)
        self.assertTrue(user.needs_onboarding)
        self.assertFalse(user.onboarding_completed)
        
        user.onboarding_status = 'ONBOARDING_COMPLETATO'
        user.save()
        
        self.assertFalse(user.needs_anagrafica)
        self.assertFalse(user.needs_onboarding)
        self.assertTrue(user.onboarding_completed)

# tests/test_minimal_registration_form.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from users.forms import MinimalRegistrationForm

User = get_user_model()

class MinimalRegistrationFormTest(TestCase):
    def test_form_valid_data(self):
        """Test form con dati validi"""
        form_data = {
            'first_name': 'Mario',
            'last_name': 'Rossi',
            'email': 'mario.rossi@example.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
            'privacy_policy': True
        }
        form = MinimalRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_form_creates_user_with_defaults(self):
        """Test che il form crea utente con valori di default"""
        form_data = {
            'first_name': 'Mario',
            'last_name': 'Rossi',
            'email': 'mario.rossi@example.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
            'privacy_policy': True
        }
        form = MinimalRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        user = form.save()
        self.assertEqual(user.cer_role, 'ISCRITTO')
        self.assertEqual(user.onboarding_status, 'REGISTRATO')
        self.assertTrue(user.privacy_accepted)
    
    def test_form_email_validation(self):
        """Test validazione email univoca"""
        # Crea utente esistente
        User.objects.create_user(
            username='existing',
            email='existing@example.com',
            password='TestPass123!'
        )
        
        form_data = {
            'first_name': 'Mario',
            'last_name': 'Rossi',
            'email': 'existing@example.com',  # Email già esistente
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
            'privacy_policy': True
        }
        form = MinimalRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
    
    def test_form_privacy_policy_required(self):
        """Test che privacy policy sia obbligatoria"""
        form_data = {
            'first_name': 'Mario',
            'last_name': 'Rossi',
            'email': 'mario.rossi@example.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
            'privacy_policy': False  # Privacy non accettata
        }
        form = MinimalRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('privacy_policy', form.errors)
```

### **Test di Integrazione**

```python
# tests/test_registration_flow.py
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

class RegistrationFlowTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('users:register')
    
    def test_minimal_registration_flow(self):
        """Test flusso completo di registrazione minimale"""
        form_data = {
            'first_name': 'Mario',
            'last_name': 'Rossi',
            'email': 'mario.rossi@example.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
            'privacy_policy': True
        }
        
        response = self.client.post(self.register_url, form_data)
        
        # Verifica redirect
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('cer:profile_complete'))
        
        # Verifica creazione utente
        user = User.objects.get(email='mario.rossi@example.com')
        self.assertEqual(user.first_name, 'Mario')
        self.assertEqual(user.last_name, 'Rossi')
        self.assertEqual(user.cer_role, 'ISCRITTO')
        self.assertEqual(user.onboarding_status, 'REGISTRATO')
        self.assertTrue(user.privacy_accepted)
        
        # Verifica login automatico
        response = self.client.get(reverse('users:profile'))
        self.assertEqual(response.status_code, 200)
```

## 📊 Metriche di Successo

### **Metriche Tecniche**
- [ ] **Coverage test:** ≥80%
- [ ] **Performance:** Tempo risposta <2s per registrazione
- [ ] **Compatibilità:** Tutti i test esistenti passano
- [ ] **Migrazione:** Database aggiornato senza errori

### **Metriche Business**
- [ ] **Registrazione semplificata:** Form con solo 5 campi
- [ ] **Tasso completamento:** >90% per registrazione minimale
- [ ] **Tempo registrazione:** <2 minuti per completare

## 🔄 Rollback Plan

In caso di problemi:

1. **Rollback migrazione:**
   ```bash
   python manage.py migrate users 0001
   ```

2. **Ripristino form originale:**
   - Ripristinare `UserRegistrationForm` come form di default
   - Rimuovere `MinimalRegistrationForm`

3. **Rollback view:**
   - Ripristinare view `register` originale
   - Rimuovere logica per nuovi campi

## 📚 Documentazione

- [ ] Aggiornare documentazione API per nuovi campi
- [ ] Documentare proprietà del modello `CustomUser`
- [ ] Guida per sviluppatori su nuovi campi
- [ ] Procedure di migrazione per produzione

## 🎯 Criteri di Completamento

- [ ] Tutti i test passano (unit, integration)
- [ ] Coverage test ≥80%
- [ ] Migrazione database eseguita con successo
- [ ] Form registrazione minimale funzionante
- [ ] Login automatico dopo registrazione
- [ ] Redirect a completamento anagrafico
- [ ] Compatibilità con sistema esistente
- [ ] Documentazione aggiornata
- [ ] Review codice approvata

---

**Stato:** ✅ Completato  
**Assegnato a:** Team Sviluppo  
**Sprint:** Sprint 1  
**Epic:** EPIC-04  
**Ultimo Aggiornamento:** 2024-12-19
