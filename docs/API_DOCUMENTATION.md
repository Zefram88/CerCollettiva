# API Documentation CerCollettiva

## Panoramica

CerCollettiva espone API REST per l'integrazione con sistemi esterni, dispositivi IoT e applicazioni mobile. Le API seguono i principi REST e utilizzano Django REST Framework.

## Autenticazione

### Metodi Supportati
- **Session Authentication**: Per applicazioni web
- **Basic Authentication**: Per integrazioni semplici
- **Token Authentication**: Per API mobile (da implementare)

### Headers Richiesti
```http
Authorization: Basic <base64_encoded_credentials>
Content-Type: application/json
X-CSRFToken: <csrf_token>  # Per session auth
```

## Endpoints Principali

### Core API

#### CER Management
```http
GET    /api/cer/                    # Lista CER
POST   /api/cer/                    # Crea CER
GET    /api/cer/{id}/               # Dettaglio CER
PUT    /api/cer/{id}/               # Aggiorna CER
DELETE /api/cer/{id}/               # Elimina CER
```

#### Plant Management
```http
GET    /api/plants/                 # Lista impianti
POST   /api/plants/                 # Crea impianto
GET    /api/plants/{id}/            # Dettaglio impianto
PUT    /api/plants/{id}/            # Aggiorna impianto
DELETE /api/plants/{id}/            # Elimina impianto
GET    /api/plants/{id}/data/       # Dati energetici impianto
```

#### Membership Management
```http
GET    /api/cer/{id}/members/       # Lista membri CER
POST   /api/cer/{id}/members/       # Aggiungi membro
GET    /api/cer/{id}/members/{id}/  # Dettaglio membro
PUT    /api/cer/{id}/members/{id}/  # Aggiorna membro
DELETE /api/cer/{id}/members/{id}/  # Rimuovi membro
```

### Energy API

#### Device Management
```http
GET    /api/energy/devices/         # Lista dispositivi
POST   /api/energy/devices/         # Crea dispositivo
GET    /api/energy/devices/{id}/    # Dettaglio dispositivo
PUT    /api/energy/devices/{id}/    # Aggiorna dispositivo
DELETE /api/energy/devices/{id}/    # Elimina dispositivo
GET    /api/energy/devices/{id}/latest_measurement/  # Ultima misurazione
```

#### Measurements
```http
GET    /api/energy/measurements/    # Lista misurazioni
POST   /api/energy/measurements/    # Crea misurazione (bulk)
GET    /api/energy/measurements/latest/  # Ultime misurazioni
GET    /api/energy/measurements/{id}/    # Dettaglio misurazione
```

#### MQTT Data
```http
GET    /api/energy/plants/{id}/mqtt-data/  # Dati MQTT impianto
GET    /api/energy/total-power/            # Potenza totale sistema
```

### Documents API

#### Document Management
```http
GET    /api/documents/              # Lista documenti
POST   /api/documents/              # Upload documento
GET    /api/documents/{id}/         # Dettaglio documento
DELETE /api/documents/{id}/         # Elimina documento
GET    /api/documents/{id}/download/  # Download documento
```

#### GAUDI Processing
```http
POST   /api/documents/gaudi/process/  # Processa documento GAUDI
GET    /api/documents/gaudi/status/{id}/  # Stato elaborazione
```

### Users API

#### User Management
```http
GET    /api/users/profile/          # Profilo utente corrente
PUT    /api/users/profile/          # Aggiorna profilo
POST   /api/users/register/         # Registrazione utente
POST   /api/users/login/            # Login utente
POST   /api/users/logout/           # Logout utente
```

#### GDPR Compliance
```http
GET    /api/users/data-export/      # Esporta dati utente
DELETE /api/users/account/          # Cancella account
POST   /api/users/consent/          # Gestione consensi
```

### Monitoring API

