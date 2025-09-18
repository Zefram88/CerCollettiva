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

## 🎯 Raccomandazioni

- **Sviluppo locale**: Usa sempre `docker-compose.dev.yml`
- **Test produzione**: Usa `docker-compose.yml` standard
- **Deploy VPS**: Usa `docker-compose.yml` + variabili ambiente
- **Mai**: Usare bind mount codice in produzione
