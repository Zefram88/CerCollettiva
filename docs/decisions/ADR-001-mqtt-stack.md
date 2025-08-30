# ADR-001: Standardizzazione Stack MQTT

Status: Accepted
Date: 2025-08-30

## Context
Nel repo coesistono due implementazioni MQTT:
- Legacy: `energy/mqtt/client.py` con gestione diretta Paho, sottoscrizioni e coda.
- Nuova: `energy/mqtt/core.py` (MQTTService con CircuitBreaker/Retry/Handlers) + `energy/mqtt/manager.py` (DeviceManager: mapping topic→device, dedup, salvataggi).

La duplicazione complica debugging, evoluzione e affidabilità.

## Decision
Standardizzare sullo stack “nuovo”: `MQTTService (core.py)` + `DeviceManager (manager.py)` come percorso unico per ingest e persistenza.

## Conseguenze
- Disattivare dipendenze dal client legacy, mantenendolo eventualmente come fallback dietro feature flag temporaneo.
- Test integrazione con broker esistente (Mosquitto) e payload reali.
- Metriche/health centralizzate su `MQTTService`.

## Migrazione
- Introduzione feature flag `USE_NEW_MQTT` (default: true) in settings.
- Aggiornare punti d’ingresso (views/command) a usare il servizio.
- Rimuovere/refactor codice legacy in PR separata, dopo validazione in staging.

