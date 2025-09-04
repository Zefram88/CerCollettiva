# Struttura Progetto CerCollettiva

## Panoramica

Questo documento descrive la struttura completa del progetto CerCollettiva dopo la completa strutturazione e organizzazione.

## 📁 Struttura Directory

```
CerCollettiva/
├── 📁 .claude/                    # Configurazioni Claude AI
│   └── 📁 agents/                 # Agenti specializzati
├── 📁 .cursor/                    # Configurazioni Cursor IDE
├── 📁 .github/                    # Configurazioni GitHub
│   └── 📁 workflows/              # CI/CD pipelines
│       ├── ci.yml                 # Pipeline CI/CD principale
│       └── release.yml            # Pipeline release
├── 📁 cercollettiva/              # Configurazioni Django principali
│   ├── 📁 settings/               # Settings per ambiente
│   │   ├── base.py                # Settings base
│   │   ├── local.py               # Settings sviluppo
│   │   └── production.py          # Settings produzione
│   ├── asgi.py                    # ASGI application
│   ├── urls.py                    # URL principali
│   └── wsgi.py                    # WSGI application
├── 📁 config/                     # Configurazioni servizi esterni
│   ├── 📁 grafana/                # Configurazioni Grafana
│   │   ├── 📁 dashboards/         # Dashboard predefinite
│   │   │   └── cercollettiva-overview.json
│   │   └── 📁 provisioning/       # Provisioning automatico
│   │       ├── 📁 dashboards/
│   │       └── 📁 datasources/
│   ├── 📁 mosquitto/              # Configurazioni MQTT
│   │   ├── mosquitto.conf         # Config broker
│   │   ├── passwd                 # File password
│   │   └── acl                    # Access Control List
│   ├── 📁 nginx/                  # Configurazioni Nginx
│   │   ├── nginx.conf             # Config principale
│   │   └── 📁 conf.d/
│   │       └── cercollettiva.conf # Config applicazione
│   └── 📁 prometheus/             # Configurazioni monitoring
│       └── prometheus.yml         # Config Prometheus
├── 📁 core/                       # App principale CER management
│   ├── 📁 admin/                  # Template admin custom
│   ├── 📁 services/               # Servizi business logic
│   ├── 📁 templates/              # Template HTML
│   │   ├── 📁 admin/
│   │   └── 📁 core/
│   ├── 📁 views/                  # Views organizzate
│   │   ├── 📁 api/                # API views
│   │   ├── 📁 mixins/             # Mixins riutilizzabili
│   │   ├── base.py                # View base
│   │   ├── cer.py                 # Views CER
│   │   ├── dashboard.py           # Dashboard views
│   │   ├── document.py            # Document views
│   │   ├── economic.py            # Economic views
│   │   ├── fees.py                # Fees management
│   │   ├── gaudi.py               # GAUDI processing
│   │   ├── mqtt.py                # MQTT views
│   │   ├── plant.py               # Plant views
│   │   └── setup.py               # Setup views
│   ├── admin.py                   # Admin interface
│   ├── apps.py                    # App configuration
│   ├── forms.py                   # Django forms
│   ├── middleware.py              # Custom middleware
│   ├── models.py                  # Modelli business
│   ├── signals.py                 # Django signals
│   └── urls.py                    # URL routing
├── 📁 documents/                  # App gestione documenti
│   ├── 📁 processors/             # Elaboratori documenti
│   │   ├── 📁 utils/              # Utility processing
│   │   └── gaudi.py               # Processor GAUDI
│   ├── 📁 templates/              # Template documenti
│   │   └── 📁 documents/
│   ├── admin.py                   # Admin documents
│   ├── apps.py                    # App configuration
│   ├── forms.py                   # Document forms
│   ├── models.py                  # Document models
│   ├── services.py                # Document services
│   ├── signals.py                 # Document signals
│   ├── tests.py                   # Document tests
│   ├── urls.py                    # Document URLs
│   └── views.py                   # Document views
├── 📁 docs/                       # Documentazione completa
│   ├── 📁 install/                # Guide installazione
│   │   ├── disinstalla_cercollettiva.sh
│   │   ├── install_updated.sh
│   │   ├── install_wsl_debian.sh
│   │   └── install.sh
│   ├── API_DOCUMENTATION.md       # Documentazione API
│   ├── ARCHITECTURE.md            # Architettura sistema
│   ├── CODE_OF_CONDUCT.md         # Codice di condotta
│   ├── DEPLOYMENT_GUIDE.md        # Guida deployment
│   ├── DEVELOPER_GUIDE.md         # Guida sviluppatori
│   ├── monitoring.md              # Guide monitoring
│   ├── README.md                  # Documentazione principale
│   └── SECURITY_GUIDE.md          # Guida sicurezza
├── 📁 energy/                     # App monitoraggio energetico
│   ├── 📁 api/                    # API energy
│   │   ├── exceptions.py          # Eccezioni API
│   │   ├── filters.py             # Filtri API
│   │   ├── mixins.py              # Mixins API
│   │   ├── pagination.py          # Paginazione
│   │   ├── permissions.py         # Permessi API
│   │   ├── serializers.py         # Serializers
│   │   └── throttling.py          # Rate limiting
│   ├── 📁 devices/                # Gestione dispositivi IoT
│   │   ├── 📁 base/               # Classi base device
│   │   ├── 📁 vendors/            # Implementazioni vendor
│   │   │   ├── shelly/            # Dispositivi Shelly
│   │   │   ├── tasmota/           # Dispositivi Tasmota
│   │   │   └── huawei/            # Dispositivi Huawei
│   │   ├── models.py              # Device models
│   │   └── registry.py            # Device registry
│   ├── 📁 management/             # Management commands
│   │   └── 📁 commands/           # Comandi Django
│   ├── 📁 models/                 # Modelli energy
│   │   ├── audit.py               # Modelli audit
│   │   ├── base.py                # Modelli base
│   │   ├── device.py              # Modelli device
│   │   ├── energy.py              # Modelli energy
│   │   ├── metrics.py             # Modelli metrics
│   │   └── mqtt.py                # Modelli MQTT
│   ├── 📁 mqtt/                   # Client MQTT
│   │   ├── 📁 handlers/           # Message handlers
│   │   ├── acl.py                 # Access Control
│   │   ├── auth.py                # Autenticazione MQTT
│   │   ├── client.py              # Client MQTT
│   │   ├── core.py                # Core MQTT
│   │   └── manager.py             # Manager MQTT
│   ├── 📁 services/               # Servizi energy
│   │   ├── device_manager.py      # Device manager
│   │   ├── energy_calculator_aggregations.py
│   │   ├── energy_calculator_base.py
│   │   ├── energy_calculator_cache.py
│   │   ├── energy_calculator_measurements.py
│   │   ├── signals.py             # Energy signals
│   │   └── utils.py               # Utility energy
│   ├── 📁 templates/              # Template energy
│   │   └── 📁 energy/
│   ├── 📁 templatetags/           # Template tags
│   │   ├── energy_extras.py
│   │   └── energy_tags.py
│   ├── 📁 views/                  # Views energy
│   │   ├── 📁 api/                # API views
│   │   ├── dashboard_views.py     # Dashboard views
│   │   ├── debug_views.py         # Debug views
│   │   ├── device_views.py        # Device views
│   │   ├── mqtt_views.py          # MQTT views
│   │   └── plant_views.py         # Plant views
│   ├── admin.py                   # Admin energy
│   ├── apps.py                    # App configuration
│   ├── logging.py                 # Energy logging
│   ├── urls.py                    # Energy URLs
│   └── views.py                   # Energy views
├── 📁 examples/                   # Esempi e template
│   ├── docker-compose.override.yml # Override sviluppo
│   ├── management-commands-example.py # Esempi comandi
│   └── test-data.sql              # Dati di test
├── 📁 monitoring/                 # App monitoring sistema
│   ├── urls.py                    # Monitoring URLs
│   └── views.py                   # Health check views
├── 📁 Normativa/                  # Documenti normativi
│   ├── 2018 DLGS_DIRETTIVA_2018_2001.pdf
│   ├── 2019 DLGS_DIRETTIVA_2019_944_0.pdf
│   ├── 2021 03 12 ADE Risoluzione n.18.pdf
│   ├── 2022 08 04 Arera 390-2022-R-EEL .pdf
│   ├── 2024 07 22 ADE Risoluzione n.37e CER.pdf
│   ├── CACER - ALLEGATO 1 Regole operative CACER def.pdf
│   └── CACER Decreto.pdf
├── 📁 scripts/                    # Script di automazione
│   ├── backup.sh                  # Script backup
│   ├── init-db.sql                # Inizializzazione DB
│   ├── logs.sh                    # Gestione log
│   ├── README.md                  # Documentazione script
│   ├── restart.sh                 # Restart servizi
│   ├── restore.sh                 # Script restore
│   ├── rundev.sh                  # Run sviluppo
│   ├── setup.ps1                  # Setup Windows
│   ├── setup.sh                   # Setup Linux/macOS
│   ├── start_gunicorn.sh          # Start produzione
│   ├── update.sh                  # Update sistema
│   └── validate-setup.sh          # Validazione setup
├── 📁 static/                     # File statici
│   ├── 📁 admin/                  # Statici admin
│   ├── 📁 css/                    # Fogli di stile
│   ├── 📁 energy/                 # Statici energy
│   ├── 📁 images/                 # Immagini
│   ├── 📁 js/                     # JavaScript
│   └── favicon.ico                # Favicon
├── 📁 templates/                  # Template globali
│   ├── base.html                  # Template base
│   ├── base_temp.html             # Template temporaneo
│   └── 📁 core/                   # Template core
│       ├── cer_join.html
│       ├── cer_public_detail.html
│       └── 📁 setup/
├── 📁 tests/                      # Test suite
│   ├── test_models_core.py        # Test modelli core
│   ├── test_models_energy.py      # Test modelli energy
│   ├── test_models_users.py       # Test modelli users
│   └── test_monitoring.py         # Test monitoring
├── 📁 users/                      # App gestione utenti
│   ├── 📁 templates/              # Template users
│   │   └── 📁 users/
│   ├── apps.py                    # App configuration
│   ├── forms.py                   # User forms
│   ├── models.py                  # User models
│   ├── signals.py                 # User signals
│   ├── urls.py                    # User URLs
│   └── views.py                   # User views
├── 📁 utilities/                  # Utility Python
│   ├── create_superuser.py        # Creazione superuser
│   ├── generate_key.py            # Generazione chiavi
│   └── README.md                  # Documentazione utility
├── 📄 .gitignore                  # Git ignore rules
├── 📄 CHANGELOG.md                # Changelog progetto
├── 📄 CONTRIBUTING.md             # Guida contributori
├── 📄 CLAUDE.md                   # Documentazione Claude
├── 📄 docker-compose.yml          # Stack Docker completo
├── 📄 Dockerfile                  # Containerizzazione
├── 📄 env.example                 # Template variabili ambiente
├── 📄 install_dev.sh              # Installazione sviluppo
├── 📄 LICENSE                     # Licenza MIT
├── 📄 manage.py                   # Django management
├── 📄 PROJECT_STRUCTURE.md        # Questo file
├── 📄 pyproject.toml              # Configurazione Python
├── 📄 README.md                   # README principale
├── 📄 requirements.txt            # Dipendenze Python
├── 📄 TROUBLESHOOTING.md          # Guida troubleshooting
└── 📄 screenshot/                 # Screenshot applicazione
    └── homepage V.A.2.png
```

