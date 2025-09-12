# EPIC-04: Sistema di Onboarding CER

## 📋 Panoramica

**Obiettivo:** Implementare un sistema completo di onboarding per nuovi membri della Comunità Energetica Rinnovabile (CER) con flusso a 3 fasi sequenziali.

**Priorità:** Alta
**Stima:** 3-4 settimane
**Complessità:** Media-Alta

## 🎯 Obiettivi Business

- **Ridurre attrito registrazione:** Processo minimale per acquisire nuovi utenti
- **Raccogliere dati completi:** Profilo anagrafico dettagliato per compliance CER
- **Guidare configurazione:** Wizard assistito per scelta tipo socio e configurazione impianti
- **Migliorare conversione:** Flusso guidato per completare adesione CER

## 🏗️ Architettura Tecnica

### **Modello Utente Esteso**
```python
# users/models.py - Estensione CustomUser
class CustomUser(AbstractUser):
    # Campi esistenti mantenuti...
    
    class CERRole(models.TextChoices):
        ISCRITTO = 'ISCRITTO', 'Iscritto'
        SOCIO_ORDINARIO = 'SOCIO_ORDINARIO', 'Socio Ordinario'
        SOCIO_SOSTENITORE = 'SOCIO_SOSTENITORE', 'Socio Sostenitore'
    
    class OnboardingStatus(models.TextChoices):
        REGISTRATO = 'REGISTRATO', 'Registrato'
        ANAGRAFICA_COMPLETA = 'ANAGRAFICA_COMPLETA', 'Anagrafica Completa'
        ONBOARDING_COMPLETATO = 'ONBOARDING_COMPLETATO', 'Onboarding Completato'
    
    cer_role = models.CharField(
        max_length=20,
        choices=CERRole.choices,
        default=CERRole.ISCRITTO,
        verbose_name="Ruolo CER"
    )
    
    onboarding_status = models.CharField(
        max_length=20,
        choices=OnboardingStatus.choices,
        default=OnboardingStatus.REGISTRATO,
        verbose_name="Stato Onboarding"
    )
```

### **Flusso a 3 Fasi**

#### **Fase 1: Registrazione Minimale**
- **Form:** `MinimalRegistrationForm` (nome, cognome, email, password, privacy)
- **Risultato:** Utente creato con `cer_role=ISCRITTO`, `onboarding_status=REGISTRATO`
- **Redirect:** `/profilo/completa-anagrafica`

#### **Fase 2: Completamento Anagrafico**
- **App:** Nuova app `cer` per gestire profili membro
- **Modello:** `MemberProfile` (OneToOne con CustomUser)
- **Risultato:** `onboarding_status=ANAGRAFICA_COMPLETA`
- **Redirect:** `/dashboard`

#### **Fase 3: Wizard Configurazione Socio**
- **Trigger:** Call-to-action nella dashboard per utenti con `onboarding_status=ANAGRAFICA_COMPLETA`
- **Wizard:** 5 step (tipo socio → POD → impianto → documenti → motivazioni)
- **Risultato:** `cer_role` + `onboarding_status=ONBOARDING_COMPLETATO`

## 📊 User Stories

### **Story 1: Registrazione Minimale**
**Come** nuovo utente  
**Voglio** registrarmi rapidamente con dati essenziali  
**Per** iniziare il processo di adesione alla CER

**Criteri di Accettazione:**
- [ ] Form con solo: nome, cognome, email, password, accettazione privacy
- [ ] Validazione email univoca
- [ ] Creazione utente con `cer_role=ISCRITTO`, `onboarding_status=REGISTRATO`
- [ ] Redirect automatico a completamento anagrafico
- [ ] Login automatico dopo registrazione

### **Story 2: Completamento Profilo Anagrafico**
**Come** utente registrato  
**Voglio** completare i miei dati anagrafici  
**Per** procedere con l'adesione alla CER

**Criteri di Accettazione:**
- [ ] Form per Persona Fisica e Persona Giuridica
- [ ] Validazione campi obbligatori per tipo soggetto
- [ ] Salvataggio in `MemberProfile` (OneToOne con CustomUser)
- [ ] Aggiornamento `onboarding_status=ANAGRAFICA_COMPLETA`
- [ ] Redirect a dashboard con visibilità condizionale

### **Story 3: Dashboard Condizionale**
**Come** utente con anagrafica completa  
**Voglio** vedere una call-to-action per completare l'adesione  
**Per** finalizzare la mia partecipazione alla CER

**Criteri di Accettazione:**
- [ ] Dashboard mostra CTA per `onboarding_status=ANAGRAFICA_COMPLETA`
- [ ] Dashboard completa per `onboarding_status=ONBOARDING_COMPLETATO`
- [ ] Mantenimento logica esistente per admin/staff
- [ ] Template responsive e accessibile

### **Story 4: Wizard Configurazione Socio**
**Come** utente con anagrafica completa  
**Voglio** configurare il mio tipo di socio e i miei impianti  
**Per** completare l'adesione alla CER

**Criteri di Accettazione:**
- [ ] Step 1: Scelta tipo socio (Ordinario/Sostenitore)
- [ ] Step 2: Dati Punto di Prelievo (POD)
- [ ] Step 3: Dettagli impianto fotovoltaico (condizionale)
- [ ] Step 4: Upload documenti (identità, bolletta)
- [ ] Step 5: Motivazioni adesione (opzionale)
- [ ] Aggiornamento `cer_role` e `onboarding_status=ONBOARDING_COMPLETATO`
- [ ] Redirect a dashboard completa

