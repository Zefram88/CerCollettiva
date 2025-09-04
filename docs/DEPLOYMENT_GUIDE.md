# Guida al Deployment CerCollettiva

## Panoramica

Questa guida fornisce istruzioni dettagliate per il deployment di CerCollettiva in diversi ambienti, dalla configurazione di sviluppo alla produzione enterprise.

## Architettura di Deployment

### Componenti Principali
- **Django Application**: Applicazione web principale
- **PostgreSQL**: Database principale
- **Redis**: Cache e sessioni
- **MQTT Broker**: Comunicazione IoT
- **Nginx**: Reverse proxy e load balancer
- **Gunicorn**: WSGI server
- **Celery**: Task asincroni
- **Monitoring**: Prometheus + Grafana

### Diagramma Architetturale
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Internet    │    │   Load Balancer │    │   Web Servers   │
│                 │────│     (Nginx)     │────│   (Gunicorn)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                │                        │
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Application   │    │   Background    │
                       │     Servers     │    │     Workers     │
                       │   (Django)      │    │    (Celery)     │
                       └─────────────────┘    └─────────────────┘
                                │                        │
                                │                        │
                       ┌─────────────────┐    ┌─────────────────┐
                       │    Database     │    │   Message       │
                       │  (PostgreSQL)   │    │   Broker        │
                       │                 │    │   (Redis)       │
                       └─────────────────┘    └─────────────────┘
                                │                        │
                                │                        │
                       ┌─────────────────┐    ┌─────────────────┐
                       │   File Storage  │    │   IoT Devices   │
                       │   (Media)       │    │   (MQTT)        │
                       └─────────────────┘    └─────────────────┘
```

## Ambienti di Deployment

### 1. Sviluppo Locale

#### Prerequisiti
- Python 3.11+
- PostgreSQL 14+
- Redis 6+
- Git

#### Setup
```bash
# Clone repository
git clone https://github.com/atomozero/CerCollettiva.git
cd CerCollettiva

# Setup automatico
./scripts/setup.sh

# Oppure manuale
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp env.example .env
# Modifica .env per sviluppo locale
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

#### Avvio
```bash
# Server di sviluppo
python manage.py runserver

# Con MQTT (opzionale)
mosquitto -c config/mosquitto/mosquitto.conf
```

### 2. Sviluppo con Docker

#### Prerequisiti
- Docker 20.10+
- Docker Compose 2.0+

#### Setup
```bash
# Setup con Docker
./scripts/setup.sh
# Scegli opzione 2 (Docker)

# Oppure manuale
cp env.example .env
# Modifica .env per Docker
docker-compose up -d
```

#### Servizi Disponibili
- **Web**: http://localhost:8000
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Flower**: http://localhost:5555

### 3. Staging

#### Configurazione
```bash
# Ambiente staging
export DJANGO_SETTINGS_MODULE=cercollettiva.settings.staging
export DEBUG=False
export ALLOWED_HOSTS=staging.cercollettiva.it

# Deploy
git checkout staging
git pull origin staging
docker-compose -f docker-compose.staging.yml up -d
```

#### Caratteristiche
- Database PostgreSQL dedicato
- Cache Redis dedicata
- SSL/HTTPS abilitato
- Monitoring completo
- Backup automatici

### 4. Produzione

#### Prerequisiti
- Server Linux (Ubuntu 20.04+ o CentOS 8+)
- 4+ CPU cores
- 8+ GB RAM
- 100+ GB storage SSD
- Dominio e certificati SSL

#### Setup Server

##### 1. Preparazione Sistema
```bash
# Aggiorna sistema
sudo apt update && sudo apt upgrade -y

# Installa dipendenze
sudo apt install -y python3.11 python3.11-venv python3-pip postgresql-14 redis-server nginx certbot python3-certbot-nginx

# Crea utente applicazione
sudo useradd -m -s /bin/bash cercollettiva
sudo usermod -aG sudo cercollettiva
```

##### 2. Configurazione Database
```bash
# PostgreSQL
sudo -u postgres createuser cercollettiva_user
sudo -u postgres createdb cercollettiva
sudo -u postgres psql -c "ALTER USER cercollettiva_user PASSWORD 'secure_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE cercollettiva TO cercollettiva_user;"
```

##### 3. Configurazione Redis
```bash
# Redis
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Configurazione sicurezza
sudo nano /etc/redis/redis.conf
# requirepass secure_redis_password
sudo systemctl restart redis-server
```

