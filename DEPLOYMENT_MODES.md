# Modalità di Deployment - CerCollettiva (UNIFICATO)

## 🎆 ARCHITETTURA UNIFICATA

**Novità v2.0:**
- **Single docker-compose.yml** con configurazione dinamica
- **Environment profiles** per ogni modalità
- **SSL automation** completo
- **Command switching** automatico
- **Bind mount condizionale**

---

## 🔧 Modalità Sviluppo

**Comando:**
```bash
# Copia profile development
cp env.development .env

# Avvio modalità sviluppo
docker compose up --build
```

**Caratteristiche:**
- ✅ **Auto-reload**: Bind mount `.:/app/src` + runserver_plus
- ✅ **Debug completo**: DEBUG=True + Django Debug Toolbar
- ✅ **Logging verbose**: Console output + livello DEBUG
- ✅ **HTTP only**: No SSL per velocità
- ✅ **Environment validation**: Pre-flight checks automatici
- ⚠️ **Solo per sviluppo**: Mai usare in staging/prod

---

## 🎭 Modalità Staging

**Comando:**
```bash
# Copia profile staging
cp env.staging .env

# Configura dominio test (opzionale)
echo "DOMAIN=staging.cercollettiva.local" >> .env

# Avvio modalità staging
docker compose up --build -d
```

**Caratteristiche:**
- ✅ **Codice embedded**: No bind mount, come produzione
- ✅ **HTTPS**: SSL self-signed automatico
- ✅ **Gunicorn**: Production server per test performance
- ✅ **Logging moderato**: Livello INFO
- ✅ **Debug opzionale**: Configurabile per troubleshooting
- ✅ **Open monitoring**: Endpoint accessibili per test

---

## 🚀 Modalità Produzione

**Comando:**
```bash
# Copia profile production
cp env.production .env

# Configura dominio reale e SSL
echo "DOMAIN=cercollettiva.com" >> .env
echo "LETSENCRYPT_EMAIL=admin@cercollettiva.com" >> .env

# Genera password sicure
./scripts/validate-environment.sh

# Avvio modalità produzione
docker compose up --build -d
```

**Caratteristiche:**
- ✅ **Sicurezza massima**: Codice embedded + validazioni strict
- ✅ **Let's Encrypt**: SSL automatico per domini reali
- ✅ **Performance**: Gunicorn multi-worker + cache aggressive
- ✅ **Monitoring**: Rate limiting + HTTPS obbligatorio
- ✅ **Error tracking**: Sentry integration
- ✅ **Backup automatico**: Database + media files
- ❌ **Zero debug**: DEBUG=False forzato

---

## 🔍 Differenze Architetturali

| Aspetto | Sviluppo | Produzione |
|---------|----------|------------|
| **Codice** | Bind mount `.:/app` | Dentro immagine `COPY . .` |
| **SSL Database** | Disabilitato | Disabilitato (Docker interno) |
| **SSL UI** | HTTP (dev) | HTTPS |
| **Settings** | `local.py` | `production.py` |
| **Debug** | `True` | `False` |
| **Performance** | Ridotta | Ottimale |
| **Sicurezza** | Ridotta | Massima |

---

## ⚠️ Problemi Risolti

**PRIMA (architettura sbagliata):**
- RUN_MODE ovunque → Confusione variabili
- Bind mount anche in produzione → Insicurezza
- Configurazioni fisse → Poca flessibilità

**DOPO (architettura corretta):**
- Variabili d'ambiente chiare → Flessibilità massima
- Due approcci: file override + variabili → Scelta libera
- docker-compose.yml neutro → Configurabile

---

## 🧪 Setup Iniziale (Wizard)

- Wizard disponibile su `/setup` quando non esistono superuser attivi.
- Reset completo per testare il wizard:
  - `docker compose down -v`
  - `docker system prune -af`
  - `docker compose build --no-cache && docker compose up -d`
- Il marker di entrypoint è persistito via volume `setup_complete` e non blocca il wizard.

---

## 🔐 Login e Rate Limiting

- Il rate limit su `/users/login/` a livello Nginx è disattivato per evitare 503 in caso di redirect/loop.
- Eventuali limiti si implementano lato Django se richiesti.

