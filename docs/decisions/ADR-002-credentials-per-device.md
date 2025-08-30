# ADR-002: Ambito Credenziali MQTT — per Dispositivo

Status: Accepted
Date: 2025-08-30

## Context
Esistono due possibili granolarità per le credenziali MQTT:
- Per-utente (User-level)
- Per-dispositivo (Device-level)

Il modello dati attuale include `MQTTBroker` (config globale) e `MQTTConfiguration` (per singolo `DeviceConfiguration`).

## Decision
Mantenere l’ambito “per-dispositivo” per autorizzazioni e tracciabilità fine-grained.

## Conseguenze
- Ogni device ha username/password dedicati, revocabili senza impatti su altri.
- Audit più preciso (`MQTTAuditLog` su username device).
- Semplifica ACL basate su topic legati a `plant.pod_code` e `device_id`.

## Implementazione
- Usare `MQTTConfiguration` collegata 1–1 a `DeviceConfiguration`.
- Generazione/rotazione credenziali mediante service dedicato.
- ACL su broker allineate a topic dei device (read-only publish verso topic assegnati).

