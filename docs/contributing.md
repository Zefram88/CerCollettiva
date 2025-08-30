# Contribuire a CerCollettiva

## Requisiti
- Python 3.11+
- Redis, Postgres/SQLite, Mosquitto (ambiente esistente)

## Setup rapido
```
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
set DJANGO_SETTINGS_MODULE=cercollettiva.settings.local
python manage.py migrate
python manage.py runserver
```

## Stile e Qualità
- PEP8; suggeriti `black`, `isort`, `ruff` (opzionale pre-commit).
- Commit convention (consigliato): Conventional Commits.

## Branch & PR
- Branch per feature/fix separati; PR piccole e atomiche.
- Descrivere cambi, rischi e note di migrazione.

## Test
- Preferire unit test mirati; integrazione con broker esistente per MQTT.