#### Health Checks
```http
GET    /monitoring/health/          # Health check generale
GET    /monitoring/health/database/ # Health check database
GET    /monitoring/health/mqtt/     # Health check MQTT
GET    /monitoring/status/          # Status sistema
GET    /monitoring/metrics/         # Metriche Prometheus
```

## Modelli Dati

### CER Configuration
```json
{
  "id": 1,
  "name": "CER Milano Centro",
  "code": "CER001",
  "vat_number": "12345678901",
  "address": "Via Roma 1",
  "city": "Milano",
  "province": "MI",
  "zip_code": "20100",
  "email": "info@cermilano.it",
  "phone": "+390212345678",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### Plant
```json
{
  "id": 1,
  "name": "Impianto Solare Via Milano",
  "code": "PLANT001",
  "type": "PHOTOVOLTAIC",
  "power_kw": 100.50,
  "address": "Via Milano 10",
  "city": "Milano",
  "province": "MI",
  "zip_code": "20100",
  "latitude": 45.4642,
  "longitude": 9.1900,
  "owner": 1,
  "cer": 1,
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Device Configuration
```json
{
  "id": 1,
  "device_id": "SHELLY_EM_001",
  "name": "Smart Meter 1",
  "device_type": "METER",
  "vendor": "SHELLY",
  "model": "EM",
  "plant": 1,
  "is_active": true,
  "configuration": {
    "ip_address": "192.168.1.100",
    "polling_interval": 60,
    "mqtt_topic": "cercollettiva/shelly/SHELLY_EM_001"
  },
  "last_seen": "2024-01-01T12:00:00Z"
}
```

### Device Measurement
```json
{
  "id": 1,
  "device": 1,
  "plant": 1,
  "measurement_type": "POWER",
  "timestamp": "2024-01-01T12:00:00Z",
  "power": 2500.0,
  "voltage": 230.0,
  "current": 10.87,
  "power_factor": 0.95,
  "frequency": 50.0,
  "quality": "GOOD",
  "phase_details": [
    {
      "phase": "L1",
      "voltage": 230.0,
      "current": 3.62,
      "power": 833.33
    }
  ]
}
```

### User Profile
```json
{
  "id": 1,
  "username": "mario.rossi",
  "email": "mario.rossi@email.com",
  "first_name": "Mario",
  "last_name": "Rossi",
  "fiscal_code": "RSSMRA80A01H501X",
  "phone": "+393331234567",
  "address": "Via Roma 1",
  "city": "Milano",
  "province": "MI",
  "zip_code": "20100",
  "is_active": true,
  "date_joined": "2024-01-01T00:00:00Z",
  "last_login": "2024-01-01T12:00:00Z"
}
```

## Filtri e Ricerca

### Filtri Supportati
```http
# Filtri temporali
?created_after=2024-01-01
?created_before=2024-12-31
?timestamp_after=2024-01-01T00:00:00Z

# Filtri geografici
?city=Milano
?province=MI
?latitude_min=45.0&latitude_max=46.0

# Filtri di stato
?is_active=true
?quality=GOOD
?device_type=METER

# Filtri di appartenenza
?owner=1
?cer=1
?plant=1
```

### Ordinamento
```http
# Ordinamento semplice
?ordering=name
?ordering=-created_at

# Ordinamento multiplo
?ordering=cer,name
?ordering=-timestamp,device
```

### Paginazione
```http
# Paginazione standard
?page=1&page_size=20

# Cursor pagination (per grandi dataset)
?cursor=eyJpZCI6MTB9
```

## Rate Limiting

### Limiti Applicati
- **Anonymous**: 100 richieste/giorno
- **Authenticated**: 1000 richieste/giorno
- **API Key**: 10000 richieste/giorno (da implementare)

### Headers di Risposta
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

## Errori e Codici di Stato

### Codici di Stato HTTP
- **200 OK**: Richiesta completata con successo
- **201 Created**: Risorsa creata con successo
- **400 Bad Request**: Richiesta malformata
- **401 Unauthorized**: Autenticazione richiesta
- **403 Forbidden**: Accesso negato
- **404 Not Found**: Risorsa non trovata
- **429 Too Many Requests**: Rate limit superato
- **500 Internal Server Error**: Errore server

### Formato Errori
```json
{
  "error": "Validation failed",
  "detail": "I campi richiesti non sono stati forniti",
  "code": "VALIDATION_ERROR",
  "fields": {
    "name": ["Questo campo è obbligatorio"],
    "email": ["Inserire un indirizzo email valido"]
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "request_id": "req_123456789"
}
```

## Webhook e Eventi

### Eventi Supportati (da implementare)
- **user.registered**: Nuovo utente registrato
- **plant.created**: Nuovo impianto creato
- **measurement.received**: Nuova misurazione ricevuta
- **device.offline**: Dispositivo offline
- **document.processed**: Documento elaborato

### Formato Webhook
```json
{
  "event": "measurement.received",
  "timestamp": "2024-01-01T12:00:00Z",
  "data": {
    "device_id": "SHELLY_EM_001",
    "plant_id": 1,
    "power": 2500.0,
    "timestamp": "2024-01-01T12:00:00Z"
  },
  "signature": "sha256=abc123..."
}
```

## SDK e Librerie

### Python SDK (da implementare)
```python
from cercollettiva import CerCollettivaClient

client = CerCollettivaClient(
    base_url="https://api.cercollettiva.it",
    api_key="your_api_key"
)

# Crea impianto
plant = client.plants.create({
    "name": "Impianto Solare",
    "type": "PHOTOVOLTAIC",
    "power_kw": 100.0
})

# Ottieni misurazioni
measurements = client.measurements.list(
    plant_id=plant.id,
    hours=24
)
```

### JavaScript SDK (da implementare)
```javascript
import { CerCollettivaClient } from '@cercollettiva/sdk';

const client = new CerCollettivaClient({
  baseUrl: 'https://api.cercollettiva.it',
  apiKey: 'your_api_key'
});

// Crea impianto
const plant = await client.plants.create({
  name: 'Impianto Solare',
  type: 'PHOTOVOLTAIC',
  powerKw: 100.0
});

// Ottieni misurazioni
const measurements = await client.measurements.list({
  plantId: plant.id,
  hours: 24
});
```

## Testing

### Test Endpoints
```bash
# Health check
curl -X GET https://api.cercollettiva.it/monitoring/health/

# Lista impianti
curl -X GET https://api.cercollettiva.it/api/plants/ \
  -H "Authorization: Basic $(echo -n 'user:pass' | base64)"

# Crea impianto
curl -X POST https://api.cercollettiva.it/api/plants/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Basic $(echo -n 'user:pass' | base64)" \
  -d '{"name": "Test Plant", "type": "PHOTOVOLTAIC", "power_kw": 50.0}'
```

### Postman Collection
Una collection Postman completa è disponibile in `docs/postman/CerCollettiva_API.postman_collection.json`

## Versioning

### Strategia di Versioning
- **URL Versioning**: `/api/v1/`, `/api/v2/`
- **Header Versioning**: `Accept: application/vnd.cercollettiva.v1+json`
- **Backward Compatibility**: Mantenuta per almeno 12 mesi

### Changelog
- **v1.0.0**: Versione iniziale (2024-01-01)
- **v1.1.0**: Aggiunto supporto GAUDI (2024-02-01)
- **v1.2.0**: Aggiunto MQTT real-time (2024-03-01)

## Supporto

### Documentazione
- **API Reference**: https://docs.cercollettiva.it/api/
- **Postman Collection**: Disponibile per download
- **SDK Documentation**: Per Python e JavaScript

### Contatti
- **Email**: api-support@cercollettiva.it
- **GitHub Issues**: https://github.com/atomozero/CerCollettiva/issues
- **Discord**: https://discord.gg/cercollettiva
