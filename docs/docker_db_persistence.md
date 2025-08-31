# Persistenza Database con Docker

Questo documento spiega come mantenere il database dell’utente persistente usando Docker, sia per sviluppo (SQLite) che per produzione (PostgreSQL).

## Sviluppo – SQLite

- Configurazione: `cercollettiva/settings/local.py` usa `CerCollettiva/db.sqlite3`.
- Persistenza: montare il file DB e cartelle `media/` e `logs/` nel container `web`.
- Esempio `docker-compose.yml` (estratto):

```
services:
  web:
    image: your/cercollettiva:dev
    environment:
      - DJANGO_SETTINGS_MODULE=cercollettiva.settings.local
    volumes:
      - ./CerCollettiva/db.sqlite3:/app/CerCollettiva/db.sqlite3
      - ./CerCollettiva/media:/app/CerCollettiva/media
      - ./CerCollettiva/logs:/app/CerCollettiva/logs
    ports:
      - "8000:8000"
```

Note: su Windows usare WSL2 per evitare problemi di file‑lock e performance.

## Produzione – PostgreSQL

- Configurazione: `cercollettiva/settings/production.py` richiede variabili `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`.
- Persistenza: utilizzare un volume nominato per i dati di Postgres.
- Esempio `docker-compose.yml` (estratto):

```
services:
  db:
    image: postgres:16
    environment:
      - POSTGRES_DB=cercollettiva
      - POSTGRES_USER=cercollettiva_user
      - POSTGRES_PASSWORD=change_me
    volumes:
      - pgdata:/var/lib/postgresql/data

  web:
    image: your/cercollettiva:prod
    environment:
      - DJANGO_SETTINGS_MODULE=cercollettiva.settings.production
      - DB_NAME=cercollettiva
      - DB_USER=cercollettiva_user
      - DB_PASSWORD=change_me
      - DB_HOST=db
      - DB_PORT=5432
    depends_on:
      - db
    volumes:
      - ./CerCollettiva/media:/app/CerCollettiva/media
      - ./CerCollettiva/logs:/app/CerCollettiva/logs

volumes:
  pgdata:
```

## Migrazione Dati da SQLite a Postgres

```
python manage.py dumpdata --natural-foreign --natural-primary \
  -e contenttypes -e auth.Permission > backup.json

# Avvia Postgres e configura settings → migrate
python manage.py migrate
python manage.py loaddata backup.json
```

## Backup

- SQLite: copia del file `.sqlite3` a caldo solo se l’app è ferma; altrimenti usare `sqlite3 .backup`.
- Postgres: `pg_dump -Fc -U <user> <db> > backup.dump` (dal container `db`).