## 📊 Statistiche Progetto

### File e Directory
- **Totale file**: ~200+ file
- **Directory principali**: 15+
- **File di configurazione**: 25+
- **Script di automazione**: 12+
- **File di documentazione**: 15+

### Tipologie File
- **Python**: ~80 file (.py)
- **HTML**: ~30 file (.html)
- **JavaScript**: ~10 file (.js)
- **CSS**: ~8 file (.css)
- **YAML/JSON**: ~15 file
- **Markdown**: ~15 file (.md)
- **SQL**: ~5 file (.sql)
- **Shell**: ~8 file (.sh)

### Configurazioni
- **Docker**: docker-compose.yml, Dockerfile
- **Nginx**: config/nginx/
- **MQTT**: config/mosquitto/
- **Monitoring**: config/grafana/, config/prometheus/
- **CI/CD**: .github/workflows/
- **Python**: pyproject.toml, requirements.txt

## 🏗️ Architettura Modulare

### App Django
1. **core**: Gestione CER, impianti, membership
2. **energy**: Monitoraggio IoT, MQTT, calcoli energetici
3. **documents**: Elaborazione GAUDI, gestione file
4. **users**: Autenticazione, profili, GDPR
5. **monitoring**: Health checks, metriche sistema

### Servizi Esterni
- **PostgreSQL**: Database principale
- **Redis**: Cache e sessioni
- **Mosquitto**: Broker MQTT
- **Nginx**: Reverse proxy
- **Prometheus**: Metriche
- **Grafana**: Dashboard

