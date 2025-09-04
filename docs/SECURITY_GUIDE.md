# Guida alla Sicurezza CerCollettiva

## Panoramica

Questa guida fornisce linee guida complete per la sicurezza di CerCollettiva, coprendo aspetti di sicurezza dell'applicazione, infrastruttura, dati e compliance normativa.

## Framework di Sicurezza

### Principi Fondamentali
- **Defense in Depth**: Multipli livelli di protezione
- **Least Privilege**: Accesso minimo necessario
- **Zero Trust**: Verifica continua dell'identità
- **Privacy by Design**: Privacy integrata fin dall'inizio
- **Security by Default**: Configurazioni sicure di default

### Modello di Minaccia
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Attacchi      │    │   Vulnerabilità │    │   Controlli     │
│   Esterni       │    │   Applicazione  │    │   Sicurezza     │
│                 │    │                 │    │                 │
│ • DDoS          │    │ • SQL Injection │    │ • WAF           │
│ • Bot Attacks   │    │ • XSS           │    │ • Rate Limiting │
│ • Brute Force   │    │ • CSRF          │    │ • Input Val.    │
│ • Phishing      │    │ • Auth Bypass   │    │ • Auth/Author   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Sicurezza Applicazione

### Autenticazione e Autorizzazione

#### Implementazione Sicura
```python
# users/models.py
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator

class CustomUser(AbstractUser):
    username_validator = UnicodeUsernameValidator()
    
    # Campi aggiuntivi per sicurezza
    failed_login_attempts = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    last_password_change = models.DateTimeField(auto_now_add=True)
    
    def is_account_locked(self):
        if self.locked_until:
            return timezone.now() < self.locked_until
        return False
    
    def increment_failed_login(self):
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            self.locked_until = timezone.now() + timedelta(minutes=30)
        self.save()
```

#### Password Security
```python
# settings/base.py
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 12,  # Password lunghe
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
    {
        'NAME': 'users.validators.ComplexPasswordValidator',  # Custom validator
    },
]

# Password hashing
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
]
```

#### Session Security
```python
# settings/production.py
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 3600  # 1 ora

# CSRF Protection
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Strict'
CSRF_USE_SESSIONS = True
```

### Input Validation e Sanitization

#### Form Validation
```python
# users/forms.py
from django import forms
from django.core.validators import RegexValidator
import re

class UserRegistrationForm(forms.ModelForm):
    fiscal_code = forms.CharField(
        validators=[
            RegexValidator(
                regex=r'^[A-Z]{6}[0-9]{2}[A-Z][0-9]{2}[A-Z][0-9]{3}[A-Z]$',
                message='Codice fiscale non valido'
            )
        ]
    )
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Validazione email avanzata
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            raise forms.ValidationError('Formato email non valido')
        return email
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        # Validazione numero telefono
        if not re.match(r'^\+39[0-9]{9,10}$', phone):
            raise forms.ValidationError('Numero telefono non valido')
        return phone
```

#### API Input Validation
```python
# energy/serializers.py
from rest_framework import serializers
from django.core.exceptions import ValidationError

class DeviceMeasurementSerializer(serializers.ModelSerializer):
    def validate_power(self, value):
        if value < 0 or value > 1000000:  # Max 1MW
            raise serializers.ValidationError('Potenza non valida')
        return value
    
    def validate_timestamp(self, value):
        now = timezone.now()
        if value > now:
            raise serializers.ValidationError('Timestamp futuro non valido')
        if value < now - timedelta(days=30):
            raise serializers.ValidationError('Timestamp troppo vecchio')
        return value
```

### SQL Injection Prevention

#### Query Sicure
```python
# ✅ CORRETTO - Query parametrizzate
def get_user_plants(user_id):
    return Plant.objects.filter(owner_id=user_id)

# ✅ CORRETTO - Raw SQL con parametri
def get_energy_data(plant_id, start_date, end_date):
    return DeviceMeasurement.objects.raw(
        "SELECT * FROM energy_devicemeasurement WHERE plant_id = %s AND timestamp BETWEEN %s AND %s",
        [plant_id, start_date, end_date]
    )

# ❌ SBAGLIATO - String formatting
def get_user_plants_unsafe(user_id):
    return Plant.objects.raw(f"SELECT * FROM core_plant WHERE owner_id = {user_id}")
```

### XSS Prevention

#### Template Security
```html
<!-- ✅ CORRETTO - Auto-escaping -->
<div>{{ user_input }}</div>

<!-- ✅ CORRETTO - Safe filter solo se necessario -->
<div>{{ trusted_html|safe }}</div>

<!-- ✅ CORRETTO - Escape manuale -->
<div>{{ user_input|escape }}</div>
```

