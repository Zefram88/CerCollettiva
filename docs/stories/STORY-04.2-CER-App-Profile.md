# STORY-04.2: App CER e Profilo Anagrafico

## 📋 Panoramica

**Epic:** EPIC-04: Sistema di Onboarding CER  
**Sprint:** Sprint 2  
**Priorità:** Alta  
**Stima:** 3-5 giorni  
**Complessità:** Media  

## 🎯 Obiettivo

Creare l'app Django `cer` e implementare il completamento del profilo anagrafico per utenti con stato `REGISTRATO`.

## 👤 User Story

**Come** utente appena registrato  
**Voglio** completare i miei dati anagrafici  
**Per** procedere con l'adesione alla CER

## ✅ Criteri di Accettazione

### **Creazione App CER**
- [x] Creare app Django `cer` con struttura completa
- [x] Configurare `cer` in `INSTALLED_APPS`
- [x] Creare URL patterns per app `cer`
- [x] Configurare admin interface per app `cer`

### **Modello MemberProfile**
- [x] Creare modello `MemberProfile` (OneToOne con CustomUser)
- [x] Campi per Persona Fisica: nome, cognome, codice fiscale, indirizzo, telefono
- [x] Campi per Persona Giuridica: denominazione, partita IVA, PEC, codice SDI
- [x] Validazioni specifiche per tipo soggetto
- [x] Creare migrazione database

### **Form Completamento Anagrafico**
- [x] Form dinamico che si adatta al tipo di soggetto
- [x] Validazione campi obbligatori per Persona Fisica
- [x] Validazione campi obbligatori per Persona Giuridica
- [x] Validazione codice fiscale e partita IVA
- [x] Gestione errori e messaggi utente

### **View e Template**
- [x] View per completamento profilo anagrafico
- [x] Template responsive per form anagrafico
- [x] Gestione redirect dopo salvataggio
- [x] Aggiornamento `onboarding_status=ANAGRAFICA_COMPLETA`

## 🔧 Implementazione Tecnica

### **Struttura App CER**
```
cer/
├── __init__.py
├── apps.py
├── models.py
├── forms.py
├── views.py
├── urls.py
├── admin.py
├── migrations/
└── templates/
    └── cer/
        ├── profile_complete.html
        └── base.html
```

### **Modello MemberProfile**
```python
# cer/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()

class MemberProfile(models.Model):
    """Profilo anagrafico membro CER"""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='member_profile',
        verbose_name="Utente"
    )
    
    # Campi comuni
    fiscal_code = models.CharField(
        max_length=16,
        verbose_name="Codice Fiscale",
        help_text="16 caratteri per persona fisica, 11 per persona giuridica"
    )
    
    address = models.CharField(
        max_length=255,
        verbose_name="Indirizzo"
    )
    
    phone = models.CharField(
        max_length=20,
        verbose_name="Telefono"
    )
    
    # Campi per Persona Giuridica
    legal_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Denominazione"
    )
    
    vat_number = models.CharField(
        max_length=11,
        blank=True,
        null=True,
        verbose_name="Partita IVA"
    )
    
    pec = models.EmailField(
        blank=True,
        null=True,
        verbose_name="PEC"
    )
    
    sdi_code = models.CharField(
        max_length=7,
        blank=True,
        null=True,
        verbose_name="Codice SDI"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def clean(self):
        super().clean()
        
        # Validazioni per tipo soggetto
        if self.user.legal_type == 'PRIVATE':
            if not all([self.user.first_name, self.user.last_name]):
                raise ValidationError('Nome e cognome sono obbligatori per persone fisiche.')
        elif self.user.legal_type in ['BUSINESS', 'ASSOCIATION']:
            if not all([self.legal_name, self.vat_number, self.pec]):
                raise ValidationError('Denominazione, Partita IVA e PEC sono obbligatori per aziende e associazioni.')
    
    def __str__(self):
        if self.legal_name:
            return f"{self.legal_name} - {self.user.get_full_name()}"
        return f"{self.user.get_full_name()}"
    
    class Meta:
        verbose_name = "Profilo Membro CER"
        verbose_name_plural = "Profili Membri CER"
```

