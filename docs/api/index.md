# API Overview

Le API sono esposte sia tramite DRF (ViewSet/Router) sia con viste JSON specifiche in `core`.

## Autenticazione
- Session-based (login Django). Tutte le API richiedono utente autenticato; permessi per-staff/owner.

## NAMESPACE
- DRF Energy: `/energy/api/` e `/api/energy/` (namespace `energy`)
- Core JSON: `/core/api/...` (in `core/urls.py`)

## Rate limiting
- DRF throttling (Anon/User) configurata nei settings.

## Errori
- JSON con `error`/`detail`, 4xx/5xx coerenti.