#### Content Security Policy
```python
# settings/production.py
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net")
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net")
CSP_IMG_SRC = ("'self'", "data:", "https:")
CSP_CONNECT_SRC = ("'self'", "wss:", "ws:")
CSP_FONT_SRC = ("'self'", "https://fonts.gstatic.com")
```

## Sicurezza Infrastruttura

### Network Security

#### Firewall Configuration
```bash
# UFW Configuration
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow from 10.0.0.0/8 to any port 5432  # PostgreSQL solo LAN
sudo ufw allow from 10.0.0.0/8 to any port 6379  # Redis solo LAN
sudo ufw enable
```

#### Nginx Security Headers
```nginx
# config/nginx/conf.d/security.conf
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' ws: wss:;" always;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;
```

### Database Security

#### PostgreSQL Hardening
```sql
-- Configurazione sicura PostgreSQL
-- postgresql.conf
ssl = on
ssl_cert_file = 'server.crt'
ssl_key_file = 'server.key'
ssl_ca_file = 'ca.crt'
password_encryption = scram-sha-256
log_connections = on
log_disconnections = on
log_statement = 'all'
log_min_duration_statement = 1000

-- pg_hba.conf
# TYPE  DATABASE        USER            ADDRESS                 METHOD
local   all             postgres                                peer
local   all             all                                     scram-sha-256
host    all             all             127.0.0.1/32            scram-sha-256
host    all             all             ::1/128                 scram-sha-256
host    cercollettiva   cercollettiva_user 10.0.0.0/8          scram-sha-256
```

#### Database Access Control
```sql
-- Creazione utenti con privilegi limitati
CREATE USER cercollettiva_user WITH PASSWORD 'secure_password';
CREATE USER cercollettiva_readonly WITH PASSWORD 'readonly_password';

-- Privilegi specifici
GRANT CONNECT ON DATABASE cercollettiva TO cercollettiva_user;
GRANT USAGE ON SCHEMA public TO cercollettiva_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO cercollettiva_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO cercollettiva_user;

-- Utente readonly
GRANT CONNECT ON DATABASE cercollettiva TO cercollettiva_readonly;
GRANT USAGE ON SCHEMA public TO cercollettiva_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO cercollettiva_readonly;
```

### MQTT Security

#### Mosquitto Configuration
```conf
# config/mosquitto/mosquitto.conf
# Autenticazione obbligatoria
allow_anonymous false
password_file /mosquitto/config/passwd
acl_file /mosquitto/config/acl

# SSL/TLS
listener 8883
certfile /mosquitto/config/server.crt
keyfile /mosquitto/config/server.key
cafile /mosquitto/config/ca.crt

# Logging
log_dest file /mosquitto/log/mosquitto.log
log_type error
log_type warning
log_type notice
log_type information
```

#### Access Control List
```conf
# config/mosquitto/acl
# Utente applicazione - accesso completo
user cercollettiva
topic readwrite cercollettiva/#

# Utente dispositivi - solo pubblicazione
user iot_device_001
topic write cercollettiva/plant_001/device_001/status/#
topic read cercollettiva/plant_001/device_001/config/#

# Utente monitoring - solo lettura
user monitoring
topic read cercollettiva/+/+/status/#
topic read $SYS/#
```

## Sicurezza Dati

### Crittografia

#### Crittografia Campi Sensibili
```python
# settings/base.py
FIELD_ENCRYPTION_KEY = os.getenv('FIELD_ENCRYPTION_KEY')

# models.py
from encrypted_model_fields.fields import EncryptedCharField, EncryptedEmailField

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    fiscal_code = EncryptedCharField(max_length=16)
    phone = EncryptedCharField(max_length=20)
    email = EncryptedEmailField()
```

#### Crittografia File
```python
# documents/services.py
from cryptography.fernet import Fernet
import os

class DocumentEncryption:
    def __init__(self):
        self.key = os.getenv('DOCUMENT_ENCRYPTION_KEY').encode()
        self.cipher = Fernet(self.key)
    
    def encrypt_file(self, file_path):
        with open(file_path, 'rb') as file:
            data = file.read()
        encrypted_data = self.cipher.encrypt(data)
        with open(f"{file_path}.enc", 'wb') as file:
            file.write(encrypted_data)
        os.remove(file_path)
    
    def decrypt_file(self, encrypted_path):
        with open(encrypted_path, 'rb') as file:
            encrypted_data = file.read()
        decrypted_data = self.cipher.decrypt(encrypted_data)
        return decrypted_data
```

