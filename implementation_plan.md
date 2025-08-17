# Implementation Plan

[Overview]
Obiettivo: Fornire un piano dettagliato, passo-passo e attuabile per l'analisi approfondita, la correzione delle criticità e i miglioramenti del progetto CerCollettiva.

Questo documento definisce ambito, motivazioni, modifiche proposte, impatti e ordine di implementazione per garantire che ogni cambiamento sia tracciabile e testato. Si concentra su sicurezza/configurazioni, affidabilità MQTT e ingestione dati, processamento documenti (GAUDI), qualità del codice e test coverage. Il piano è pensato per evitare interruzioni in produzione e minimizzare i rischi di regressione, includendo strategie di migrazione e rollback quando necessario.

Integrazione di buone norme di programmazione ed esecuzione: il piano incorpora regole pratiche per stile, tipizzazione, testing, CI/CD, gestione segreti, logging e runbook operativo. Queste norme sono intese come obbligatorie per tutte le modifiche di produzione; i dettagli operativi ed esempi di comandi sono inclusi nelle sezioni successive e nei file di configurazione proposti.

[Types]
Single sentence: Introduzione di DTO/TypedDict/dataclass per i payload MQTT e per i dati estratti dai documenti GAUDI, con validatori e regole chiare.

- MQTTPayload (DTO)
  - topic: str (non vuoto) — validare con regexp in accordo a TOPIC_PREFIX
  - device_id: str (uuid o alfanumerico) — required
  - timestamp: datetime (UTC) — required, timezone-aware
  - values: Dict[str, Decimal] — keys previste: POWER, ENERGY, VOLTAGE, CURRENT
  - qos: int (0|1|2) — default 1
  - retained: bool — default False
  - Validation: pydantic/dataclass validators: types, ranges (es. POWER >= 0)

- GaudiPlantDTO
  - pod_code: str — pattern e lunghezza validate
  - nominal_power: Decimal (kW) — > 0
  - installation_date: date | None
  - address: {address: str, city: str, zip_code: str, province: str}
  - gaudi_fields: dict con chiavi mappate a core.models.Plant.gaudi_*
  - Validation: normalize strings, trim, coerce numerics, report errors strutturati

- ConfigSchema (typed dict)
  - DB: {NAME: str, USER: str, HOST: str, PORT: int}
  - MQTT: {BROKER_HOST: str, BROKER_PORT: int, USERNAME?: str, PASSWORD?: str}
  - ENCRYPTION_KEYS: lettura esclusiva da env o keydir con permessi ristretti

- Validation rules
  - Tutti i DTO devono avere validator (pydantic o serializzatore custom).
  - Errori di validazione devono essere restituiti in forma strutturata (dict con campo->errore).
  - Nessun dato sensibile deve essere salvato in chiaro; usare encryption layer per campi sensibili.

[Files]
Single sentence: Creazione dei nuovi file per DTO, wrapper MQTT, decoder, validators e aggiunta/aggiornamento di configurazioni e script operativi.

- Nuovi file (da creare)
  - core/types.py — DTO/TypedDict/dataclass e validator functions
  - energy/mqtt/wrapper.py — MqttClientWrapper testabile
  - energy/mqtt/decoder.py — decode_mqtt_payload(payload_bytes) -> MQTTPayload
  - documents/processors/validators.py — validate_gaudi_dto(dto) e helper
  - documents/processors/gaudi_processor.py — GaudiProcessor.parse/validate/persist
  - .env.example — variabili env obbligatorie e opzionali
  - requirements-dev.txt — dev dependencies (ruff, pytest, pytest-django, mypy/pyright, factory-boy)
  - .ruff.toml, pyproject.toml (se serve) — lint/config
  - docs/SECURITY.md — policy segreti e key management
  - scripts/verify_env_secrets.sh — verifica non distruttiva segreti in env
  - .github/workflows/ci.yml — pipeline lint/test
  - core/tests/test_plant_model.py, energy/tests/test_mqtt_client.py, documents/tests/test_gaudi_processor.py, integration/tests/test_integration.py — test suite

- Esistenti da modificare (cambi specifici)
  - core/models.py
    - Rimuovere duplicati (get_total_system_power duplicata), rimuovere funzione globale test_mqtt_connection
    - Delegare test_mqtt_connection e connessione reale a MqttClientWrapper
    - Aggiungere type hints, docstrings e separare query complesse in helper privati
  - energy/mqtt/client.py
    - Rifattorizzare per utilizzare energy/mqtt/wrapper.py; mantenere retrocompatibilità API con adapter
  - documents/processors/gaudi.py
    - Estrarre parsing puro, validazione e persistenza in GaudiProcessor; centralizzare logging ed error handling
  - cercollettiva/settings/base.py
    - Rimuovere FIELD_ENCRYPTION_KEY hardcoded; leggere da env o keydir. Aggiungere controllo di startup per segreti mancanti
  - cercollettiva/settings/local.py
    - Rimuovere credenziali hardcoded, sostituire con env o commento TODO e fallback sicuro
  - app/requirements.txt
    - Separare in requirements.txt (prod) e requirements-dev.txt (dev)
  - core/admin.py, Alert model (core/models.py)
    - Correggere campi duplicati e verificare indici