## 🔧 Implementazione Tecnica

### **Modifiche Database**
```sql
-- Migrazione per estendere CustomUser
ALTER TABLE users_customuser 
ADD COLUMN cer_role VARCHAR(20) DEFAULT 'ISCRITTO',
ADD COLUMN onboarding_status VARCHAR(20) DEFAULT 'REGISTRATO';

-- Creazione app cer
CREATE TABLE cer_memberprofile (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE REFERENCES users_customuser(id),
    -- Campi specifici CER...
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### **Struttura App `cer`**
```
cer/
├── __init__.py
├── apps.py
├── models.py          # MemberProfile, OnboardingStep, etc.
├── forms.py           # ProfileForm, WizardForms
├── views.py           # ProfileView, OnboardingWizardView
├── urls.py            # URL patterns per onboarding
├── admin.py           # Admin interface
├── migrations/        # Database migrations
└── templates/         # Template per profilo e wizard
    ├── cer/
    │   ├── profile_complete.html
    │   ├── onboarding_wizard.html
    │   └── wizard/
    │       ├── step1_type.html
    │       ├── step2_pod.html
    │       ├── step3_plant.html
    │       ├── step4_documents.html
    │       └── step5_motivations.html
```

### **Modifiche Sistema Esistente**

#### **users/models.py**
- Aggiungere campi `cer_role` e `onboarding_status`
- Mantenere tutti i campi esistenti
- Aggiungere proprietà per gestione stati

#### **users/forms.py**
- Creare `MinimalRegistrationForm`
- Modificare `UserRegistrationForm` per flusso minimale
- Mantenere validazioni esistenti

#### **users/views.py**
- Modificare `register` view per flusso minimale
- Aggiungere redirect a completamento anagrafico
- Mantenere logica esistente

#### **core/views/dashboard.py**
- Modificare `DashboardView` per visibilità condizionale
- Aggiungere logica per stati onboarding
- Mantenere logica esistente per admin/staff

## 🧪 Testing Strategy

### **Test Unitari**
- [ ] Modello `CustomUser` con nuovi campi
- [ ] Form `MinimalRegistrationForm`
- [ ] Form `MemberProfileForm`
- [ ] Wizard forms per ogni step
- [ ] Validazioni campi obbligatori

### **Test di Integrazione**
- [ ] Flusso completo registrazione → anagrafica → wizard
- [ ] Dashboard condizionale per diversi stati
- [ ] Redirect e navigazione tra fasi
- [ ] Upload documenti

### **Test E2E**
- [ ] Scenario completo: nuovo utente → socio completo
- [ ] Test su diversi tipi di soggetto (fisica/giuridica)
- [ ] Test responsive su mobile/desktop
- [ ] Test accessibilità

## 📈 Metriche di Successo

### **Metriche Business**
- **Tasso di completamento registrazione:** >80%
- **Tempo medio completamento onboarding:** <15 minuti
- **Tasso di abbandono per fase:** <20% per fase
- **Soddisfazione utente:** >4.0/5.0

### **Metriche Tecniche**
- **Coverage test:** ≥80%
- **Performance:** Tempo risposta <2s per step
- **Accessibilità:** WCAG 2.1 AA compliance
- **Compatibilità:** Supporto browser moderni

## 🚀 Piano di Implementazione

### **Sprint 1: Estensione Modello Utente**
- [ ] Estendere `CustomUser` con campi onboarding
- [ ] Creare migrazione database
- [ ] Implementare `MinimalRegistrationForm`
- [ ] Test unitari per nuovi campi

### **Sprint 2: App CER e Profilo Anagrafico**
- [ ] Creare app `cer`
- [ ] Implementare modello `MemberProfile`
- [ ] Creare form per completamento anagrafico
- [ ] Implementare view e template

### **Sprint 3: Dashboard Condizionale**
- [ ] Modificare `DashboardView` per visibilità condizionale
- [ ] Implementare template condizionali
- [ ] Test integrazione con sistema esistente
- [ ] Test responsive e accessibilità

### **Sprint 4: Wizard Configurazione Socio**
- [ ] Implementare wizard multi-step
- [ ] Creare form per ogni step
- [ ] Implementare upload documenti
- [ ] Test E2E completo

## 🔒 Considerazioni di Sicurezza

- **Validazione input:** Tutti i form con validazione server-side
- **Upload sicuro:** Validazione tipo e dimensione file
- **Autorizzazione:** Controllo accessi per ogni fase
- **GDPR:** Gestione consensi e dati personali
- **Audit trail:** Log delle modifiche stato utente

## 📚 Documentazione

- [ ] Documentazione API per endpoint onboarding
- [ ] Guida utente per processo di adesione
- [ ] Documentazione tecnica per sviluppatori
- [ ] Procedure di rollback per migrazioni

## 🎯 Criteri di Completamento

- [ ] Tutti i test passano (unit, integration, E2E)
- [ ] Coverage test ≥80%
- [ ] Performance requirements soddisfatti
- [ ] Accessibilità WCAG 2.1 AA
- [ ] Documentazione completa
- [ ] Review codice approvata
- [ ] Deploy in ambiente di staging
- [ ] Test utente completati con successo

---

**Stato:** 🟡 In Progettazione  
**Ultimo Aggiornamento:** 2024-12-19  
**Responsabile:** Team Sviluppo  
**Stakeholder:** Product Owner, Business Analyst