### Backup Security

#### Backup Crittografati
```bash
#!/bin/bash
# scripts/secure_backup.sh

# Genera chiave di crittografia
BACKUP_KEY=$(openssl rand -base64 32)

# Backup database crittografato
pg_dump -h localhost -U cercollettiva_user cercollettiva | \
gzip | \
openssl enc -aes-256-cbc -salt -k "$BACKUP_KEY" > \
"backup_$(date +%Y%m%d).sql.gz.enc"

# Backup file media crittografati
tar -czf - media/ | \
openssl enc -aes-256-cbc -salt -k "$BACKUP_KEY" > \
"media_backup_$(date +%Y%m%d).tar.gz.enc"

# Salva chiave separatamente
echo "$BACKUP_KEY" > "backup_key_$(date +%Y%m%d).txt"
gpg --symmetric --cipher-algo AES256 "backup_key_$(date +%Y%m%d).txt"
rm "backup_key_$(date +%Y%m%d).txt"
```

## GDPR Compliance

### Privacy by Design

#### Data Minimization
```python
# users/models.py
class UserProfile(models.Model):
    # Solo dati necessari
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    fiscal_code = EncryptedCharField(max_length=16)  # Richiesto per CER
    phone = EncryptedCharField(max_length=20, blank=True)  # Opzionale
    address = EncryptedCharField(max_length=200, blank=True)  # Opzionale
    
    # Metadati per GDPR
    data_processing_consent = models.BooleanField(default=False)
    marketing_consent = models.BooleanField(default=False)
    consent_date = models.DateTimeField(auto_now_add=True)
    data_retention_until = models.DateTimeField()
```

#### Right to Erasure
```python
# users/services.py
class GDPRService:
    def anonymize_user_data(self, user):
        """Anonimizza dati utente mantenendo funzionalità sistema"""
        # Anonimizza dati personali
        user.first_name = "ANONYMIZED"
        user.last_name = "ANONYMIZED"
        user.email = f"anonymized_{user.id}@deleted.local"
        user.fiscal_code = "ANONYMIZED"
        user.phone = "ANONYMIZED"
        user.is_active = False
        user.save()
        
        # Anonimizza profilo
        if hasattr(user, 'profile'):
            profile = user.profile
            profile.address = "ANONYMIZED"
            profile.save()
    
    def delete_user_data(self, user):
        """Cancella completamente dati utente"""
        # Cancella misurazioni personali
        DeviceMeasurement.objects.filter(device__plant__owner=user).delete()
        
        # Cancella documenti personali
        Document.objects.filter(uploaded_by=user).delete()
        
        # Cancella utente
        user.delete()
```

### Data Portability
```python
# users/views.py
class DataExportView(LoginRequiredMixin, View):
    def get(self, request):
        user_data = {
            'profile': {
                'username': request.user.username,
                'email': request.user.email,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'date_joined': request.user.date_joined,
            },
            'plants': list(Plant.objects.filter(owner=request.user).values()),
            'measurements': list(DeviceMeasurement.objects.filter(
                device__plant__owner=request.user
            ).values()),
        }
        
        response = JsonResponse(user_data, json_dumps_params={'indent': 2})
        response['Content-Disposition'] = f'attachment; filename="user_data_{request.user.id}.json"'
        return response
```

## Monitoring e Incident Response

### Security Monitoring

#### Log Analysis
```python
# monitoring/security.py
import logging
from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.dispatch import receiver

security_logger = logging.getLogger('security')

@receiver(user_login_failed)
def log_failed_login(sender, credentials, request, **kwargs):
    security_logger.warning(
        f"Failed login attempt for user: {credentials.get('username')} "
        f"from IP: {request.META.get('REMOTE_ADDR')} "
        f"User-Agent: {request.META.get('HTTP_USER_AGENT')}"
    )

@receiver(user_logged_in)
def log_successful_login(sender, request, user, **kwargs):
    security_logger.info(
        f"Successful login for user: {user.username} "
        f"from IP: {request.META.get('REMOTE_ADDR')}"
    )
```

#### Intrusion Detection
```python
# monitoring/intrusion_detection.py
class IntrusionDetector:
    def __init__(self):
        self.failed_attempts = {}
        self.blocked_ips = set()
    
    def check_suspicious_activity(self, request):
        ip = request.META.get('REMOTE_ADDR')
        
        # Conta tentativi falliti
        if ip not in self.failed_attempts:
            self.failed_attempts[ip] = 0
        
        # Se troppi tentativi, blocca IP
        if self.failed_attempts[ip] > 10:
            self.blocked_ips.add(ip)
            return True
        
        return False
```

