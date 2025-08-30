# Sicurezza e GDPR

## Classificazione Dati
- PUBLIC / INTERNAL / CONFIDENTIAL / PERSONAL (vedi `documents.Document.data_classification`).

## Consenso e Retention
- Consenso GDPR richiesto per documenti con dati personali (`ID_DOC`, `BILL`, o classification `PERSONAL`).
- Retention automatica per tipo documento (2–10 anni) — vedi `Document.set_retention_period`.

## Minimizzazione Log
- Mascherare POD e device_id nei log; no PII in payload/trace.

## Diritti Interessati
- Cancellazione account utente (`users.DeleteAccountView`) — prevedere tracce minime per compliance.

## Segreti
- `FIELD_ENCRYPTION_KEY` e segreti su env/secret manager; no in repository.

