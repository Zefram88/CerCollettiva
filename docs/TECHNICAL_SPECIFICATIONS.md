# 🔧 Technical Specifications - CerCollettiva

## 📋 Overview

Questo documento definisce le specifiche tecniche dettagliate per l'implementazione del sistema CerCollettiva, includendo architettura, API, database schema e componenti software.

## 🏗️ System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CLIENT LAYER                             │
├─────────────────────────────────────────────────────────────┤
│  Web App (React)  │  Mobile App  │  Admin Panel  │  API    │
└─────────────────────────────────────────────────────────────┘
                                │
                                │ HTTPS/REST/GraphQL
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                    API GATEWAY                              │
├─────────────────────────────────────────────────────────────┤
│  Authentication  │  Rate Limiting  │  Load Balancing       │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                  APPLICATION LAYER                          │
├─────────────────────────────────────────────────────────────┤
│  Django REST API  │  Business Logic  │  Background Tasks   │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                    SERVICE LAYER                            │
├─────────────────────────────────────────────────────────────┤
│ Energy Service │ Economic Service │ IoT Service │ GSE Service│
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                     DATA LAYER                              │
├─────────────────────────────────────────────────────────────┤
│ PostgreSQL │ InfluxDB │ Redis │ File Storage │ Message Queue│
└─────────────────────────────────────────────────────────────┘
```

### Microservices Architecture

#### Core Services
1. **User Service**: Gestione utenti e autenticazione
2. **CER Service**: Gestione comunità energetiche
3. **Energy Service**: Calcoli energetici e monitoraggio
4. **Economic Service**: Gestione benefici e pagamenti
5. **IoT Service**: Integrazione dispositivi
6. **Notification Service**: Comunicazioni utenti
7. **Reporting Service**: Generazione report

## 🗄️ Database Schema

### PostgreSQL Schema (Main Database)

```sql
-- Users and Authentication
CREATE TABLE users_customuser (
    id SERIAL PRIMARY KEY,
    username VARCHAR(150) UNIQUE NOT NULL,
    email VARCHAR(254) UNIQUE NOT NULL,
    first_name VARCHAR(150) NOT NULL,
    last_name VARCHAR(150) NOT NULL,
    user_type VARCHAR(20) NOT NULL, -- PRIVATE, BUSINESS, ADMIN
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- CER Configuration
CREATE TABLE core_cerconfiguration (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    primary_substation VARCHAR(255),
    description TEXT,
    logo VARCHAR(100),
    statute_document VARCHAR(100),
    regulation_document VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Plants (Energy Production/Consumption)
CREATE TABLE core_plant (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    pod_code VARCHAR(50) UNIQUE NOT NULL,
    plant_type VARCHAR(20) NOT NULL, -- CONSUMER, PRODUCER, PROSUMER
    owner_id INTEGER REFERENCES users_customuser(id),
    cer_configuration_id INTEGER REFERENCES core_cerconfiguration(id),
    nominal_power DECIMAL(10,2) NOT NULL,
    connection_voltage VARCHAR(50),
    installation_date DATE,
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    address TEXT,
    city VARCHAR(100),
    province VARCHAR(10),
    zip_code VARCHAR(10),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Energy Measurements (Time Series)
CREATE TABLE energy_measurements (
    id SERIAL PRIMARY KEY,
    plant_id INTEGER REFERENCES core_plant(id),
    device_id VARCHAR(100),
    timestamp TIMESTAMP NOT NULL,
    energy_produced DECIMAL(12,4), -- kWh
    energy_consumed DECIMAL(12,4), -- kWh
    power_produced DECIMAL(10,2), -- kW
    power_consumed DECIMAL(10,2), -- kW
    voltage DECIMAL(8,2), -- V
    current DECIMAL(8,2), -- A
    frequency DECIMAL(5,2), -- Hz
    power_factor DECIMAL(4,3),
    raw_data JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Economic Transactions
CREATE TABLE economic_transactions (
    id SERIAL PRIMARY KEY,
    cer_id INTEGER REFERENCES core_cerconfiguration(id),
    plant_id INTEGER REFERENCES core_plant(id),
    transaction_type VARCHAR(50) NOT NULL, -- BENEFIT_DISTRIBUTION, GSE_PAYMENT, FEE
    amount DECIMAL(12,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'EUR',
    description TEXT,
    reference_period_start DATE,
    reference_period_end DATE,
    status VARCHAR(20) DEFAULT 'PENDING', -- PENDING, PROCESSED, FAILED
    payment_method VARCHAR(50),
    payment_reference VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP
);

-- CER Memberships
CREATE TABLE core_cermembership (
    id SERIAL PRIMARY KEY,
    cer_id INTEGER REFERENCES core_cerconfiguration(id),
    user_id INTEGER REFERENCES users_customuser(id),
    role VARCHAR(20) NOT NULL, -- ADMIN, MEMBER, VIEWER
    joined_date DATE DEFAULT CURRENT_DATE,
    is_active BOOLEAN DEFAULT TRUE,
    share_percentage DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(cer_id, user_id)
);
```

### InfluxDB Schema (Time Series Data)

```sql
-- Energy measurements time series
CREATE MEASUREMENT energy_data (
    time TIMESTAMP,
    plant_id INTEGER,
    device_id STRING,
    energy_produced FLOAT,
    energy_consumed FLOAT,
    power_produced FLOAT,
    power_consumed FLOAT,
    voltage FLOAT,
    current FLOAT,
    frequency FLOAT,
    power_factor FLOAT
);

-- Device status time series
CREATE MEASUREMENT device_status (
    time TIMESTAMP,
    device_id STRING,
    plant_id INTEGER,
    status STRING, -- ONLINE, OFFLINE, ERROR
    last_seen TIMESTAMP,
    battery_level FLOAT,
    signal_strength FLOAT
);
```

## 🔌 API Specifications

### REST API Endpoints

#### Authentication
```http
POST /api/auth/login/
POST /api/auth/logout/
POST /api/auth/refresh/
POST /api/auth/register/
```

#### CER Management
```http
GET    /api/cer/                    # List CERs
POST   /api/cer/                    # Create CER
GET    /api/cer/{id}/               # Get CER details
PUT    /api/cer/{id}/               # Update CER
DELETE /api/cer/{id}/               # Delete CER
GET    /api/cer/{id}/members/       # List CER members
POST   /api/cer/{id}/members/       # Add member
DELETE /api/cer/{id}/members/{user_id}/ # Remove member
```

#### Plant Management
```http
GET    /api/plants/                 # List plants
POST   /api/plants/                 # Create plant
GET    /api/plants/{id}/            # Get plant details
PUT    /api/plants/{id}/            # Update plant
DELETE /api/plants/{id}/            # Delete plant
GET    /api/plants/{id}/measurements/ # Get energy data
POST   /api/plants/{id}/measurements/ # Add measurement
```

#### Energy Data
```http
GET    /api/energy/measurements/    # Get energy measurements
POST   /api/energy/measurements/    # Create measurement
GET    /api/energy/aggregations/    # Get aggregated data
GET    /api/energy/predictions/     # Get energy predictions
```

#### Economic Data
```http
GET    /api/economic/transactions/  # List transactions
POST   /api/economic/transactions/  # Create transaction
GET    /api/economic/benefits/      # Calculate benefits
POST   /api/economic/distribute/    # Distribute benefits
GET    /api/economic/reports/       # Generate reports
```

### API Response Format

```json
{
    "success": true,
    "data": {
        "id": 1,
        "name": "CER Milano Centro",
        "code": "CER001",
        "members_count": 25,
        "total_power": 150.5,
        "created_at": "2025-09-04T10:00:00Z"
    },
    "meta": {
        "page": 1,
        "per_page": 20,
        "total": 1
    },
    "errors": []
}
```

## 🔧 Business Logic Components

### Energy Calculator Engine

```python
class EnergyCalculator:
    """Core engine for energy calculations"""
    
    def calculate_autoconsumption(self, plant_id: int, period: str) -> dict:
        """
        Calculate autoconsumption for a plant in a given period
        
        Args:
            plant_id: Plant identifier
            period: Time period (daily, monthly, yearly)
            
        Returns:
            Dict with autoconsumption data
        """
        pass
    
    def calculate_energy_exchange(self, cer_id: int, period: str) -> dict:
        """
        Calculate energy exchange within CER
        
        Args:
            cer_id: CER identifier
            period: Time period
            
        Returns:
            Dict with exchange data
        """
        pass
    
    def calculate_cer_benefits(self, cer_id: int, period: str) -> dict:
        """
        Calculate CER economic benefits
        
        Args:
            cer_id: CER identifier
            period: Time period
            
        Returns:
            Dict with benefits calculation
        """
        pass
```

### Economic Distribution Engine

```python
class EconomicEngine:
    """Engine for economic calculations and distributions"""
    
    def calculate_member_benefits(self, cer_id: int, member_id: int, period: str) -> dict:
        """
        Calculate benefits for a specific member
        
        Args:
            cer_id: CER identifier
            member_id: Member identifier
            period: Time period
            
        Returns:
            Dict with member benefits
        """
        pass
    
    def distribute_benefits(self, cer_id: int, period: str) -> dict:
        """
        Distribute benefits to all CER members
        
        Args:
            cer_id: CER identifier
            period: Time period
            
        Returns:
            Dict with distribution results
        """
        pass
    
    def generate_invoice(self, member_id: int, period: str) -> dict:
        """
        Generate invoice for member
        
        Args:
            member_id: Member identifier
            period: Time period
            
        Returns:
            Dict with invoice data
        """
        pass
```

## 🔌 Integration Specifications

### IoT Device Integration

#### MQTT Topics
```
energy/plant/{plant_id}/device/{device_id}/measurements
energy/plant/{plant_id}/device/{device_id}/status
energy/plant/{plant_id}/device/{device_id}/commands
```

#### Device Message Format
```json
{
    "device_id": "DEVICE001",
    "plant_id": 123,
    "timestamp": "2025-09-04T10:00:00Z",
    "measurements": {
        "energy_produced": 15.5,
        "energy_consumed": 8.2,
        "power_produced": 3.1,
        "power_consumed": 1.6,
        "voltage": 230.5,
        "current": 13.7,
        "frequency": 50.0,
        "power_factor": 0.95
    },
    "status": {
        "battery_level": 85,
        "signal_strength": -45,
        "last_seen": "2025-09-04T10:00:00Z"
    }
}
```

### GSE Integration

#### GSE API Endpoints
```http
GET    /gse/api/v1/plants/          # List plants
POST   /gse/api/v1/plants/          # Register plant
GET    /gse/api/v1/measurements/    # Get measurements
POST   /gse/api/v1/measurements/    # Submit measurements
GET    /gse/api/v1/payments/        # Get payment data
```

## 🚀 Performance Requirements

### Response Time Targets
- **API Endpoints**: <200ms p95
- **Dashboard Load**: <2s initial load
- **Real-time Updates**: <100ms latency
- **Report Generation**: <30s for monthly reports

### Scalability Targets
- **Concurrent Users**: 10,000+
- **Devices**: 100,000+ IoT devices
- **Data Volume**: 1TB+ time series data
- **Transactions**: 1M+ daily transactions

### Availability Targets
- **Uptime**: 99.9%
- **RTO**: <4 hours (Recovery Time Objective)
- **RPO**: <1 hour (Recovery Point Objective)

## 🔒 Security Specifications

### Authentication & Authorization
- **JWT Tokens**: Stateless authentication
- **RBAC**: Role-based access control
- **OAuth 2.0**: Third-party integrations
- **2FA**: Two-factor authentication

### Data Protection
- **Encryption**: AES-256 at rest, TLS 1.3 in transit
- **PII Protection**: GDPR compliance
- **Audit Logging**: Complete audit trail
- **Data Retention**: Configurable retention policies

### API Security
- **Rate Limiting**: Per-user and per-endpoint limits
- **Input Validation**: Comprehensive validation
- **SQL Injection**: Parameterized queries
- **XSS Protection**: Content Security Policy

## 📊 Monitoring & Observability

### Metrics Collection
- **Application Metrics**: Custom business metrics
- **Infrastructure Metrics**: System performance
- **User Metrics**: Usage analytics
- **Error Metrics**: Error rates and types

### Logging Strategy
- **Structured Logging**: JSON format
- **Log Levels**: DEBUG, INFO, WARN, ERROR, FATAL
- **Correlation IDs**: Request tracing
- **Log Aggregation**: Centralized logging

### Alerting Rules
- **Error Rate**: >5% error rate
- **Response Time**: >500ms p95
- **Availability**: <99% uptime
- **Resource Usage**: >80% CPU/Memory

---

**Document Version**: 1.0  
**Last Updated**: 2025-09-04  
**Next Review**: 2025-10-04