### **Form Completamento Anagrafico**
```python
# cer/forms.py
from django import forms
from django.contrib.auth import get_user_model
from .models import MemberProfile

User = get_user_model()

class MemberProfileForm(forms.ModelForm):
    """Form per completamento profilo anagrafico"""
    
    class Meta:
        model = MemberProfile
        fields = [
            'fiscal_code', 'address', 'phone',
            'legal_name', 'vat_number', 'pec', 'sdi_code'
        ]
        widgets = {
            'fiscal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'legal_name': forms.TextInput(attrs={'class': 'form-control'}),
            'vat_number': forms.TextInput(attrs={'class': 'form-control'}),
            'pec': forms.EmailInput(attrs={'class': 'form-control'}),
            'sdi_code': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Configura campi in base al tipo di soggetto
        if self.user and self.user.legal_type == 'PRIVATE':
            self.fields['legal_name'].required = False
            self.fields['vat_number'].required = False
            self.fields['pec'].required = False
            self.fields['sdi_code'].required = False
        elif self.user and self.user.legal_type in ['BUSINESS', 'ASSOCIATION']:
            self.fields['legal_name'].required = True
            self.fields['vat_number'].required = True
            self.fields['pec'].required = True
            self.fields['sdi_code'].required = False
    
    def clean_fiscal_code(self):
        fiscal_code = self.cleaned_data.get('fiscal_code')
        if not fiscal_code:
            raise forms.ValidationError('Il codice fiscale è obbligatorio.')
        
        fiscal_code = fiscal_code.upper()
        
        if self.user.legal_type == 'PRIVATE':
            if len(fiscal_code) != 16:
                raise forms.ValidationError('Il codice fiscale per persone fisiche deve essere di 16 caratteri.')
        elif self.user.legal_type in ['BUSINESS', 'ASSOCIATION']:
            if len(fiscal_code) != 11:
                raise forms.ValidationError('Il codice fiscale per aziende deve essere di 11 caratteri numerici.')
            if not fiscal_code.isdigit():
                raise forms.ValidationError('Il codice fiscale per aziende deve contenere solo numeri.')
        
        return fiscal_code
    
    def clean_vat_number(self):
        vat_number = self.cleaned_data.get('vat_number')
        
        if self.user.legal_type in ['BUSINESS', 'ASSOCIATION'] and not vat_number:
            raise forms.ValidationError('La Partita IVA è obbligatoria per aziende e associazioni.')
        
        if vat_number and len(vat_number) != 11:
            raise forms.ValidationError('La Partita IVA deve essere di 11 cifre.')
        
        return vat_number
```

### **View Completamento Profilo**
```python
# cer/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from .forms import MemberProfileForm
from .models import MemberProfile

User = get_user_model()

@login_required
def profile_complete(request):
    """View per completamento profilo anagrafico"""
    
    # Verifica che l'utente sia nello stato corretto
    if request.user.onboarding_status != 'REGISTRATO':
        messages.warning(request, 'Il tuo profilo è già stato completato.')
        return redirect('core:dashboard')
    
    # Ottieni o crea il profilo
    profile, created = MemberProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = MemberProfileForm(request.POST, instance=profile, user=request.user)
        
        if form.is_valid():
            form.save()
            
            # Aggiorna stato onboarding
            request.user.onboarding_status = 'ANAGRAFICA_COMPLETA'
            request.user.save()
            
            messages.success(request, 'Profilo anagrafico completato con successo!')
            return redirect('core:dashboard')
        else:
            messages.error(request, 'Ci sono errori nel form. Controlla i campi evidenziati.')
    else:
        form = MemberProfileForm(instance=profile, user=request.user)
    
    context = {
        'form': form,
        'user': request.user,
        'profile': profile,
        'is_private': request.user.legal_type == 'PRIVATE',
        'is_business': request.user.legal_type in ['BUSINESS', 'ASSOCIATION']
    }
    
    return render(request, 'cer/profile_complete.html', context)
```

### **URL Patterns**
```python
# cer/urls.py
from django.urls import path
from . import views

app_name = 'cer'

urlpatterns = [
    path('profilo/completa-anagrafica/', views.profile_complete, name='profile_complete'),
]
```