- File da eliminare / spostare
  - Eliminare definizioni duplicate identificate (es. test_mqtt_connection globale) dopo aver verificato che non esistono riferimenti residui
  - Spostare logica di connessione esterna fuori dai models in servizi dedicati

- Aggiornamenti di configurazione
  - Aggiungere .env.example e README aggiornato con variabili obbligatorie
  - Aggiungere startup checks (manage command o middleware) che falliscono in assenza di segreti critici in production

[Functions]
Single sentence: Introduzione di funzioni helper e spostamento della logica esterna in nuovi moduli per aumentare testabilità e separazione delle responsabilità.

- Nuove funzioni
  - MqttClientWrapper.__init__(config: dict)
  - MqttClientWrapper.connect(self, blocking: bool = False) -> None  (energy/mqtt/wrapper.py)
  - MqttClientWrapper.disconnect(self) -> None
  - MqttClientWrapper.publish(self, topic: str, payload: dict, qos:int=1, retain:bool=False) -> bool
  - MqttClientWrapper.subscribe(self, topic: str, callback: Callable) -> None
  - decode_mqtt_payload(payload_bytes: bytes) -> MQTTPayload (energy/mqtt/decoder.py)
  - gaudi_parse_workbook(path: str) -> GaudiPlantDTO (documents/processors/gaudi_processor.py)
  - validate_gaudi_dto(dto: GaudiPlantDTO) -> None (documents/processors/validators.py)
  - scripts/verify_env_secrets.sh — verifica presenza e formato di env critici

- Funzioni da modificare
  - Plant.test_mqtt_connection (core/models.py)
    - Delegare a MqttClientWrapper.test_connection o rimuovere doppioni; non effettuare save() come effetto collaterale
  - Plant.save (core/models.py)
    - Evitare doppio super().save() non necessario; usare update_fields quando possibile; aggiungere parametro do_geocoding per controllare comportamento
  - get_total_system_power (core/models.py)
    - Consolidare in singola implementazione e ottimizzare query usando annotazioni e indici
  - documents/processors/gaudi.py
    - Split parse/validate/persist; rendere parse pura (senza side-effects), persist tramite service

- Funzioni da rimuovere
  - Definizione globale test_mqtt_connection duplicata (core/models.py) — rimuovere dopo migrazione al wrapper
  - Helper non usati: rimuovere solo dopo search_files completa e refactor

[Classes]
Single sentence: Aggiunta di classi servizio testabili e refactor di model per delega di responsabilità.

- Nuove classi
  - MqttClientWrapper (energy/mqtt/wrapper.py)
    - Key methods: __init__(config), connect(), disconnect(), subscribe(topic, cb), publish(topic, payload), register_handler(topic, cb), _on_message
    - Testable, riutilizzabile, espose metriche e hooks
  - GaudiProcessor (documents/processors/gaudi_processor.py)
    - Methods: parse(file_path) -> GaudiPlantDTO, validate(dto), persist(dto, create_or_update=True)
  - DTO classes (core/types.py) — dataclass/TypedDict per MQTTPayload, GaudiPlantDTO

- Classi modificate
  - Plant (core/models.py)
    - Rimozione della logica di connessione MQTT diretta; injection di servizio wrapper dove necessario
    - Refactor di save(), clean(), geocoding in helper privati e testabili
  - CERConfiguration / CERMembership
    - Aggiunta di indici e constraint se necessario (index su code)
  - Alert
    - Eliminare duplicazioni di campi e mantenere struttura coerente

- Classi rimosse
  - Nessuna rimozione completa prevista; responsabilità spostate in nuove classi/servizi

[Dependencies]
Single sentence: Aggiunta di tool di sviluppo e integrazione CI, mantenendo le dipendenze di runtime invariate salvo aggiornamenti di sicurezza.

- Nuove dipendenze proposte
  - Dev: ruff, pytest, pytest-django, factory-boy, mypy o pyright, pre-commit, coverage
  - Optional security scans: bandit o semgrep
  - Prod: mantenere paho-mqtt, channels, channels-redis; aggiornare version pin se necessario

- Version pinning e file
  - Creare requirements-dev.txt con version pin controllati; mantenere app/requirements.txt per runtime
  - Fornire .python-version o note su versione Python supportata (es. 3.10+)

- Integrazione
  - Aggiungere .github/workflows/ci.yml che esegue lint, test e security-scan su PR
  - Aggiungere pre-commit per eseguire ruff --fix e controlli base prima del commit

[Testing]
Single sentence: Implementare suite completa di unit e integration tests con CI che esegue lint e test automaticamente.

