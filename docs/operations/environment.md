# Configurazione Ambiente e Variabili

Questo documento elenca le variabili di ambiente e le configurazioni richieste per eseguire CerCollettiva in sviluppo e produzione.

## Variabili Obbligatorie
- `DJANGO_SETTINGS_MODULE`: modulo settings (`cercollettiva.settings.local` in dev, `cercollettiva.settings.production` in prod)
- `SECRET_KEY`: chiave Django
- `FIELD_ENCRYPTION_KEY`: chiave cifratura per `encrypted_model_fields`
  - Formato: chiave Fernet base64 url-safe (32 byte)
  - Generazione: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
  - Supportato anche il prefisso `base64:...` (verrà normalizzato automaticamente)
- `DEBUG`: `True|False` (solo local: True)

### Opzionali utili
- `DJANGO_LOG_LEVEL`: livello log Django (default `INFO`)

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
- Avvio sviluppo (Unix): `bash scripts/rundev.sh --bind 127.0.0.1 --port 8000`
- Sanity check + migrazioni (Windows): `pwsh scripts/check.ps1`
- Sanity check + migrazioni (Unix): `bash scripts/check.sh`
- Client/Service MQTT:
  - Configura e stampa stato una sola volta: `python manage.py mqtt_client --once`
  - Avvio con heartbeat: `python manage.py mqtt_client`
  - Inizializza broker MQTT attivo dalle variabili di ambiente: `python manage.py init_mqtt_broker`
  - Genera credenziali per-device: `python manage.py gen_mqtt_device_creds <device_id> [--acl]`
  - Pubblica payload di test: `python manage.py publish_mqtt_demo <device_id> [--count N] [--interval S]`
- Genera chiave cifratura valida (Fernet): `python manage.py gen_field_key`

### Sentry (produzione opzionale)
- `SENTRY_DSN`
- `SENTRY_SAMPLE_RATE`
- `SENTRY_ENVIRONMENT`

## File .env (esempio base)
```
DJANGO_SETTINGS_MODULE=cercollettiva.settings.local
SECRET_KEY=change-me
FIELD_ENCRYPTION_KEY=Z1o9j5T2T1Qz3KJmWmKx1e0Y2xJYg2f4m0f4O5z6X9o=
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
- PDF: opzionale `WeasyPrint` per generare PDF senza dipendenze OS di wkhtmltopdf.
  - `pip install weasyprint` e relativi prerequisiti di sistema come da documentazione ufficiale.