### Incident Response Plan

#### 1. Detection
```python
# monitoring/incident_detection.py
class IncidentDetector:
    def detect_security_incident(self):
        incidents = []
        
        # Controlla login sospetti
        recent_failed_logins = FailedLogin.objects.filter(
            timestamp__gte=timezone.now() - timedelta(hours=1)
        ).count()
        
        if recent_failed_logins > 100:
            incidents.append({
                'type': 'BRUTE_FORCE_ATTACK',
                'severity': 'HIGH',
                'description': f'{recent_failed_logins} failed login attempts in last hour'
            })
        
        return incidents
```

#### 2. Response
```python
# monitoring/incident_response.py
class IncidentResponse:
    def handle_incident(self, incident):
        if incident['severity'] == 'HIGH':
            # Blocca IP sospetti
            self.block_suspicious_ips()
            
            # Invia notifica
            self.send_alert(incident)
            
            # Log incidente
            self.log_incident(incident)
```

## Security Testing

### Automated Security Tests
```python
# tests/security_tests.py
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()

class SecurityTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='TestPass123!'
        )
    
    def test_sql_injection_protection(self):
        """Test protezione SQL injection"""
        malicious_input = "'; DROP TABLE users; --"
        response = self.client.get(f'/search/?q={malicious_input}')
        self.assertEqual(response.status_code, 200)
        # Verifica che la tabella users esista ancora
        self.assertTrue(User.objects.filter(username='testuser').exists())
    
    def test_xss_protection(self):
        """Test protezione XSS"""
        malicious_script = "<script>alert('XSS')</script>"
        response = self.client.post('/comment/', {
            'content': malicious_script
        })
        self.assertNotContains(response, '<script>')
    
    def test_csrf_protection(self):
        """Test protezione CSRF"""
        response = self.client.post('/admin/users/user/add/', {
            'username': 'hacker',
            'password': 'hacked'
        })
        self.assertEqual(response.status_code, 403)
    
    def test_authentication_required(self):
        """Test che le pagine richiedano autenticazione"""
        response = self.client.get('/admin/')
        self.assertRedirects(response, '/admin/login/?next=/admin/')
```

### Penetration Testing Checklist
- [ ] SQL Injection testing
- [ ] XSS testing
- [ ] CSRF testing
- [ ] Authentication bypass
- [ ] Authorization testing
- [ ] Session management
- [ ] Input validation
- [ ] File upload security
- [ ] API security
- [ ] Infrastructure security

## Compliance e Audit

### Security Audit Checklist
- [ ] **Authentication**: Password policy, account lockout, MFA
- [ ] **Authorization**: Role-based access, least privilege
- [ ] **Data Protection**: Encryption at rest and in transit
- [ ] **Network Security**: Firewall, VPN, network segmentation
- [ ] **Application Security**: Input validation, output encoding
- [ ] **Infrastructure Security**: OS hardening, service configuration
- [ ] **Monitoring**: Logging, alerting, incident response
- [ ] **Backup Security**: Encrypted backups, secure storage
- [ ] **Compliance**: GDPR, industry standards
- [ ] **Documentation**: Security policies, procedures

### Regular Security Tasks
```bash
# Aggiornamento sicurezza
sudo apt update && sudo apt upgrade -y

# Audit sistema
sudo lynis audit system

# Controllo vulnerabilità
sudo apt list --upgradable

# Verifica certificati SSL
openssl x509 -in /etc/ssl/certs/cert.pem -text -noout

# Controllo log sicurezza
sudo grep "Failed password" /var/log/auth.log
sudo grep "Invalid user" /var/log/auth.log
```

## Incident Response

### Security Incident Classification
- **Critical**: Data breach, system compromise
- **High**: Unauthorized access, service disruption
- **Medium**: Suspicious activity, policy violation
- **Low**: Minor security issues, false positives

### Response Procedures
1. **Immediate Response**: Isolate affected systems
2. **Assessment**: Determine scope and impact
3. **Containment**: Prevent further damage
4. **Eradication**: Remove threat
5. **Recovery**: Restore normal operations
6. **Lessons Learned**: Improve security posture

### Contact Information
- **Security Team**: security@cercollettiva.it
- **Incident Response**: +39-XXX-XXX-XXXX
- **External Security**: security@external-provider.com

---

**Sicurezza implementata con successo! 🔒**