---

## 🛡️ CSP e Statici

- CSP configurato per consentire CDN standard (Bootstrap/Google Fonts/jsDelivr).
- In dev, Nginx serve HTTP; in prod HTTPS con certificato (self-signed se non configurato dominio).

---

## 🔒 TLS/SSL: architettura e fix apportati

Questo progetto usa terminazione TLS a livello Nginx. Le connessioni interne Docker (Nginx→Django, Django→PostgreSQL/Redis) rimangono in chiaro perché confinate nella rete bridge.

- Reverse proxy HTTPS
  - In produzione (`NGINX_ENV=prod`) Nginx espone `:443` con HTTP/2 e certificati.
  - In sviluppo (`NGINX_ENV=dev`) Nginx espone solo HTTP (`:80`) per rapidità e semplicità.

- Generazione certificati
  - `scripts/nginx-entrypoint.sh` genera certificati self‑signed quando non sono impostati `DOMAIN` e `LETSENCRYPT_EMAIL`.
  - È stato aggiunto `openssl` in `Dockerfile.nginx` per abilitare la generazione dei cert.
  - Per domini reali, l’entrypoint prepara le directory per l’eventuale integrazione Let’s Encrypt.

- Upstream interno Nginx→Django
  - Il traffico interno resta in HTTP (no TLS) verso l’upstream `web:8000`.
  - In Django è configurato `SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")` per fidarsi del protocollo del proxy.
  - `SECURE_SSL_REDIRECT = False` lato Django per evitare loop (è Nginx a forzare HTTPS esternamente). Il redirect a HTTPS è gestito dal server block su porta 80.

- Database PostgreSQL (SSL DB)
  - In `cercollettiva/settings/production.py` `sslmode="disable"` per le connessioni interne Docker: l’SSL dell’UI è indipendente dal canale DB.
  - Timeout/keepalive configurati per robustezza; in ambienti esterni a Docker, abilitare SSL DB se richiesto dall’infrastruttura.

- Redis
  - Connessione interna non TLS; autenticazione obbligatoria con password.
  - Healthcheck aggiornato per includere `-a <password>`.

- Host e origini fidate
  - `ALLOWED_HOSTS` configurabile via `.env`; include `web` per supportare il proxy Nginx.
  - `CSRF_TRUSTED_ORIGINS` e `CSP_CONNECT_SRC` derivano da `DOMAIN`, `WWW_DOMAIN`, `API_DOMAIN` con fallback a `localhost`/`127.0.0.1`.

- CSP
  - Ampliate le direttive per consentire CDN standard (jsDelivr, cdnjs, Google Fonts) ed evitare UI “monca”.

- Rate limiting login
  - Rimosso `limit_req` su `/users/login/` in Nginx: i POST di autenticazione non generano più 503 spurie.

- Robustezza e DX
  - Rimosso bind mount del sito Nginx in prod per evitare conflitti (file mancanti/override vuoti).
  - Healthcheck semplificati (`/health/` via HTTP) e logging Gunicorn esteso.

---

## 🎯 Raccomandazioni

## 🔯 Nuovi Comandi Quick Start

```bash
# DEVELOPMENT
cp env.development .env
docker compose up --build
# → HTTP localhost:8000 + auto-reload + debug

# STAGING  
cp env.staging .env
echo "DOMAIN=staging.local" >> .env
docker compose up --build -d
# → HTTPS staging.local + production-like

# PRODUCTION
cp env.production .env
echo "DOMAIN=yourdomain.com" >> .env
echo "LETSENCRYPT_EMAIL=admin@yourdomain.com" >> .env
./scripts/validate-environment.sh
docker compose up --build -d
# → HTTPS yourdomain.com + Let's Encrypt + security
```

## 🔄 Migrazione da v1.0

```bash
# Backup configurazione esistente
cp docker-compose.yml docker-compose.v1.backup
cp docker-compose.dev.yml docker-compose.dev.v1.backup

# Usa nuova architettura
cp env.development .env  # per development
# oppure
cp env.production .env   # per production

# Test nuova configurazione
./scripts/validate-environment.sh
docker compose up --build
```