##### 4. Configurazione Nginx
```bash
# Nginx
sudo cp config/nginx/nginx.conf /etc/nginx/nginx.conf
sudo cp config/nginx/conf.d/cercollettiva.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/cercollettiva.conf /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl enable nginx
sudo systemctl start nginx
```

##### 5. SSL/HTTPS
```bash
# Certificati SSL
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
sudo systemctl enable certbot.timer
```

#### Deploy Applicazione

##### 1. Setup Repository
```bash
# Clona repository
sudo -u cercollettiva git clone https://github.com/atomozero/CerCollettiva.git /opt/cercollettiva
cd /opt/cercollettiva

# Setup ambiente
sudo -u cercollettiva python3.11 -m venv venv
sudo -u cercollettiva venv/bin/pip install -r requirements.txt
```

##### 2. Configurazione Ambiente
```bash
# File .env produzione
sudo -u cercollettiva cp env.example .env
sudo -u cercollettiva nano .env

# Configurazione produzione
DEBUG=False
SECRET_KEY=your-super-secret-key-here
DB_PASSWORD=secure_database_password
REDIS_PASSWORD=secure_redis_password
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

##### 3. Setup Database
```bash
# Migrazioni
sudo -u cercollettiva venv/bin/python manage.py migrate
sudo -u cercollettiva venv/bin/python manage.py createsuperuser
sudo -u cercollettiva venv/bin/python manage.py collectstatic --noinput
```

##### 4. Configurazione Gunicorn
```bash
# Systemd service
sudo nano /etc/systemd/system/cercollettiva.service

[Unit]
Description=CerCollettiva Gunicorn daemon
After=network.target

[Service]
User=cercollettiva
Group=cercollettiva
WorkingDirectory=/opt/cercollettiva
Environment="PATH=/opt/cercollettiva/venv/bin"
ExecStart=/opt/cercollettiva/venv/bin/gunicorn --workers 3 --bind unix:/opt/cercollettiva/cercollettiva.sock cercollettiva.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
Restart=on-failure

[Install]
WantedBy=multi-user.target

# Avvia servizio
sudo systemctl daemon-reload
sudo systemctl enable cercollettiva
sudo systemctl start cercollettiva
```

##### 5. Configurazione Celery
```bash
# Celery worker
sudo nano /etc/systemd/system/cercollettiva-celery.service

[Unit]
Description=CerCollettiva Celery Worker
After=network.target

[Service]
Type=forking
User=cercollettiva
Group=cercollettiva
WorkingDirectory=/opt/cercollettiva
Environment="PATH=/opt/cercollettiva/venv/bin"
ExecStart=/opt/cercollettiva/venv/bin/celery -A cercollettiva worker -l info
ExecReload=/bin/kill -s HUP $MAINPID
Restart=on-failure

[Install]
WantedBy=multi-user.target

# Celery beat
sudo nano /etc/systemd/system/cercollettiva-celery-beat.service

[Unit]
Description=CerCollettiva Celery Beat
After=network.target

[Service]
Type=forking
User=cercollettiva
Group=cercollettiva
WorkingDirectory=/opt/cercollettiva
Environment="PATH=/opt/cercollettiva/venv/bin"
ExecStart=/opt/cercollettiva/venv/bin/celery -A cercollettiva beat -l info
ExecReload=/bin/kill -s HUP $MAINPID
Restart=on-failure

[Install]
WantedBy=multi-user.target

# Avvia servizi
sudo systemctl daemon-reload
sudo systemctl enable cercollettiva-celery cercollettiva-celery-beat
sudo systemctl start cercollettiva-celery cercollettiva-celery-beat
```

## Docker Deployment

### Docker Compose Produzione
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  web:
    build:
      context: .
      dockerfile: Dockerfile.prod
    environment:
      - DEBUG=False
      - SECRET_KEY=${SECRET_KEY}
    volumes:
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    depends_on:
      - db
      - redis
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    volumes:
      - static_volume:/var/www/static
      - media_volume:/var/www/media
      - ./config/nginx/nginx.prod.conf:/etc/nginx/nginx.conf
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - web
    restart: unless-stopped

volumes:
  static_volume:
  media_volume:
```

### Dockerfile Produzione
```dockerfile
# Dockerfile.prod
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "cercollettiva.wsgi:application"]
```

## Monitoring e Observability

### Prometheus Configuration
```yaml
# config/prometheus/prometheus.prod.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'cercollettiva'
    static_configs:
      - targets: ['web:8000']
    metrics_path: '/monitoring/metrics/'
```

### Grafana Dashboards
- **Application Metrics**: Request rate, response time, error rate
- **Database Metrics**: Connection pool, query performance
- **System Metrics**: CPU, memory, disk usage
- **Business Metrics**: Energy production, user activity

