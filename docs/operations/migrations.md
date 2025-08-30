# Migrazioni e Gestione Schema

## Obiettivo
Allineare e versionare lo schema DB per tutte le app (`core`, `energy`, `documents`, `users`).

## Strategia
1. Generare migrazioni iniziali per ogni app (dev):
   - `python manage.py makemigrations users core energy documents`
2. Review: vincoli, indici, `unique_together`, `db_index`.
3. Applicare su ambiente di test/staging con backup:
   - `python manage.py migrate`
4. Validare funzionale (login, CRUD impianti, MQTT ingest, documenti).
5. Pianificare rollback: dump pre-migrazione, test `migrate <app> <previous_migration>`.

## Punti di Attenzione
- `core/models.py`: rimuovere campi duplicati in `Alert` e metodi duplicati prima di creare migrazioni.
- ForeignKey coerenti (`DeviceMeasurement.device` vs `device_id`), indici su `timestamp` e `device`.
- GDPR: eventuali `on_delete` coerenti (es. `SET_NULL` dove sensato) per conservazione audit.

## Convenzioni
- Una PR per gruppo logico di modifiche schema.
- `RunSQL` solo se indispensabile; preferire migrazioni auto‑generate chiare.

