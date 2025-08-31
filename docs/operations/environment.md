# Configurazione Ambiente e Variabili

Questo documento elenca le variabili di ambiente e le configurazioni richieste per eseguire CerCollettiva in sviluppo e produzione.

## Variabili Obbligatorie
- `DJANGO_SETTINGS_MODULE`: modulo settings (`cercollettiva.settings.local` in dev, `cercollettiva.settings.production` in prod)
- `SECRET_KEY`: chiave Django
- `FIELD_ENCRYPTION_KEY`: chiave cifratura per `encrypted_model_fields`
- `DEBUG`: `True|False` (solo local: True)

### Database
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `DB_PORT` (default `5432`)

### Redis / Channels / Cache
- `REDIS_URL` (es. `redis://127.0.0.1:6379/1`)

### SMTP / Email
- `EMAIL_HOST`
- `EMAIL_PORT` (default `587`)
- `EMAIL_USE_TLS` (`True|False`)
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`
- `DEFAULT_FROM_EMAIL`

### MQTT
- `MQTT_HOST`
- `MQTT_PORT` (1883/8883 TLS)
- `MQTT_USER` (opzionale — se broker richiede auth globale)
- `MQTT_PASS`
- `MQTT_QOS` (default `1`)
- `MQTT_KEEPALIVE` (default `60`)
- `MQTT_TLS` (`True|False`)
- `USE_NEW_MQTT` (`True|False`) — feature flag unificazione stack

### Script e Comandi utili
- Avvio sviluppo (PowerShell Windows): `pwsh scripts/rundev.ps1 -BindAddress 127.0.0.1 -Port 8000`
- Sanity check + migrazioni: `pwsh scripts/check.ps1`
- Client/Service MQTT:
  - Configura e stampa stato una sola volta: `python manage.py mqtt_client --once`
  - Avvio con heartbeat: `python manage.py mqtt_client`

### Sentry (produzione opzionale)
- `SENTRY_DSN`
- `SENTRY_SAMPLE_RATE`
- `SENTRY_ENVIRONMENT`

## File .env (esempio base)
```
DJANGO_SETTINGS_MODULE=cercollettiva.settings.local
SECRET_KEY=change-me
FIELD_ENCRYPTION_KEY=base64:change-me
DEBUG=True

DB_NAME=cercollettiva
DB_USER=cer_user
DB_PASSWORD=change-me
DB_HOST=127.0.0.1
DB_PORT=5432

REDIS_URL=redis://127.0.0.1:6379/1

EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=noreply@example.org

MQTT_HOST=localhost
MQTT_PORT=1883
MQTT_TLS=False
MQTT_USER=
MQTT_PASS=
MQTT_QOS=1
MQTT_KEEPALIVE=60
USE_NEW_MQTT=True
```

## Linee Guida Sicurezza
- Non committare `.env`.
- Gestire segreti con secret manager in produzione.
- Rotazione periodica `FIELD_ENCRYPTION_KEY` con piano di re-cifratura (out-of-scope qui).
