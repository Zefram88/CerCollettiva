# Deploy su Web Server

Questo documento descrive una soluzione consigliata per il deploy di CerCollettiva su un web server, con attenzione a stabilità, sicurezza e aggiornabilità.

## Obiettivi

- Separare i processi (web ASGI, worker MQTT, DB, cache)
- Supportare WebSocket (Django Channels)
- Aggiornamenti sicuri e rollback rapidi
- Persistenza dei dati (DB, media, log)

## Architettura Raccomandata (Docker Compose)

- Proxy reverse (Nginx/Caddy/Traefik) con TLS,
- `web`: Gunicorn + UvicornWorker (ASGI),
- `mqtt-worker`: esegue `python manage.py mqtt_client`,
- `db`: PostgreSQL con volume nominato (produzione),
- `redis`: cache e canale per Channels,
- Volumi: `pgdata`, `media`, `staticfiles`, `logs`.

### Comando ASGI consigliato

```
gunicorn cercollettiva.asgi:application -k uvicorn.workers.UvicornWorker -w 3 -b 0.0.0.0:8000
```

## Ciclo di Deploy

1. Build/push immagine (CI → registry),
2. `docker compose pull`,
3. Migrazioni DB: `docker compose run --rm web python manage.py migrate`,
4. `docker compose up -d`,
5. Healthcheck su endpoint pubblico (es. `/` o `/healthz`).

## Persistenza e Backup

- PostgreSQL: volume `pgdata` + backup periodico con `pg_dump`.
- Media e log: volumi montati e rotazione log.

## Sicurezza

- TLS (Let’s Encrypt),
- Variabili d’ambiente per segreti (`SECRET_KEY`, `DB_*`, `REDIS_URL`),
- Firewall e aggiornamenti regolari delle immagini.

## Alternativa Bare‑Metal (senza Docker)

- Nginx → Gunicorn+Uvicorn in venv via `systemd`,
- `systemd` unit separata per `mqtt-worker`,
- PostgreSQL e Redis come servizi di sistema,
- Script di deploy: `git pull`, `pip install -r requirements.txt`, `manage.py collectstatic`, `manage.py migrate`, `systemctl restart`.

