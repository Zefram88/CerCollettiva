# Setup Automatico CerCollettiva

## 🚀 Setup Completamente Automatico

CerCollettiva ora supporta un setup completamente automatico con Docker. Basta un comando per avere l'applicazione pronta all'uso!

## 📋 Prerequisiti

- Docker
- Docker Compose
- File `env.example` (già presente nel repository)

## 🎯 Avvio Rapido

### 1. Clona il repository
```bash
git clone <repository-url>
cd CerCollettiva
```

### 2. Avvia l'applicazione
```bash
docker-compose up -d
```

**È tutto!** L'applicazione si configurerà automaticamente.

## 🔧 Cosa Succede Automaticamente

Al primo avvio, l'entrypoint script esegue:

1. **Generazione chiavi di sicurezza**
   - SECRET_KEY Django generata automaticamente
   - FIELD_ENCRYPTION_KEY per crittografia campi sensibili

2. **Creazione configurazione**
   - File `.env` creato da `env.example`
   - Chiavi aggiornate con valori sicuri

3. **Setup database**
   - Attesa dipendenze (PostgreSQL, Redis, MQTT)
   - Esecuzione migrazioni automatiche
   - Creazione schema database

4. **Raccolta risorse**
   - File statici raccolti automaticamente
   - Directory necessarie create

5. **Avvio applicazione**
   - Django avviato e pronto all'uso
   - Health check configurato

## 🌐 Accesso all'Applicazione

Dopo l'avvio (circa 1-2 minuti):

- **Applicazione**: http://localhost:8000/
- **Setup iniziale**: http://localhost:8000/setup
- **Admin**: http://localhost:8000/ceradmin/

## 📝 Prossimo Passo

1. Vai su http://localhost:8000/setup
2. Crea il tuo account superuser
3. Inizia a usare CerCollettiva!

## 🔍 Monitoraggio

### Logs in tempo reale
```bash
docker-compose logs -f web
```

### Status servizi
```bash
docker-compose ps
```

### Health check
```bash
curl http://localhost:8000/monitoring/health/
```

## 🛠️ Gestione Avanzata

### Reset completo
```bash
# Ferma e rimuovi tutto
docker-compose down -v

# Riavvia con setup pulito
docker-compose up -d
```

### Solo ricostruzione container
```bash
# Ricostruisci solo il container web
docker-compose up -d --build web
```

### Accesso al container
```bash
# Entra nel container
docker-compose exec web bash

# Esegui comandi Django
docker-compose exec web python manage.py shell
```

## 🔧 Configurazione Personalizzata

### Variabili d'ambiente
Modifica il file `.env` per personalizzare:

```bash
# Database
DB_PASSWORD=your_secure_password

# Debug mode
DEBUG=False

# Chiavi personalizzate (opzionale)
SECRET_KEY=your_custom_secret_key
FIELD_ENCRYPTION_KEY=your_custom_encryption_key
```

### Servizi opzionali
```bash
# Solo servizi essenziali
docker-compose up -d db redis mqtt web

# Con monitoring
docker-compose up -d

# Con backup
docker-compose --profile backup up -d
```

## 🐛 Troubleshooting

### Problema: Container non si avvia
```bash
# Controlla logs
docker-compose logs web

# Verifica configurazione
docker-compose config
```

### Problema: Database non pronto
```bash
# Riavvia solo database
docker-compose restart db

# Controlla status
docker-compose exec db pg_isready
```

### Problema: Setup già completato
```bash
# Reset setup
docker-compose exec web rm -f /app/.setup_complete
docker-compose restart web
```

## 📊 Servizi Inclusi

- **Web**: Django application (porta 8000)
- **Database**: PostgreSQL (porta 5432)
- **Cache**: Redis (porta 6379)
- **MQTT**: Mosquitto broker (porta 1883)
- **Proxy**: Nginx (porta 80/443)
- **Monitoring**: Prometheus (porta 9090)
- **Dashboard**: Grafana (porta 3000)

## 🎉 Risultato

Dopo `docker-compose up -d`:

✅ Database inizializzato e migrato  
✅ Chiavi di sicurezza generate  
✅ File statici raccolti  
✅ Applicazione pronta all'uso  
✅ Setup iniziale disponibile su /setup  

**Tempo totale: <2 minuti**  
**Comandi richiesti: 1**  
**Configurazione manuale: 0**

---

*CerCollettiva - Sistema di gestione Comunità Energetiche Rinnovabili*
