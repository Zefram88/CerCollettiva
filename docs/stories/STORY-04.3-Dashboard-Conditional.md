# STORY-04.3: Dashboard Condizionale

## 📋 Panoramica

**Epic:** EPIC-04: Sistema di Onboarding CER  
**Sprint:** Sprint 3  
**Priorità:** Alta  
**Stima:** 2-3 giorni  
**Complessità:** Media  

## 🎯 Obiettivo

Modificare la dashboard per mostrare visibilità condizionale basata sullo stato di onboarding dell'utente.

## 👤 User Story

**Come** utente con anagrafica completa  
**Voglio** vedere una call-to-action per completare l'adesione  
**Per** finalizzare la mia partecipazione alla CER

## ✅ Criteri di Accettazione

### **Dashboard Condizionale**
- [ ] Dashboard mostra CTA per `onboarding_status=ANAGRAFICA_COMPLETA`
- [ ] Dashboard completa per `onboarding_status=ONBOARDING_COMPLETATO`
- [ ] Mantenimento logica esistente per admin/staff
- [ ] Template responsive e accessibile

### **Call-to-Action**
- [ ] Banner prominente con messaggio "Completa la tua adesione"
- [ ] Pulsante "Inizia Onboarding" che porta al wizard
- [ ] Design accattivante e chiaro
- [ ] Responsive su mobile e desktop

### **Compatibilità**
- [ ] Mantenere funzionalità esistenti per admin
- [ ] Mantenere funzionalità esistenti per staff
- [ ] Non compromettere performance esistenti
- [ ] Test di regressione passano

## 🔧 Implementazione Tecnica

### **Modifiche `core/views/dashboard.py`**

```python
# Aggiungere logica condizionale alla DashboardView
def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    user = self.request.user
    
    # Logica esistente per admin/staff
    is_global_admin = user.is_staff or user.is_superuser
    
    # NUOVA LOGICA: Visibilità basata su onboarding_status
    if user.onboarding_status == 'ANAGRAFICA_COMPLETA':
        context['show_onboarding_cta'] = True
        context['onboarding_url'] = reverse('cer:onboarding_start')
        context['onboarding_message'] = 'Completa la tua adesione e scegli che tipo di membro essere'
    elif user.onboarding_status == 'ONBOARDING_COMPLETATO':
        context['show_full_dashboard'] = True
    elif user.onboarding_status == 'REGISTRATO':
        context['show_anagrafica_cta'] = True
        context['anagrafica_url'] = reverse('cer:profile_complete')
        context['anagrafica_message'] = 'Completa il tuo profilo anagrafico per procedere'
    
    # Mantenere logica esistente per admin
    if is_global_admin:
        # ... logica esistente per admin ...
        pass
    
    return context
```

### **Modifiche Template Dashboard**

```html
<!-- core/templates/core/dashboard.html -->
{% extends 'base.html' %}
{% load static %}

{% block title %}Dashboard{% endblock %}

{% block content %}
<div class="container-fluid">
    <!-- CTA per completamento anagrafica -->
    {% if show_anagrafica_cta %}
    <div class="row mb-4">
        <div class="col-12">
            <div class="alert alert-info alert-dismissible fade show" role="alert">
                <div class="d-flex align-items-center">
                    <i class="fas fa-user-plus fa-2x me-3"></i>
                    <div class="flex-grow-1">
                        <h4 class="alert-heading mb-1">Completa il tuo profilo</h4>
                        <p class="mb-2">{{ anagrafica_message }}</p>
                        <a href="{{ anagrafica_url }}" class="btn btn-primary btn-lg">
                            <i class="fas fa-arrow-right me-2"></i>Completa Profilo
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </div>
    {% endif %}
    
    <!-- CTA per onboarding -->
    {% if show_onboarding_cta %}
    <div class="row mb-4">
        <div class="col-12">
            <div class="card border-primary">
                <div class="card-body text-center py-5">
                    <div class="row align-items-center">
                        <div class="col-md-8">
                            <h2 class="card-title text-primary mb-3">
                                <i class="fas fa-rocket me-2"></i>
                                Completa la tua adesione alla CER
                            </h2>
                            <p class="card-text lead mb-4">
                                {{ onboarding_message }}
                            </p>
                            <p class="text-muted">
                                Il processo richiede solo pochi minuti e ti permetterà di:
                            </p>
                            <ul class="list-unstyled text-start d-inline-block">
                                <li><i class="fas fa-check text-success me-2"></i>Scegliere il tuo tipo di socio</li>
                                <li><i class="fas fa-check text-success me-2"></i>Configurare i tuoi impianti</li>
                                <li><i class="fas fa-check text-success me-2"></i>Caricare i documenti necessari</li>
                                <li><i class="fas fa-check text-success me-2"></i>Accedere a tutte le funzionalità</li>
                            </ul>
                        </div>
                        <div class="col-md-4">
                            <div class="text-center">
                                <i class="fas fa-users fa-5x text-primary mb-3"></i>
                                <br>
                                <a href="{{ onboarding_url }}" class="btn btn-primary btn-lg px-5">
                                    <i class="fas fa-play me-2"></i>Inizia Onboarding
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    {% endif %}
    
    <!-- Dashboard completa -->
    {% if show_full_dashboard %}
    <div class="row">
        <div class="col-12">
            <h1 class="h3 mb-4">Dashboard CER</h1>
            
            <!-- Statistiche utente -->
            <div class="row mb-4">
                <div class="col-md-3">
                    <div class="card bg-primary text-white">
                        <div class="card-body">
                            <div class="d-flex justify-content-between">
                                <div>
                                    <h4 class="card-title">{{ user.get_cer_role_display }}</h4>
                                    <p class="card-text">Tipo di Socio</p>
                                </div>
                                <div class="align-self-center">
                                    <i class="fas fa-user-tag fa-2x"></i>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-3">
                    <div class="card bg-success text-white">
                        <div class="card-body">
                            <div class="d-flex justify-content-between">
                                <div>
                                    <h4 class="card-title">{{ plants.count }}</h4>
                                    <p class="card-text">Impianti</p>
                                </div>
                                <div class="align-self-center">
                                    <i class="fas fa-solar-panel fa-2x"></i>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-3">
                    <div class="card bg-info text-white">
                        <div class="card-body">
                            <div class="d-flex justify-content-between">
                                <div>
                                    <h4 class="card-title">{{ energy_stats.total_power }} kW</h4>
                                    <p class="card-text">Potenza Totale</p>
                                </div>
                                <div class="align-self-center">
                                    <i class="fas fa-bolt fa-2x"></i>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-3">
                    <div class="card bg-warning text-white">
                        <div class="card-body">
                            <div class="d-flex justify-content-between">
                                <div>
                                    <h4 class="card-title">{{ energy_stats.today_energy }} kWh</h4>
                                    <p class="card-text">Energia Oggi</p>
                                </div>
                                <div class="align-self-center">
                                    <i class="fas fa-chart-line fa-2x"></i>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Contenuto dashboard esistente -->
            <!-- ... resto del contenuto dashboard ... -->
        </div>
    </div>
    {% endif %}
    
    <!-- Dashboard semplificata per utenti in onboarding -->
    {% if not show_full_dashboard and not show_onboarding_cta and not show_anagrafica_cta %}
    <div class="row">
        <div class="col-12">
            <div class="text-center py-5">
                <i class="fas fa-cog fa-spin fa-3x text-muted mb-3"></i>
                <h3 class="text-muted">Configurazione in corso...</h3>
                <p class="text-muted">Stiamo preparando la tua dashboard personalizzata.</p>
            </div>
        </div>
    </div>
    {% endif %}
</div>
{% endblock %}
```

