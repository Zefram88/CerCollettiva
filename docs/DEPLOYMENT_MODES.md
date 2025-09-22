# Modalità di Deployment - CerCollettiva

## Panoramica

Il sistema CerCollettiva supporta tre modalità di deployment con auto-rilevamento intelligente:

- **Development** (`dev`): ✅ **TESTATO E FUNZIONANTE** - Sviluppo locale con HTTP
- **Staging** (`staging`): ✅ **TESTATO E FUNZIONANTE** - Test con HTTPS self-signed  
- **Production** (`prod`): ⚠️ **DA TESTARE** - Produzione con HTTPS Let's Encrypt

## 🚀 Auto-Rilevamento Nginx

Il sistema implementa **auto-rilevamento intelligente** che determina automaticamente la modalità nginx:

1. **Se `NGINX_ENV` è impostata**: Usa la modalità esplicita
2. **Se `NGINX_ENV` NON è impostata**: Auto-rileva basandosi sui servizi disponibili:
   - **Dev**: Se `web-dev` è disponibile → configurazione dev
   - **Prod**: Se `web` è disponibile E ci sono certificati Let's Encrypt → configurazione prod
   - **Staging**: Default → configurazione staging

## Modalità Development ✅

### Caratteristiche
- **HTTP** (porta 80)
- **Hot reload** per sviluppo (bind mount `.:/app`)
- **Debug abilitato** (Django Debug Toolbar)
- **CSP permissivo** per sviluppo
- **Cache disabilitata**
- **Upstream**: `web-dev:8000`

### Avvio
```bash
docker-compose --profile dev up -d
```

### Accesso
- **Applicazione**: http://127.0.0.1
- **Setup**: http://127.0.0.1/setup
- **Admin**: http://127.0.0.1/ceradmin/

### Servizi Attivi
- `secrets-init`, `db`, `redis`, `mqtt`, `web-dev`, `nginx`

## Modalità Staging ✅

### Caratteristiche
- **HTTPS** con certificati self-signed
- **Security headers** ottimizzati
- **CSP** con `upgrade-insecure-requests`
- **Rate limiting** abilitato
- **Monitoring** con Prometheus/Grafana
- **Upstream**: `web:8000`

### Avvio
```bash
docker-compose --profile staging up -d
```

### Accesso
- **Applicazione**: https://localhost (accetta certificato self-signed)
- **Monitoring**: http://localhost:3000 (Grafana)
- **Prometheus**: http://localhost:9090

### Servizi Attivi
- `secrets-init`, `db`, `redis`, `mqtt`, `web`, `nginx`, `prometheus`, `grafana`

### Configurazione SSL
I certificati self-signed vengono generati automaticamente all'avvio.

## Modalità Production ⚠️

### Caratteristiche
- **HTTPS** con certificati Let's Encrypt
- **Massima sicurezza** (TLS 1.2/1.3, modern ciphers)
- **CSP** con `block-all-mixed-content`
- **OCSP Stapling**
- **Rate limiting** avanzato
- **Monitoring** completo
- **Upstream**: `web:8000`

### Prerequisiti
```bash
export DOMAIN=example.com
export LETSENCRYPT_EMAIL=admin@example.com
```

### Avvio
```bash
# Metodo 1: Script automatico
./scripts/test-prod.sh

# Metodo 2: Manuale
export DOMAIN=example.com
export LETSENCRYPT_EMAIL=admin@example.com
docker-compose --profile prod up -d
```

### Accesso
- **Applicazione**: https://example.com
- **Monitoring**: https://example.com:3000 (Grafana)
- **Prometheus**: https://example.com:9090

### Servizi Attivi
- `secrets-init`, `db`, `redis`, `mqtt`, `web`, `nginx`, `prometheus`, `grafana`

### Configurazione SSL
I certificati Let's Encrypt vengono ottenuti automaticamente all'avvio con rinnovo automatico.

## 🏗️ Architettura del Sistema

### Profili Docker Compose
```yaml
# Development
profiles: ["dev"]
services: secrets-init, db, redis, mqtt, web-dev, nginx

# Staging  
profiles: ["staging"]
services: secrets-init, db, redis, mqtt, web, nginx, prometheus, grafana

# Production
profiles: ["prod"] 
services: secrets-init, db, redis, mqtt, web, nginx, prometheus, grafana
```

### Configurazioni Nginx

#### Development
- **File**: `config/nginx/conf.d/cercollettiva-dev.conf`
- **Protocollo**: HTTP only
- **Upstream**: `web-dev:8000`
- **Cache**: Disabilitata
- **CSP**: Permissivo per sviluppo

#### Staging
- **File**: `config/nginx/conf.d/cercollettiva-staging.conf`
- **Protocollo**: HTTPS con self-signed
- **Upstream**: `web:8000`
- **Security**: Headers ottimizzati
- **Rate Limiting**: Abilitato

#### Production
- **File**: `config/nginx/conf.d/cercollettiva-prod.conf`
- **Protocollo**: HTTPS con Let's Encrypt
- **Upstream**: `web:8000`
- **Security**: Massima sicurezza
- **OCSP Stapling**: Abilitato

### Volumi e Bind Mount

