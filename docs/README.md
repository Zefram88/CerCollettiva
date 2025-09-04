# Documentazione CerCollettiva

Benvenuto nella documentazione completa di CerCollettiva, il sistema di gestione per Comunità Energetiche Rinnovabili (CER) e Comunità Energetiche dei Cittadini (CEC).

## 📚 Indice Documentazione

### 🏗️ Architettura e Sviluppo
- **[Architettura del Sistema](ARCHITECTURE.md)** - Panoramica completa dell'architettura, componenti e pattern utilizzati
- **[Guida per Sviluppatori](DEVELOPER_GUIDE.md)** - Tutto quello che serve per contribuire al progetto
- **[Documentazione API](API_DOCUMENTATION.md)** - Reference completo delle API REST
- **[🚀 Roadmap Strategica](STRATEGIC_ROADMAP.md)** - Piano di sviluppo enterprise e roadmap business
- **[🔧 Specifiche Tecniche](TECHNICAL_SPECIFICATIONS.md)** - Architettura dettagliata, API e schema database

### 🚀 Deployment e Operazioni
- **[Guida al Deployment](DEPLOYMENT_GUIDE.md)** - Istruzioni per deployment in diversi ambienti
- **[Guida alla Sicurezza](SECURITY_GUIDE.md)** - Best practices per sicurezza e compliance

### 📋 Installazione e Setup
- **[Installazione](install/README.md)** - Guide di installazione per diversi sistemi operativi
- **[Troubleshooting](TROUBLESHOOTING.md)** - Soluzioni ai problemi comuni

## 🎯 Panoramica del Sistema

CerCollettiva è una piattaforma Django completa per la gestione delle comunità energetiche rinnovabili in Italia, conforme alle normative vigenti (Decreto CACER, TIAD).

### Caratteristiche Principali
- **Gestione CER/CEC**: Costituzione e amministrazione comunità energetiche
- **Monitoraggio IoT**: Integrazione dispositivi smart via MQTT
- **Elaborazione Documenti**: Processing automatico documenti GAUDI
- **Dashboard Real-time**: Visualizzazione dati energetici in tempo reale
- **Compliance GDPR**: Gestione privacy e diritti utenti
- **API REST**: Integrazione con sistemi esterni

### Stack Tecnologico
- **Backend**: Django 5.0 + Python 3.11+
- **Database**: PostgreSQL 14+
- **Cache**: Redis 6+
- **MQTT**: Mosquitto per IoT
- **Frontend**: Bootstrap 5 + Chart.js
- **Deployment**: Docker + Nginx + Gunicorn

## 🚀 Quick Start

### Installazione Rapida
```bash
# Clone repository
git clone https://github.com/atomozero/CerCollettiva.git
cd CerCollettiva

# Setup automatico (Linux/macOS)
chmod +x scripts/setup.sh
./scripts/setup.sh

# Setup automatico (Windows)
.\scripts\setup.ps1

# Avvia server
python manage.py runserver
```

### Accesso
- **Applicazione**: http://127.0.0.1:8000/
- **Admin**: http://127.0.0.1:8000/ceradmin/

## 📖 Guide per Utente

