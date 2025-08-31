# Next Steps (Operativi e Ripartenza)

Questo file elenca i prossimi passi operativi e funge da punto di ripartenza per nuove sessioni.

## Stato Attuale (breve)
- Script dev allineati: `scripts/rundev.sh` (Unix) e `scripts/rundev.ps1` (Windows) usano `settings.local` e attivano venv.
- Script check: `scripts/check.sh` (Unix) e `scripts/check.ps1` (Windows).
- Logging aggiornato nei docs e script di logs (`scripts/logs.sh`).
- Install scripts: produzione con `settings.production`; WSL dev usa `settings.local`.

## Prossimi Passi Prioritari
- Migrazioni: verificare modelli e generare/applicare migrazioni iniziali.
  - Comando: `python manage.py makemigrations users core energy documents`
  - Poi: `python manage.py migrate`
- MQTT: inizializzazione e test con le env correnti.
  - `python manage.py init_mqtt_broker`
  - `python manage.py mqtt_client --once` (stato/config)
  - `python manage.py mqtt_client` (run con heartbeat)
  - `python manage.py gen_mqtt_device_creds <device_id> [--acl]` (credenziali per-device)
  - `python manage.py seed_mqtt_demo [POD] [DEVICE_ID] [--with-creds]` (crea Plant+Device demo)
- Health/Monitoring: verificare endpoints operativi.
  - Aprire: `/monitoring/health/`, `/monitoring/health/mqtt/`, `/monitoring/health/cache/`
  - Se necessario, aggiungere credenziali e controllo accessi.
- Documentazione: aggiungere sezione “Quick start” in `docs/README.md` con i nuovi script.
- Convenience: opzionale `make` targets per sviluppo (`make dev`, `make check`, `make mqtt-*`).
- WSL installer: valutare rimozione del blocco `dev.py` (overlay) per evitare ambiguità, mantenendo solo `settings.local`.

## Comandi Rapidi (sviluppo)
- Avvio (Unix): `bash scripts/rundev.sh --bind 127.0.0.1 --port 8000`
- Avvio (Windows): `pwsh scripts/rundev.ps1 -BindAddress 127.0.0.1 -Port 8000`
- Check + migrazioni (Unix): `bash scripts/check.sh`
- Check + migrazioni (Windows): `pwsh scripts/check.ps1`
- Log (Unix): `bash scripts/logs.sh [righe]` (default 50)

## Variabili d’Ambiente (essenziali)
- `DJANGO_SETTINGS_MODULE`: `cercollettiva.settings.local` (dev) / `cercollettiva.settings.production` (prod)
- `SECRET_KEY`, `FIELD_ENCRYPTION_KEY` (supporta prefisso `base64:`)
- `DB_*`, `REDIS_URL`, `EMAIL_*`
- `MQTT_*` (`HOST`, `PORT`, `USER`, `PASS`, `TLS`, `QOS`, `KEEPALIVE`)
- Opzionale: `DJANGO_LOG_LEVEL`

## Note
- I log principali: `logs/cercollettiva.log`, `logs/mqtt.log` (altri file extra in `local.py`).
- I settings di base usano PostgreSQL e Redis; in `local.py` alcuni fallback possono differire.