#### Development (web-dev)
```yaml
volumes:
  - .:/app                    # ✅ Bind mount per live reload
  - ./media:/app/media
  - ./staticfiles:/app/staticfiles
  - ./logs:/app/logs
  - setup_complete:/app/.setup_complete
  - secrets_data:/secrets:ro
```

#### Staging/Production (web)
```yaml
volumes:
  - ./media:/app/media        # ✅ Solo dati utente
  - ./staticfiles:/app/staticfiles  # ✅ Solo file statici
  - ./logs:/app/logs          # ✅ Solo log
  - setup_complete:/app/.setup_complete  # ✅ Solo stato setup
  - secrets_data:/secrets:ro  # ✅ Solo segreti
```

## 🔧 Variabili d'Ambiente

### Auto-Rilevamento (Raccomandato)
Il sistema funziona **senza variabili d'ambiente** grazie all'auto-rilevamento.

### Configurazione Esplicita (Opzionale)

#### Development
```bash
export NGINX_ENV=dev
export DEPLOYMENT_MODE=development
```

#### Staging
```bash
export NGINX_ENV=staging
export DEPLOYMENT_MODE=staging
```

#### Production
```bash
export NGINX_ENV=prod
export DEPLOYMENT_MODE=production
export DOMAIN=example.com
export LETSENCRYPT_EMAIL=admin@example.com
```

## 📋 Comandi Utili

### Avvio
```bash
# Development
docker-compose --profile dev up -d

# Staging
docker-compose --profile staging up -d

# Production
docker-compose --profile prod up -d
```

### Stop
```bash
# Development
docker-compose --profile dev down

# Staging
docker-compose --profile staging down

# Production
docker-compose --profile prod down
```

### Logs
```bash
# Development
docker-compose --profile dev logs -f

# Staging
docker-compose --profile staging logs -f

# Production
docker-compose --profile prod logs -f
```

### Verifica Stato
```bash
# Verifica container attivi
docker ps

# Verifica servizi per profilo
docker-compose --profile dev config --services
docker-compose --profile staging config --services
docker-compose --profile prod config --services
```

### Rinnovo Certificati (Produzione)
```bash
docker-compose --profile prod exec nginx certbot renew
```

## 🐛 Troubleshooting

### Problemi di Avvio
1. **Container nginx si riavvia**: Verifica che il servizio web sia healthy
2. **Host not found**: Controlla che `web` o `web-dev` sia in esecuzione
3. **Porta occupata**: Verifica con `netstat -tulpn | grep :80`

### Problemi SSL
1. **Certificati self-signed**: Accetta il certificato nel browser
2. **Let's Encrypt fallisce**: Verifica che il dominio punti al server
3. **Certificati scaduti**: Rinnova con `certbot renew`

### Problemi CSP
1. **Risorse bloccate**: Controlla la console del browser
2. **CDN non funziona**: Verifica `cercollettiva/settings/security.py`
3. **Font non caricati**: Controlla `CSP_FONT_SRC`

### Problemi di Connessione
1. **ERR_CONNECTION_CLOSED**: Usa `127.0.0.1` invece di `localhost`
2. **HSTS forzato**: Cancella i dati del sito in Chrome
3. **Container non healthy**: Controlla `docker ps` e logs

### Debug Auto-Rilevamento
```bash
# Verifica modalità nginx
docker logs cercollettiva_nginx | grep "Modalità"

# Verifica servizi disponibili
docker ps --filter "name=cercollettiva"

# Test connettività
curl -I http://localhost/health/
```

## 🔒 Sicurezza

### Best Practices Implementate
- **Bind mount solo in dev**: Codice sorgente non esposto in staging/prod
- **Secrets dinamici**: Generazione automatica di chiavi sicure
- **Security headers**: Implementati per tutti gli ambienti
- **CSP ottimizzato**: Diverso per ogni ambiente
- **Rate limiting**: Protezione contro attacchi DDoS
- **TLS moderno**: Solo protocolli sicuri in produzione

### Configurazioni Sicurezza
- **Development**: Permissivo per sviluppo
- **Staging**: Moderato per testing
- **Production**: Massima sicurezza

## 📊 Monitoring

### Prometheus
- **Endpoint**: `/metrics`
- **Porta**: 9090
- **Targets**: web, nginx, db, redis, mqtt

### Grafana
- **Porta**: 3000
- **Default login**: admin/admin
- **Dashboards**: Pre-configurati per CerCollettiva

## 🚀 Deployment

### Sviluppo Locale
```bash
git clone <repository>
cd CerCollettiva
docker-compose --profile dev up -d
```

### Staging
```bash
docker-compose --profile staging up -d
# Accetta certificato self-signed su https://localhost
```

### Produzione
```bash
export DOMAIN=example.com
export LETSENCRYPT_EMAIL=admin@example.com
docker-compose --profile prod up -d
# Configura DNS per puntare al server
```

## 📝 Note

- **Auto-rilevamento**: Il sistema funziona senza configurazione manuale
- **Profili mutuamente esclusivi**: Ogni profilo attiva solo i servizi necessari
- **Volumi ottimizzati**: Bind mount solo dove necessario
- **Sicurezza by design**: Configurazioni diverse per ogni ambiente
- **Monitoring integrato**: Prometheus e Grafana per staging/prod