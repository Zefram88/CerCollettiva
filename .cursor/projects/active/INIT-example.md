# Esempio Comando INIT

## Prompt Utente
```
INIT Sistema di Gestione Documenti CER

CONTESTO:
- Sistema per gestire documenti CER (Comunità Energetiche Rinnovabili)
- Integrazione con database PostgreSQL esistente
- API REST per frontend React
- Conformità normative ARERA e ADE

REQUISITI:
- Upload documenti PDF con validazione formato
- Classificazione automatica per tipologia (contratti, bollette, certificati)
- Workflow approvazione multi-livello
- Generazione report conformità
- Notifiche email per scadenze

METRICHE:
- Performance: API response p95 ≤ 200ms
- Coverage: Test coverage ≥ 85%
- SLA: Disponibilità ≥ 99.9%

GATE EPIC:
- Tutti i documenti caricati correttamente classificati
- Workflow approvazione funzionante end-to-end
- Report conformità generati automaticamente
- Performance target rispettati
```

## Output Atteso INIT

```
✅ EPIC-002-sistema-gestione-documenti-cer.mdc creato
✅ Cartella EPIC-002-sistema-gestione-documenti-cer/ creata
✅ S001-upload-classificazione-documenti.mdc creata
✅ S002-workflow-approvazione.mdc creata
✅ S003-generazione-report-conformita.mdc creata
✅ S004-notifiche-scadenze.mdc creata
✅ logs/ cartella creata
✅ active/ links creati
✅ DoR validato: 12 requisiti soddisfatti

Struttura creata:
.cursor/projects/
├── EPIC-002-sistema-gestione-documenti-cer.mdc
├── EPIC-002-sistema-gestione-documenti-cer/
│   ├── S001-upload-classificazione-documenti.mdc
│   ├── S002-workflow-approvazione.mdc
│   ├── S003-generazione-report-conformita.mdc
│   ├── S004-notifiche-scadenze.mdc
│   └── logs/
└── active/
    ├── current-epic -> ../EPIC-002-sistema-gestione-documenti-cer.mdc
    ├── current-story -> ../EPIC-002-sistema-gestione-documenti-cer/S001-upload-classificazione-documenti.mdc
    └── checkpoint-20241206-140522.mdc
```

## Processo Automatico

1. **Analisi prompt** (2-3 min):
   - Estrae 5 requisiti funzionali
   - Identifica 3 vincoli tecnici
   - Rileva 4 metriche di performance

2. **Generazione EPIC** (3-4 min):
   - Crea EPIC con DoR completo
   - Definisce Gate EPIC misurabile
   - Imposta metriche e SLA

3. **Story Mapping** (4-5 min):
   - S001: Upload e classificazione (3 file, 120 LOC)
   - S002: Workflow approvazione (4 file, 150 LOC)
   - S003: Report conformità (3 file, 100 LOC)
   - S004: Notifiche scadenze (2 file, 80 LOC)

4. **Creazione struttura** (2-3 min):
   - File EPIC principale
   - Cartella EPIC con Stories
   - Links attivi per lavoro corrente

5. **Validazione DoR** (1-2 min):
   - Verifica tutti i requisiti coperti
   - Controlla metriche definite
   - Valida Gate EPIC misurabile

## Vantaggi

✅ **Struttura completa**: EPIC + Stories + organizzazione
✅ **DoR validato**: Tutti i requisiti coperti
✅ **Metriche definite**: Performance e coverage target
✅ **Pronto per lavoro**: Links attivi e checkpoint
✅ **Governance integrata**: WIP limits e verifiche automatiche