### Per Amministratori
1. **[Setup Iniziale](install/README.md#setup-iniziale)** - Configurazione sistema
2. **[Gestione CER](ARCHITECTURE.md#core-app)** - Creazione e gestione comunità
3. **[Monitoraggio Sistema](DEPLOYMENT_GUIDE.md#monitoring-e-observability)** - Health checks e metriche

### Per Sviluppatori
1. **[Setup Ambiente](DEVELOPER_GUIDE.md#setup-ambiente-di-sviluppo)** - Configurazione sviluppo
2. **[Architettura](ARCHITECTURE.md)** - Comprensione sistema
3. **[API Development](API_DOCUMENTATION.md)** - Sviluppo API
4. **[Testing](DEVELOPER_GUIDE.md#testing)** - Test e quality assurance

### Per DevOps
1. **[Deployment](DEPLOYMENT_GUIDE.md)** - Deploy in produzione
2. **[Sicurezza](SECURITY_GUIDE.md)** - Hardening e compliance
3. **[Monitoring](DEPLOYMENT_GUIDE.md#monitoring-e-observability)** - Observability stack

## 🔧 Configurazione

### Variabili d'Ambiente
Copia `env.example` in `.env` e configura:

```env
# Database
DB_NAME=cercollettiva
DB_USER=cercollettiva_user
DB_PASSWORD=your_password

# MQTT
MQTT_HOST=localhost
MQTT_PORT=1883
MQTT_USER=mqtt_user
MQTT_PASS=mqtt_password

# Sicurezza
SECRET_KEY=your-secret-key
DEBUG=False
```

### Configurazioni Docker
```bash
# Sviluppo
docker-compose up -d

# Produzione
docker-compose -f docker-compose.prod.yml up -d
```

## 🏗️ Architettura

### Moduli Principali
- **Core**: Gestione CER, impianti, membership
- **Energy**: Monitoraggio IoT, MQTT, calcoli energetici
- **Documents**: Elaborazione GAUDI, gestione file
- **Users**: Autenticazione, profili, GDPR
- **Monitoring**: Health checks, metriche sistema

### Flussi di Dati
```
IoT Devices → MQTT Broker → Django App → PostgreSQL
     ↓              ↓           ↓
  Real-time    WebSocket    Dashboard
```

## 🔒 Sicurezza

### Implementazioni Sicurezza
- **Autenticazione**: Django Auth + sessioni sicure
- **Autorizzazione**: Role-based access control
- **Crittografia**: Campi sensibili crittografati
- **HTTPS**: SSL/TLS obbligatorio in produzione
- **GDPR**: Compliance privacy completa

### Best Practices
- Password policy robusta
- Input validation completa
- SQL injection prevention
- XSS protection
- CSRF protection

## 📊 Monitoring

### Health Checks
- **Application**: `/monitoring/health/`
- **Database**: `/monitoring/health/database/`
- **MQTT**: `/monitoring/health/mqtt/`

### Metriche
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

## 🧪 Testing

### Esecuzione Test
```bash
# Tutti i test
python manage.py test

# Test specifici
python manage.py test core
python manage.py test energy

# Con coverage
coverage run --source='.' manage.py test
coverage report
```

### Test Coverage
- **Target**: 80%+ coverage
- **Tipi**: Unit, Integration, E2E
- **Automazione**: CI/CD pipeline

## 🚀 Deployment

### Ambienti Supportati
- **Sviluppo**: SQLite, debug mode
- **Staging**: PostgreSQL, monitoring
- **Produzione**: Full stack, SSL, backup

### Opzioni Deployment
- **Docker**: Containerizzazione completa
- **Tradizionale**: Gunicorn + Nginx
- **Cloud**: AWS, Azure, GCP ready

## 📈 Performance

### Ottimizzazioni
- **Database**: Indici ottimizzati, query efficienti
- **Cache**: Redis per sessioni e dati frequenti
- **Static Files**: WhiteNoise compression
- **MQTT**: Message buffering, deduplication

### Metriche Target
- **Response Time**: < 200ms p95
- **Throughput**: 1000+ req/s
- **Uptime**: 99.9%+

## 🔄 Backup e Recovery

### Backup Automatico
```bash
# Backup giornaliero
0 2 * * * /opt/cercollettiva/scripts/backup.sh

# Restore
./scripts/restore.sh backup_file.tar.gz
```

### Disaster Recovery
- **RTO**: < 4 ore
- **RPO**: < 1 ora
- **Testing**: Mensile

## 🤝 Contribuire

### Come Contribuire
1. Fork del repository
2. Crea feature branch
3. Sviluppa e testa
4. Crea Pull Request

### Standard di Codice
- **Python**: PEP 8, Black formatter
- **Django**: Best practices
- **Git**: Conventional commits
- **Testing**: Coverage 80%+

### Code Review
- **Checklist**: Sicurezza, performance, test
- **Automazione**: CI/CD pipeline
- **Processo**: 2 approvazioni richieste

## 📞 Supporto

### Canali di Supporto
- **GitHub Issues**: Bug e feature requests
- **Discord**: Discussioni e supporto rapido
- **Email**: team@cercollettiva.it

### Documentazione
- **Wiki**: https://github.com/atomozero/CerCollettiva/wiki
- **API Docs**: https://docs.cercollettiva.it/api/
- **Changelog**: [CHANGELOG.md](CHANGELOG.md)

## 📄 Licenza

Questo progetto è rilasciato sotto licenza MIT. Vedi [LICENSE](LICENSE) per dettagli.

## 🙏 Ringraziamenti

- **Comunità Django**: Framework e best practices
- **Contributors**: Tutti i contributori al progetto
- **Utenti**: Feedback e testing continuo

---

**CerCollettiva - Energia Condivisa, Futuro Sostenibile** ⚡🌱

Per domande o supporto, non esitare a contattarci!