### Alerting Rules
```yaml
# config/prometheus/alerts.yml
groups:
  - name: cercollettiva
    rules:
      - alert: HighErrorRate
        expr: rate(django_http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
```

## Backup e Disaster Recovery

### Backup Strategy
```bash
# Backup automatico
0 2 * * * /opt/cercollettiva/scripts/backup.sh

# Backup database
pg_dump -h localhost -U cercollettiva_user cercollettiva | gzip > backup_$(date +%Y%m%d).sql.gz

# Backup file media
tar -czf media_backup_$(date +%Y%m%d).tar.gz media/

# Upload S3
aws s3 cp backup_$(date +%Y%m%d).sql.gz s3://cercollettiva-backups/
```

### Disaster Recovery
```bash
# Restore database
gunzip -c backup_20240101.sql.gz | psql -h localhost -U cercollettiva_user cercollettiva

# Restore file media
tar -xzf media_backup_20240101.tar.gz

# Verifica integrità
python manage.py check
python manage.py migrate --check
```

## Security Hardening

### Firewall Configuration
```bash
# UFW
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### SSL/TLS Configuration
```nginx
# nginx SSL config
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
ssl_prefer_server_ciphers off;
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;
```

### Database Security
```sql
-- PostgreSQL hardening
ALTER USER cercollettiva_user CONNECTION LIMIT 20;
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO cercollettiva_user;
```

## Performance Optimization

### Database Optimization
```sql
-- Indici per performance
CREATE INDEX CONCURRENTLY idx_device_measurement_timestamp 
ON energy_devicemeasurement (timestamp DESC);

CREATE INDEX CONCURRENTLY idx_device_measurement_device_timestamp 
ON energy_devicemeasurement (device_id, timestamp DESC);
```

### Cache Configuration
```python
# settings/production.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            }
        }
    }
}
```

### Gunicorn Configuration
```python
# gunicorn.conf.py
bind = "unix:/opt/cercollettiva/cercollettiva.sock"
workers = 3
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
```

## Scaling

### Horizontal Scaling
```yaml
# docker-compose.scale.yml
version: '3.8'

services:
  web:
    deploy:
      replicas: 3
    environment:
      - DJANGO_SETTINGS_MODULE=cercollettiva.settings.production

  nginx:
    volumes:
      - ./config/nginx/nginx.scale.conf:/etc/nginx/nginx.conf
```

### Load Balancer Configuration
```nginx
# nginx load balancer
upstream django {
    server web1:8000;
    server web2:8000;
    server web3:8000;
}

server {
    location / {
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Troubleshooting

### Common Issues

#### Database Connection Issues
```bash
# Verifica connessione
python manage.py dbshell

# Test connessione
psql -h localhost -U cercollettiva_user -d cercollettiva -c "SELECT 1;"
```

#### MQTT Connection Issues
```bash
# Test MQTT
mosquitto_pub -h localhost -t test -m "hello"
mosquitto_sub -h localhost -t test
```

#### Performance Issues
```bash
# Monitor risorse
htop
iotop
netstat -tulpn

# Log analysis
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### Health Checks
```bash
# Application health
curl -f http://localhost:8000/monitoring/health/

# Database health
curl -f http://localhost:8000/monitoring/health/database/

# MQTT health
curl -f http://localhost:8000/monitoring/health/mqtt/
```

## Maintenance

### Regular Maintenance Tasks
```bash
# Aggiornamento sistema
sudo apt update && sudo apt upgrade -y

# Pulizia log
sudo logrotate -f /etc/logrotate.conf

# Pulizia cache
python manage.py shell -c "from django.core.cache import cache; cache.clear()"

# Backup verification
./scripts/backup.sh --verify
```

### Monitoring Checklist
- [ ] CPU usage < 80%
- [ ] Memory usage < 80%
- [ ] Disk usage < 80%
- [ ] Database connections < 80%
- [ ] Error rate < 1%
- [ ] Response time < 200ms
- [ ] MQTT connectivity
- [ ] SSL certificate validity

## Support

### Emergency Contacts
- **System Admin**: admin@cercollettiva.it
- **Development Team**: dev@cercollettiva.it
- **24/7 Support**: +39-XXX-XXX-XXXX

### Escalation Procedures
1. **Level 1**: Check logs and basic troubleshooting
2. **Level 2**: Database and application issues
3. **Level 3**: Infrastructure and security issues
4. **Level 4**: Vendor support and external dependencies

---

**Deployment completato con successo! 🚀**