### Script di Automazione
- **Setup**: Configurazione ambiente
- **Backup**: Backup automatico
- **Restore**: Ripristino backup
- **Validation**: Validazione configurazioni
- **Deployment**: Deploy automatico

## 📚 Documentazione

### Guide Principali
- **README.md**: Panoramica progetto
- **ARCHITECTURE.md**: Architettura sistema
- **DEVELOPER_GUIDE.md**: Guida sviluppatori
- **DEPLOYMENT_GUIDE.md**: Guida deployment
- **SECURITY_GUIDE.md**: Guida sicurezza
- **API_DOCUMENTATION.md**: Documentazione API

### Guide Operative
- **CONTRIBUTING.md**: Guida contributori
- **TROUBLESHOOTING.md**: Risoluzione problemi
- **CHANGELOG.md**: Cronologia modifiche
- **CODE_OF_CONDUCT.md**: Codice di condotta

## 🔧 Configurazioni

### Ambiente di Sviluppo
- **Local**: SQLite, debug mode
- **Docker**: Stack completo con servizi
- **Override**: Configurazioni sviluppo

### Ambiente di Produzione
- **Docker**: Containerizzazione completa
- **Nginx**: Reverse proxy e SSL
- **Monitoring**: Prometheus + Grafana
- **Backup**: Automatico e crittografato

### CI/CD
- **GitHub Actions**: Pipeline automatizzate
- **Testing**: Unit, integration, security
- **Deployment**: Automatico su tag
- **Quality**: Linting, formatting, coverage

## 🚀 Pronto per l'Uso

Il progetto CerCollettiva è ora completamente strutturato e pronto per:

### Sviluppo
- Setup automatico con script
- Ambiente Docker completo
- Documentazione sviluppatori
- Test suite configurata

### Deployment
- Configurazioni produzione
- Monitoring completo
- Backup automatico
- Sicurezza implementata

### Contribuzioni
- Guida contributori
- Standard di codice
- CI/CD pipeline
- Code review process

### Manutenzione
- Script di automazione
- Monitoring e alerting
- Backup e restore
- Troubleshooting guide

---

**CerCollettiva - Struttura Completa e Pronta per l'Uso! 🚀**
