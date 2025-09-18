# Modalità di Deployment - CerCollettiva

## 🔧 Modalità Sviluppo

**Comando:**
```bash
# Modalità sviluppo - OPZIONE 1 (con override file)
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build

# Modalità sviluppo - OPZIONE 2 (con variabili)
DJANGO_SETTINGS_MODULE=cercollettiva.settings.local DEBUG=True NGINX_ENV=dev docker compose up --build
```

**Caratteristiche:**
- ✅ **Auto-reload**: Modifiche codice immediate
- ✅ **Debug attivo**: Django Debug Toolbar abilitato  
- ✅ **Settings local**: Configurazione sviluppo
- ⚠️ **Performance ridotta**: Bind mount più lento
- ⚠️ **Solo per sviluppo**: Non usare in produzione

---

## 🚀 Modalità Produzione

**Comando:**
```bash
# Modalità produzione - DEFAULT (localhost)
docker compose up --build -d

# Modalità produzione - CUSTOM hosts
ALLOWED_HOSTS=example.com,www.example.com docker compose up -d
```

**Caratteristiche:**
- ✅ **Sicurezza**: Codice isolato nell'immagine
- ✅ **Performance**: Filesystem container ottimizzato
- ✅ **Stabilità**: Non dipende da file locali
- ✅ **Settings produzione**: SSL UI, validazioni complete
- ❌ **No auto-reload**: Serve rebuild per modifiche

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

- **Sviluppo locale**: Usa sempre `docker-compose.dev.yml`
- **Test produzione**: Usa `docker-compose.yml` standard
- **Deploy VPS**: Usa `docker-compose.yml` + variabili ambiente
- **Mai**: Usare bind mount codice in produzione