- Strategia
  - Unit tests per funzionalità pure (decoder, DTO validators, Gaudi parse)
  - Integration tests per flusso end-to-end (MQTT ingest -> DB), usando fixture/mock per broker o MQTT in-memory
  - Smoke tests per deploy (health checks)

- Test files e casi
  - core/tests/test_plant_model.py: geocoding success/failure, save behavior, clean membership validation
  - energy/tests/test_mqtt_client.py: connect/disconnect, reconnect backoff, subscribe+dispatch, publish return codes
  - documents/tests/test_gaudi_processor.py: parse valid workbook, invalid pod, validation errors, persist behavior
  - integration/tests/test_integration.py: fixtures per DB + mock MQTT broker

- CI checks (obbligatori)
  - ruff check --fix (fail on diffs)
  - pytest -q --maxfail=1 --cov
  - mypy/pyright step (opzionale ma raccomandato)
  - security scan (bandit/semgrep) step facoltativo ma raccomandato

- Coding & Execution Norms (integrate into testing & CI)
  - Enforce PEP8 via ruff; fixer automatico in pre-commit.
  - Type hints obbligatori per API pubbliche; controllo graduale con mypy/pyright.
  - Commit messages: Conventional Commits.
  - PR template con checklist (lint, tests, migrations, security).
  - Runbook health checks and smoke tests executed as part of staging pipeline.

[Implementation Order]
Single sentence: Eseguire il lavoro in fasi incrementali, partendo da preparazione e test infra, poi rifattorizzazioni sicure, test e infine ottimizzazioni e deploy.

1. Preparazione (low-risk)
   - Commettere implementation_plan.md (fatto).
   - Aggiungere .env.example, README aggiornato sulle env variabili obbligatorie.
   - Creare requirements-dev.txt, .ruff.toml, pyproject.toml (se serve) e file pre-commit.
   - Aggiungere docs/SECURITY.md e scripts/verify_env_secrets.sh.

2. Tooling & CI
   - Configurare .github/workflows/ci.yml per lint+test.
   - Aggiungere pre-commit config che esegue ruff --fix e controlli base.

3. Tipi e parsing
   - Creare core/types.py (DTO) e energy/mqtt/decoder.py (decode_mqtt_payload).
   - Aggiungere unit tests per decoder/validators.

4. Wrapper MQTT e adapter
   - Implementare energy/mqtt/wrapper.py (MqttClientWrapper) con test per connect/publish/subscribe.
   - Mantenere adapter che fornisca API retrocompatibili a energy/mqtt/client.py.

5. Refactor dominio core
   - Rimuovere duplicati in core/models.py (get_total_system_power, test_mqtt_connection globale).
   - Delegare connessione MQTT alla wrapper e aggiornare Plant.test_mqtt_connection per non fare save side-effects.
   - Aggiungere docstrings e type hints.

6. GAUDI processor
   - Rifattorizzare documents/processors/gaudi.py in GaudiProcessor con parse/validate/persist.
   - Aggiungere validators, test fixtures e unit tests.

7. Sicurezza e configurazioni
   - Rimuovere chiavi hardcoded (FIELD_ENCRYPTION_KEY) e DB password da local.py.
   - Verificare startup checks e documentare la gestione segreti in docs/SECURITY.md.

8. Test, CI e ottimizzazioni
   - Eseguire l'intera suite di test, risolvere regressioni.
   - Profilare get_total_system_power e query pesanti; aggiungere indici/materialized views o caching.

9. Release & staging
   - Creare branch feature/ci-refactor, PR con reviewer, validazione su staging (smoke tests, health checks).
   - Canary o staged rollout, monitor metriche e rollback se necessario.

10. Operazioni post-release
    - Aggiungere runbook (docs/DEPLOYMENT.md) con health checks, procedure rollback, backup e contatti.

Appendice: comandi rapidi per navigare il piano
# Read Overview section
sed -n '/[Overview]/,/[Types]/p' implementation_plan.md | head -n 1 | cat

# Read Types section  
sed -n '/[Types]/,/[Files]/p' implementation_plan.md | head -n 1 | cat

# Read Files section
sed -n '/[Files]/,/[Functions]/p' implementation_plan.md | head -n 1 | cat

# Read Functions section
sed -n '/[Functions]/,/[Classes]/p' implementation_plan.md | head -n 1 | cat

# Read Classes section
sed -n '/[Classes]/,/[Dependencies]/p' implementation_plan.md | head -n 1 | cat

# Read Dependencies section
sed -n '/[Dependencies]/,/[Testing]/p' implementation_plan.md | head -n 1 | cat

# Read Testing section
sed -n '/[Testing]/,/[Implementation Order]/p' implementation_plan.md | head -n 1 | cat

# Read Implementation Order section
sed -n '/[Implementation Order]/,$p' implementation_plan.md | cat
