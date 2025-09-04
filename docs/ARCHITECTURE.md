# Architettura CerCollettiva

## Panoramica del Sistema

CerCollettiva è una piattaforma Django per la gestione delle Comunità Energetiche Rinnovabili (CER) e Comunità Energetiche dei Cittadini (CEC) in Italia. Il sistema integra gestione utenti, monitoraggio energetico IoT, elaborazione documenti GAUDI e compliance normativa.

## Architettura Generale

### Stack Tecnologico
- **Backend**: Django 5.0 + Python 3.11+
- **Database**: PostgreSQL 14+ (produzione) / SQLite (sviluppo)
- **Cache**: Redis per sessioni e cache dati
- **MQTT**: Mosquitto broker per dispositivi IoT
- **WebSocket**: Django Channels per real-time
- **Frontend**: Bootstrap 5 + Chart.js
- **Deployment**: Gunicorn + Nginx

### Moduli Principali

#### 1. Core App (`core/`)
**Responsabilità**: Gestione CER, impianti, membership, dashboard principale
- **Modelli**: CERConfiguration, Plant, CERMembership, Alert
- **Views**: Dashboard, CER management, Plant CRUD
- **Admin**: Interfaccia custom su `/ceradmin/`

#### 2. Energy App (`energy/`)
**Responsabilità**: Monitoraggio IoT, MQTT, calcoli energetici
- **MQTT Client**: Gestione connessioni real-time
- **Device Registry**: Supporto multi-vendor (Shelly, Tasmota, Huawei)
- **Energy Calculator**: Aggregazioni e cache per performance
- **Modelli**: DeviceConfiguration, DeviceMeasurement, EnergyInterval

#### 3. Documents App (`documents/`)
**Responsabilità**: Gestione documenti GAUDI, compliance normativa
- **GAUDI Processor**: Parsing e validazione documenti
- **File Management**: Upload, storage, accesso controllato
- **Modelli**: Document, DocumentAccess

#### 4. Users App (`users/`)
**Responsabilità**: Autenticazione, profili, GDPR compliance
- **Custom User Model**: Estensione Django User
- **GDPR Features**: Consenso, cancellazione, portabilità dati
- **Modelli**: CustomUser con campi aggiuntivi

#### 5. Monitoring App (`monitoring/`)
**Responsabilità**: Health checks, metriche sistema
- **Health Endpoints**: Database, MQTT, servizi esterni
- **Metrics**: Prometheus-compatible endpoints
- **Status Dashboard**: Monitoraggio operativo

## Flussi di Dati

### Flusso MQTT Energy Monitoring
```
IoT Device → MQTT Broker → MQTT Service → Device Manager → Database
                ↓
            Cache Layer ← Energy Calculator ← Aggregations
```

### Flusso Documenti GAUDI
```
Upload → Validation → GAUDI Processor → Plant Creation → Database
   ↓
File Storage → Access Control → User Interface
```

### Flusso Autenticazione
```
User Registration → GDPR Consent → Profile Creation → CER Membership
       ↓
   Session Management → Role-based Access → Feature Access
```

## Pattern Architetturali

### 1. Service Layer Pattern
- **EnergyCalculator**: Logica business per calcoli energetici
- **DeviceManager**: Gestione dispositivi IoT
- **GAUDIProcessor**: Elaborazione documenti normativi

### 2. Repository Pattern
- **DeviceRegistry**: Gestione dispositivi multi-vendor
- **MeasurementRepository**: Accesso dati misurazioni

### 3. Observer Pattern
- **Django Signals**: Eventi sistema (nuovo utente, misurazione)
- **MQTT Handlers**: Gestione messaggi real-time

### 4. Strategy Pattern
- **Vendor-specific Parsers**: Shelly, Tasmota, Huawei
- **Energy Calculation Strategies**: Diversi algoritmi per aggregazioni

## Sicurezza

### Autenticazione e Autorizzazione
- **Django Auth**: Sistema base con estensioni custom
- **Session Management**: Redis-backed sessions
- **Role-based Access**: Staff, CER admin, membri

### Protezione Dati
- **Field Encryption**: Campi sensibili crittografati
- **GDPR Compliance**: Consenso, cancellazione, portabilità
- **Input Validation**: Django forms + validazione custom

### Sicurezza Network
- **HTTPS**: SSL/TLS obbligatorio in produzione
- **CSRF Protection**: Token-based protection
- **XSS Protection**: Template escaping automatico

## Performance

### Database Optimization
- **Indexes**: Ottimizzati per query temporali
- **Connection Pooling**: CONN_MAX_AGE=600
- **Query Optimization**: select_related, prefetch_related

### Caching Strategy
- **Redis Cache**: Sessioni, dati frequenti
- **Energy Calculator Cache**: Aggregazioni pre-calcolate
- **Static Files**: WhiteNoise compression

### MQTT Performance
- **Message Buffering**: Queue-based processing
- **Duplicate Detection**: Cache-based deduplication
- **Circuit Breaker**: Resilienza connessioni

## Scalabilità

### Horizontal Scaling
- **Stateless Design**: Sessioni in Redis
- **Load Balancing**: Nginx upstream
- **Database Replication**: Read replicas supportate

### Vertical Scaling
- **Connection Pooling**: Database connections
- **Memory Management**: Efficient data structures
- **CPU Optimization**: Async MQTT processing

## Monitoring e Observability

### Health Checks
- **Database**: Connection e query performance
- **MQTT**: Broker connectivity
- **Redis**: Cache availability
- **External Services**: GAUDI API, geocoding

### Logging
- **Structured Logging**: JSON format
- **Log Rotation**: 5MB files, 5 backups
- **Log Levels**: DEBUG (dev), INFO (prod)

### Metrics
- **Application Metrics**: Request rate, response time
- **Business Metrics**: Energy production, user activity
- **System Metrics**: CPU, memory, disk usage

## Deployment

### Development
- **Local Setup**: SQLite, debug mode
- **MQTT**: Local Mosquitto broker
- **Redis**: Local instance

### Production
- **PostgreSQL**: Database principale
- **Redis**: Cache e sessioni
- **MQTT**: Broker dedicato
- **Nginx**: Reverse proxy, SSL termination
- **Gunicorn**: WSGI server

### CI/CD
- **GitHub Actions**: Automated testing (da implementare)
- **Docker**: Containerization (da implementare)
- **Blue-Green**: Zero-downtime deployment (da implementare)

## Compliance e Normativa

### GDPR
- **Consenso Esplicito**: Checkbox registrazione
- **Diritti Utente**: Accesso, rettifica, cancellazione
- **Data Minimization**: Solo dati necessari
- **Retention Policy**: Cancellazione automatica

### Normativa Italiana
- **Decreto CACER**: Compliance CER
- **TIAD**: Integrazione rete elettrica
- **Privacy**: Codice Privacy italiano

### Audit Trail
- **MQTT Audit Log**: Tracciamento messaggi
- **User Actions**: Log attività utenti
- **System Events**: Log eventi sistema

## Roadmap Architetturale

### Short Term (3 mesi)
- **Test Coverage**: Aumentare a 80%
- **Security Hardening**: Fix hardcoded secrets
- **Performance**: Query optimization

### Medium Term (6 mesi)
- **Microservices**: Separazione servizi
- **API Gateway**: Centralizzazione API
- **Event Sourcing**: Audit trail completo

### Long Term (12 mesi)
- **Multi-tenant**: Supporto multi-CER
- **ML Integration**: Predictive analytics
- **Blockchain**: Energy trading