### **CSS Aggiuntivo**

```css
/* static/css/dashboard.css */
.onboarding-cta {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border: none;
    color: white;
}

.onboarding-cta:hover {
    background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%);
    color: white;
    transform: translateY(-2px);
    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
}

.cta-card {
    transition: all 0.3s ease;
}

.cta-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 10px 25px rgba(0,0,0,0.15);
}

@media (max-width: 768px) {
    .onboarding-cta .row {
        text-align: center;
    }
    
    .onboarding-cta .col-md-4 {
        margin-top: 2rem;
    }
}
```

## 🧪 Testing

### **Test Unitari**
```python
# tests/test_dashboard_conditional.py
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()

class DashboardConditionalTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
    
    def test_dashboard_anagrafica_cta(self):
        """Test CTA per completamento anagrafica"""
        self.user.onboarding_status = 'REGISTRATO'
        self.user.save()
        
        self.client.login(username='testuser', password='TestPass123!')
        response = self.client.get(reverse('core:dashboard'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Completa il tuo profilo')
        self.assertContains(response, 'anagrafica_cta')
    
    def test_dashboard_onboarding_cta(self):
        """Test CTA per onboarding"""
        self.user.onboarding_status = 'ANAGRAFICA_COMPLETA'
        self.user.save()
        
        self.client.login(username='testuser', password='TestPass123!')
        response = self.client.get(reverse('core:dashboard'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Completa la tua adesione')
        self.assertContains(response, 'onboarding_cta')
    
    def test_dashboard_full_view(self):
        """Test dashboard completa"""
        self.user.onboarding_status = 'ONBOARDING_COMPLETATO'
        self.user.cer_role = 'SOCIO_ORDINARIO'
        self.user.save()
        
        self.client.login(username='testuser', password='TestPass123!')
        response = self.client.get(reverse('core:dashboard'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'show_full_dashboard')
        self.assertContains(response, 'Socio Ordinario')
```

### **Test di Integrazione**
- [ ] Flusso completo: registrazione → anagrafica → dashboard CTA → onboarding
- [ ] Responsive design su mobile e desktop
- [ ] Accessibilità WCAG 2.1 AA

## 📊 Metriche di Successo

- [ ] **Performance:** Tempo risposta <2s
- [ ] **Accessibilità:** WCAG 2.1 AA compliance
- [ ] **Responsive:** Funziona su mobile e desktop
- [ ] **Compatibilità:** Test di regressione passano

## 🎯 Criteri di Completamento

- [ ] Dashboard condizionale implementata
- [ ] CTA per onboarding funzionante
- [ ] Template responsive e accessibile
- [ ] Mantenimento funzionalità esistenti
- [ ] Test coverage ≥80%
- [ ] Performance mantenuta

---

**Stato:** ✅ Completato  
**Sprint:** Sprint 3  
**Epic:** EPIC-04
