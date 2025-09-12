# STORY-04.4: Wizard Configurazione Socio

## 📋 Panoramica

**Epic:** EPIC-04: Sistema di Onboarding CER  
**Sprint:** Sprint 4  
**Priorità:** Alta  
**Stima:** 4-5 giorni  
**Complessità:** Alta  

## 🎯 Obiettivo

Implementare wizard multi-step per configurazione socio con 5 step: tipo socio, POD, impianto, documenti, motivazioni.

## 👤 User Story

**Come** utente con anagrafica completa  
**Voglio** configurare il mio tipo di socio e i miei impianti  
**Per** completare l'adesione alla CER

## ✅ Criteri di Accettazione

### **Wizard Multi-Step**
- [x] Step 1: Scelta tipo socio (Ordinario/Sostenitore)
- [x] Step 2: Dati Punto di Prelievo (POD)
- [x] Step 3: Dettagli impianto fotovoltaico (condizionale)
- [ ] Step 4: Upload documenti (identità, bolletta)
- [x] Step 5: Motivazioni adesione (opzionale)

### **Funzionalità Wizard**
- [x] Navigazione tra step con validazione
- [x] Salvataggio progresso tra step
- [x] Possibilità di tornare indietro
- [x] Indicatore progresso visivo
- [x] Validazione campi per ogni step

### **Upload Documenti**
- [ ] Upload sicuro documenti (identità, bolletta)
- [ ] Validazione tipo e dimensione file
- [ ] Anteprima documenti caricati
- [ ] Gestione errori upload

### **Finalizzazione**
- [x] Aggiornamento `cer_role` e `onboarding_status=ONBOARDING_COMPLETATO`
- [x] Redirect a dashboard completa
- [x] Messaggio di successo
- [x] Log completamento onboarding

## 🔧 Implementazione Tecnica

### **Modelli per Wizard**

```python
# cer/models.py - Aggiungere modelli per wizard
class OnboardingSession(models.Model):
    """Sessione di onboarding per tracciare progresso"""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='onboarding_session'
    )
    
    current_step = models.IntegerField(default=1)
    completed_steps = models.JSONField(default=list)
    session_data = models.JSONField(default=dict)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Onboarding {self.user.username} - Step {self.current_step}"

class POD(models.Model):
    """Punto di Prelievo"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pods')
    pod_code = models.CharField(max_length=20, verbose_name="Codice POD")
    address = models.CharField(max_length=255, verbose_name="Indirizzo")
    utility_company = models.CharField(max_length=100, verbose_name="Fornitore")
    is_production_capable = models.BooleanField(default=False, verbose_name="Capace di Produzione")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.pod_code} - {self.user.username}"

class OnboardingDocument(models.Model):
    """Documenti caricati durante onboarding"""
    
    DOCUMENT_TYPES = [
        ('IDENTITY', 'Documento Identità'),
        ('BILL', 'Bolletta Elettrica'),
        ('OTHER', 'Altro'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='onboarding_documents')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    file = models.FileField(upload_to='onboarding_documents/')
    description = models.CharField(max_length=255, blank=True)
    
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.get_document_type_display()} - {self.user.username}"
```

### **Form per Ogni Step**