### **Template**
```html
<!-- cer/templates/cer/profile_complete.html -->
{% extends 'base.html' %}
{% load static %}

{% block title %}Completa Profilo Anagrafico{% endblock %}

{% block content %}
<div class="container mt-4">
    <div class="row justify-content-center">
        <div class="col-md-8">
            <div class="card">
                <div class="card-header">
                    <h3>Completa il tuo profilo anagrafico</h3>
                    <p class="text-muted">Inserisci i tuoi dati per procedere con l'adesione alla CER</p>
                </div>
                <div class="card-body">
                    <form method="post">
                        {% csrf_token %}
                        
                        <div class="row">
                            <div class="col-md-6">
                                <div class="form-group">
                                    <label for="{{ form.fiscal_code.id_for_label }}">Codice Fiscale</label>
                                    {{ form.fiscal_code }}
                                    {% if form.fiscal_code.errors %}
                                        <div class="text-danger">{{ form.fiscal_code.errors }}</div>
                                    {% endif %}
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="form-group">
                                    <label for="{{ form.phone.id_for_label }}">Telefono</label>
                                    {{ form.phone }}
                                    {% if form.phone.errors %}
                                        <div class="text-danger">{{ form.phone.errors }}</div>
                                    {% endif %}
                                </div>
                            </div>
                        </div>
                        
                        <div class="form-group">
                            <label for="{{ form.address.id_for_label }}">Indirizzo</label>
                            {{ form.address }}
                            {% if form.address.errors %}
                                <div class="text-danger">{{ form.address.errors }}</div>
                            {% endif %}
                        </div>
                        
                        {% if is_business %}
                        <hr>
                        <h5>Dati Aziendali</h5>
                        <div class="row">
                            <div class="col-md-6">
                                <div class="form-group">
                                    <label for="{{ form.legal_name.id_for_label }}">Denominazione</label>
                                    {{ form.legal_name }}
                                    {% if form.legal_name.errors %}
                                        <div class="text-danger">{{ form.legal_name.errors }}</div>
                                    {% endif %}
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="form-group">
                                    <label for="{{ form.vat_number.id_for_label }}">Partita IVA</label>
                                    {{ form.vat_number }}
                                    {% if form.vat_number.errors %}
                                        <div class="text-danger">{{ form.vat_number.errors }}</div>
                                    {% endif %}
                                </div>
                            </div>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-6">
                                <div class="form-group">
                                    <label for="{{ form.pec.id_for_label }}">PEC</label>
                                    {{ form.pec }}
                                    {% if form.pec.errors %}
                                        <div class="text-danger">{{ form.pec.errors }}</div>
                                    {% endif %}
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="form-group">
                                    <label for="{{ form.sdi_code.id_for_label }}">Codice SDI</label>
                                    {{ form.sdi_code }}
                                    {% if form.sdi_code.errors %}
                                        <div class="text-danger">{{ form.sdi_code.errors }}</div>
                                    {% endif %}
                                </div>
                            </div>
                        </div>
                        {% endif %}
                        
                        <div class="form-group mt-4">
                            <button type="submit" class="btn btn-primary btn-lg">
                                Completa Profilo
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
- [ ] Modello `MemberProfile` con validazioni
- [ ] Form `MemberProfileForm` con validazioni per tipo soggetto
- [ ] View `profile_complete` con logica di stato

### **Test di Integrazione**
- [ ] Flusso completo: registrazione → completamento anagrafico
- [ ] Aggiornamento stato onboarding
- [ ] Redirect a dashboard

## 📊 Metriche di Successo

- [ ] **Coverage test:** ≥80%
- [ ] **Performance:** Tempo risposta <2s
- [ ] **Tasso completamento:** >85% per anagrafica
- [ ] **Validazione:** Campi obbligatori per tipo soggetto

## 🎯 Criteri di Completamento

- [ ] App `cer` creata e configurata
- [ ] Modello `MemberProfile` implementato
- [ ] Form anagrafico funzionante
- [ ] View e template completati
- [ ] Aggiornamento stato onboarding
- [ ] Test coverage ≥80%
- [ ] Documentazione aggiornata

---

**Stato:** ✅ Completato  
**Sprint:** Sprint 2  
**Epic:** EPIC-04
