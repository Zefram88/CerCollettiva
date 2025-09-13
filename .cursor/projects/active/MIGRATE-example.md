# Esempio Comando MIGRATE

## Prompt Utente
```
MIGRATE energy/
```

## Output Atteso MIGRATE

```
✅ Analisi codebase completata: 47 file, 3,247 LOC
✅ Componenti identificati: 
   - API REST (8 file)
   - Modelli Django (7 file)
   - MQTT handlers (10 file)
   - Templates (14 file)
   - Test (8 file)
✅ EPIC-003-migration-energy-app.mdc creato
✅ S001-refactor-api-validation.mdc creata
✅ S002-consolidate-mqtt-handlers.mdc creata
✅ S003-improve-test-coverage.mdc creata
✅ S004-optimize-database-queries.mdc creata
✅ Piano migrazione: 4 Story, 12 Slice, 6 settimane

Problemi identificati:
❌ Coverage test: 45% (target: ≥80%)
❌ Duplicazioni: 3 pattern di validazione API
❌ Performance: 2 query N+1 in views
❌ Architettura: MQTT handlers accoppiati
```

## Processo Automatico

1. **Analisi codebase** (5-7 min):
   - Scansione 47 file in energy/
   - Analisi dipendenze e architettura
   - Identificazione pattern e anti-pattern

2. **Identificazione componenti** (3-4 min):
   - API REST: 8 file, 1,200 LOC
   - Modelli: 7 file, 800 LOC
   - MQTT: 10 file, 600 LOC
   - Templates: 14 file, 400 LOC
   - Test: 8 file, 247 LOC

3. **Mappatura a Stories** (4-5 min):
   - S001: Refactor validazione API (duplicazioni)
   - S002: Consolidamento MQTT handlers (accoppiamento)
   - S003: Miglioramento test coverage (45% → 80%)
   - S004: Ottimizzazione query database (N+1)

4. **Creazione EPIC** (2-3 min):
   - EPIC di migrazione con stato attuale
   - Piano di standardizzazione
   - Metriche di miglioramento

5. **Piano migrazione** (3-4 min):
   - Roadmap 6 settimane
   - Priorità per impatto/rischio
   - Dipendenze tra Story

## Criteri di Analisi MIGRATE

### Identificazione Duplicazioni
```python
# Pattern 1: Validazione API (3 occorrenze)
def validate_device_data(data):
    if not data.get('name'):
        raise ValidationError("Name required")
    # ... duplicato in 3 file

# Pattern 2: MQTT message handling (2 occorrenze)
def handle_mqtt_message(topic, payload):
    # ... logica duplicata
```

### Rilevamento Violazioni
- **Coverage < 80%**: 45% attuale, target 80%
- **File > 120 LOC**: 3 file superano il limite
- **Dipendenze circolari**: MQTT ↔ Models
- **Test mancanti**: 5 funzioni pubbliche senza test

### Mappatura Performance
- **Query N+1**: 2 occorrenze in device_list view
- **Bottleneck MQTT**: Handler sincroni bloccanti
- **Memory leak**: Connection pool non chiuso

## Story Generate

### S001: Refactor API Validation
- **Obiettivo**: Consolidare 3 pattern di validazione
- **File**: 3 file, 90 LOC
- **Candidati riuso**: @Code core/forms.py
- **Test**: Coverage 80% → 85%

### S002: Consolidate MQTT Handlers  
- **Obiettivo**: Decoupling MQTT handlers
- **File**: 4 file, 120 LOC
- **Candidati riuso**: @Code energy/services/
- **Test**: Coverage 45% → 80%

### S003: Improve Test Coverage
- **Obiettivo**: Aggiungere test mancanti
- **File**: 2 file, 60 LOC
- **Candidati riuso**: @Code tests/test_models_energy.py
- **Test**: Coverage 45% → 80%

### S004: Optimize Database Queries
- **Obiettivo**: Risolvere query N+1
- **File**: 3 file, 100 LOC
- **Candidati riuso**: @Code core/models.py
- **Test**: Coverage 80% → 85%

## Vantaggi MIGRATE

✅ **Analisi automatica**: Identifica problemi senza intervento manuale
✅ **Piano strutturato**: Roadmap chiara per standardizzazione
✅ **Priorità intelligente**: Ordina per impatto/rischio
✅ **Riuso ottimizzato**: Identifica candidati per refactoring
✅ **Metriche chiare**: Target misurabili per ogni Story