```python
# cer/forms.py - Form per wizard
class Step1TypeForm(forms.Form):
    """Step 1: Scelta tipo socio"""
    
    SOCIO_TYPES = [
        ('SOCIO_ORDINARIO', 'Socio Ordinario'),
        ('SOCIO_SOSTENITORE', 'Socio Sostenitore'),
    ]
    
    socio_type = forms.ChoiceField(
        choices=SOCIO_TYPES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label="Tipo di Socio"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['socio_type'].widget.attrs.update({'class': 'form-check-input'})

class Step2PODForm(forms.ModelForm):
    """Step 2: Dati POD"""
    
    class Meta:
        model = POD
        fields = ['pod_code', 'address', 'utility_company', 'is_production_capable']
        widgets = {
            'pod_code': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'utility_company': forms.TextInput(attrs={'class': 'form-control'}),
            'is_production_capable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_pod_code(self):
        pod_code = self.cleaned_data.get('pod_code')
        if not pod_code:
            raise forms.ValidationError('Il codice POD è obbligatorio.')
        return pod_code.upper()

class Step3PlantForm(forms.Form):
    """Step 3: Dettagli impianto (condizionale)"""
    
    plant_type = forms.ChoiceField(
        choices=[
            ('PHOTOVOLTAIC', 'Fotovoltaico'),
            ('WIND', 'Eolico'),
            ('HYDRO', 'Idroelettrico'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Tipo Impianto"
    )
    
    nominal_power = forms.DecimalField(
        max_digits=8,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        label="Potenza Nominale (kW)"
    )
    
    installation_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label="Data Installazione"
    )

class Step4DocumentsForm(forms.Form):
    """Step 4: Upload documenti"""
    
    identity_document = forms.FileField(
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.jpg,.jpeg,.png'}),
        label="Documento Identità",
        help_text="Carica un documento di identità valido (PDF, JPG, PNG)"
    )
    
    electricity_bill = forms.FileField(
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.jpg,.jpeg,.png'}),
        label="Bolletta Elettrica",
        help_text="Carica una bolletta elettrica recente (PDF, JPG, PNG)"
    )
    
    def clean_identity_document(self):
        file = self.cleaned_data.get('identity_document')
        if file:
            if file.size > 5 * 1024 * 1024:  # 5MB
                raise forms.ValidationError('Il file non può superare i 5MB.')
            if not file.content_type.startswith(('image/', 'application/pdf')):
                raise forms.ValidationError('Formato file non supportato.')
        return file
    
    def clean_electricity_bill(self):
        file = self.cleaned_data.get('electricity_bill')
        if file:
            if file.size > 5 * 1024 * 1024:  # 5MB
                raise forms.ValidationError('Il file non può superare i 5MB.')
            if not file.content_type.startswith(('image/', 'application/pdf')):
                raise forms.ValidationError('Formato file non supportato.')
        return file

class Step5MotivationsForm(forms.Form):
    """Step 5: Motivazioni (opzionale)"""
    
    MOTIVATIONS = [
        ('ENVIRONMENTAL', 'Impatto Ambientale'),
        ('ECONOMIC', 'Risparmio Economico'),
        ('COMMUNITY', 'Partecipazione Comunitaria'),
        ('ENERGY_INDEPENDENCE', 'Indipendenza Energetica'),
        ('INNOVATION', 'Innovazione Tecnologica'),
    ]
    
    motivations = forms.MultipleChoiceField(
        choices=MOTIVATIONS,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        label="Motivazioni di Adesione"
    )
    
    additional_notes = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        required=False,
        label="Note Aggiuntive"
    )
```

### **View Wizard**

```python
# cer/views.py - Wizard view
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from .forms import (
    Step1TypeForm, Step2PODForm, Step3PlantForm, 
    Step4DocumentsForm, Step5MotivationsForm
)
from .models import OnboardingSession, POD, OnboardingDocument

@login_required
def onboarding_start(request):
    """Inizia wizard di onboarding"""
    
    if request.user.onboarding_status != 'ANAGRAFICA_COMPLETA':
        messages.warning(request, 'Devi completare l\'anagrafica prima di procedere.')
        return redirect('cer:profile_complete')
    
    # Crea o ottieni sessione onboarding
    session, created = OnboardingSession.objects.get_or_create(user=request.user)
    
    return redirect('cer:onboarding_step', step=1)

@login_required
def onboarding_step(request, step):
    """Gestisce ogni step del wizard"""
    
    if request.user.onboarding_status != 'ANAGRAFICA_COMPLETA':
        messages.warning(request, 'Devi completare l\'anagrafica prima di procedere.')
        return redirect('cer:profile_complete')
    
    # Ottieni sessione onboarding
    try:
        session = OnboardingSession.objects.get(user=request.user)
    except OnboardingSession.DoesNotExist:
        return redirect('cer:onboarding_start')
    
    # Mappa step a form
    step_forms = {
        1: Step1TypeForm,
        2: Step2PODForm,
        3: Step3PlantForm,
        4: Step4DocumentsForm,
        5: Step5MotivationsForm,
    }
    
    if step not in step_forms:
        messages.error(request, 'Step non valido.')
        return redirect('cer:onboarding_start')
    
    form_class = step_forms[step]
    
    if request.method == 'POST':
        form = form_class(request.POST, request.FILES)
        
        if form.is_valid():
            # Salva dati step
            session_data = session.session_data.copy()
            session_data[f'step_{step}'] = form.cleaned_data
            
            # Gestione speciale per step 4 (upload documenti)
            if step == 4:
                # Salva documenti
                if form.cleaned_data.get('identity_document'):
                    OnboardingDocument.objects.create(
                        user=request.user,
                        document_type='IDENTITY',
                        file=form.cleaned_data['identity_document']
                    )
                
                if form.cleaned_data.get('electricity_bill'):
                    OnboardingDocument.objects.create(
                        user=request.user,
                        document_type='BILL',
                        file=form.cleaned_data['electricity_bill']
                    )
            
            # Gestione speciale per step 2 (POD)
            if step == 2:
                pod = form.save(commit=False)
                pod.user = request.user
                pod.save()
            
            # Aggiorna sessione
            session.session_data = session_data
            session.completed_steps = list(set(session.completed_steps + [step]))
            session.current_step = step + 1
            session.save()
            
            # Se è l'ultimo step, finalizza
            if step == 5:
                return finalize_onboarding(request, session)
            
            # Vai al prossimo step
            return redirect('cer:onboarding_step', step=step + 1)
        else:
            messages.error(request, 'Ci sono errori nel form. Controlla i campi evidenziati.')
    else:
        # Carica dati esistenti se disponibili
        initial_data = session.session_data.get(f'step_{step}', {})
        form = form_class(initial=initial_data)
    
    # Calcola progresso
    progress = (step / 5) * 100
    
    context = {
        'form': form,
        'step': step,
        'progress': progress,
        'session': session,
        'can_go_back': step > 1,
        'is_last_step': step == 5,
    }
    
    return render(request, f'cer/wizard/step{step}.html', context)

def finalize_onboarding(request, session):
    """Finalizza il processo di onboarding"""
    
    # Aggiorna ruolo utente
    socio_type = session.session_data.get('step_1', {}).get('socio_type')
    if socio_type:
        request.user.cer_role = socio_type
    
    # Aggiorna stato onboarding
    request.user.onboarding_status = 'ONBOARDING_COMPLETATO'
    request.user.save()
    
    # Elimina sessione onboarding
    session.delete()
    
    messages.success(
        request, 
        f'Congratulazioni! Hai completato l\'adesione come {request.user.get_cer_role_display()}.'
    )
    
    return redirect('core:dashboard')
```

### **Template per Ogni Step**

```html
<!-- cer/templates/cer/wizard/step1.html -->
{% extends 'base.html' %}
{% load static %}

{% block title %}Onboarding - Step 1{% endblock %}

{% block content %}
<div class="container mt-4">
    <div class="row justify-content-center">
        <div class="col-md-8">
            <!-- Progress Bar -->
            <div class="progress mb-4" style="height: 20px;">
                <div class="progress-bar" role="progressbar" style="width: {{ progress }}%">
                    {{ progress|floatformat:0 }}%
                </div>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <h3>Step 1: Scegli il tuo tipo di socio</h3>
                    <p class="text-muted">Seleziona il tipo di partecipazione che preferisci</p>
                </div>
                <div class="card-body">
                    <form method="post">
                        {% csrf_token %}
                        
                        <div class="row">
                            <div class="col-md-6">
                                <div class="card h-100">
                                    <div class="card-body text-center">
                                        <i class="fas fa-users fa-3x text-primary mb-3"></i>
                                        <h5 class="card-title">Socio Ordinario</h5>
                                        <p class="card-text">
                                            Partecipa attivamente alla comunità energetica con impianti di produzione e/o consumo.
                                        </p>
                                        <div class="form-check">
                                            <input class="form-check-input" type="radio" name="socio_type" 
                                                   value="SOCIO_ORDINARIO" id="socio_ordinario">
                                            <label class="form-check-label" for="socio_ordinario">
                                                Scegli Socio Ordinario
                                            </label>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="col-md-6">
                                <div class="card h-100">
                                    <div class="card-body text-center">
                                        <i class="fas fa-heart fa-3x text-success mb-3"></i>
                                        <h5 class="card-title">Socio Sostenitore</h5>
                                        <p class="card-text">
                                            Supporta la comunità energetica senza necessariamente avere impianti propri.
                                        </p>
                                        <div class="form-check">
                                            <input class="form-check-input" type="radio" name="socio_type" 
                                                   value="SOCIO_SOSTENITORE" id="socio_sostenitore">
                                            <label class="form-check-label" for="socio_sostenitore">
                                                Scegli Socio Sostenitore
                                            </label>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="form-group mt-4">
                            <button type="submit" class="btn btn-primary btn-lg">
                                Continua <i class="fas fa-arrow-right ms-2"></i>
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

## 🧪 Testing

### **Test Unitari**
- [ ] Modelli `OnboardingSession`, `POD`, `OnboardingDocument`
- [ ] Form per ogni step del wizard
- [ ] Validazioni upload documenti
- [ ] Logica finalizzazione onboarding

### **Test di Integrazione**
- [ ] Flusso completo wizard 5 step
- [ ] Salvataggio progresso tra step
- [ ] Upload documenti
- [ ] Finalizzazione con aggiornamento ruoli

### **Test E2E**
- [ ] Scenario completo: anagrafica → wizard → dashboard completa
- [ ] Test responsive su mobile e desktop
- [ ] Test accessibilità

## 📊 Metriche di Successo

- [ ] **Performance:** Tempo risposta <3s per step
- [ ] **Upload:** Gestione file fino a 5MB
- [ ] **Completamento:** >80% utenti completano wizard
- [ ] **Accessibilità:** WCAG 2.1 AA compliance

## 🎯 Criteri di Completamento

- [ ] Wizard 5 step implementato
- [ ] Upload documenti funzionante
- [ ] Finalizzazione con aggiornamento ruoli
- [ ] Template responsive e accessibili
- [ ] Test coverage ≥80%
- [ ] Performance ottimizzata

---

**Stato:** 🟡 In Sviluppo  
**Sprint:** Sprint 4  
**Epic:** EPIC-04
