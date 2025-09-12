#!/bin/bash

###########################################
#  CerCollettiva - Installation Script   #
#  Version: 1.2                          #
#  Author: Andrea Bernardi               #
#  Date: Febbraio 2025                   #
#  Modificato: Febbraio 2025             #
###########################################

# Colori per output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Variabile per l'utente di sistema
SYSTEM_USER=""

# Configurazione base (verrà aggiornata dopo aver determinato l'utente)
APP_NAME="CerCollettiva"
APP_ROOT=""  # Sarà impostato in setup_user
APP_PATH=""  # Sarà impostato in setup_user
VENV_PATH="" # Sarà impostato in setup_user
LOGS_PATH="" # Sarà impostato in setup_user
PROJECT_PATH="" # Sarà impostato in setup_user

# Variabili aggiuntive per la configurazione di rete e sicurezza
PUBLIC_DOMAIN=""
PUBLIC_IP=""
USE_SSL=False

# Funzione di logging
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

# Configurazione dell'utente
setup_user() {
    log "Configurazione dell'utente..."
    
    # Determina l'utente corrente
    local current_user=$(whoami)
    
    # Chiedi quale utente utilizzare
    echo -e "Utente corrente: ${GREEN}$current_user${NC}"
    read -p "Vuoi utilizzare l'utente corrente per l'installazione? (s/n): " use_current_user
    
    if [[ "$use_current_user" =~ ^[Ss]$ ]]; then
        SYSTEM_USER="$current_user"
    else
        read -p "Inserisci il nome dell'utente da utilizzare: " SYSTEM_USER
        
        # Verifica che l'utente esista
        if ! id "$SYSTEM_USER" &>/dev/null; then
            error "L'utente $SYSTEM_USER non esiste. Crealo prima di continuare."
        fi
    fi
    
    # Aggiorna i percorsi di configurazione in base all'utente scelto
    APP_ROOT="/home/$SYSTEM_USER"
    APP_PATH="$APP_ROOT/$APP_NAME"
    VENV_PATH="$APP_PATH/venv"
    LOGS_PATH="$APP_PATH/logs"
    PROJECT_PATH="$APP_PATH/app"
    
    log "L'installazione verrà eseguita per l'utente: ${GREEN}$SYSTEM_USER${NC}"
    log "Directory di installazione: $APP_PATH"
}

# Verifica prerequisiti
check_prerequisites() {
    log "Verifica prerequisiti..."
    
    # Verifica utente non root
    if [ "$EUID" -eq 0 ]; then
        error "Non eseguire questo script come root"
    fi

    # Verifica presenza cartella app
    if [ ! -d "./app" ]; then
        error "Directory 'app' non trovata. Assicurati di essere nella directory corretta"
    fi

    # Verifica spazio disponibile
    local available_space=$(df -m "$APP_ROOT" | awk 'NR==2 {print $4}')
    if [ "$available_space" -lt 1000 ]; then
        error "Spazio su disco insufficiente (< 1GB)"
    fi

    # Verifica connessione internet
    if ! ping -c 1 8.8.8.8 &> /dev/null; then
        error "Connessione Internet non disponibile"
    fi
}

# Raccolta informazioni per l'esposizione su internet
collect_network_info() {
    log "Raccolta informazioni per l'esposizione su internet..."
    
    # Chiedi all'utente se vuole esporre l'applicazione su internet
    read -p "Vuoi esporre l'applicazione su internet? (s/n): " expose_online
    if [[ "$expose_online" =~ ^[Ss]$ ]]; then
        # Chiedi informazioni sul dominio o IP pubblico
        read -p "Hai un dominio per questa applicazione? (s/n): " has_domain
        if [[ "$has_domain" =~ ^[Ss]$ ]]; then
            read -p "Inserisci il tuo dominio (es. cercollettiva.example.com): " PUBLIC_DOMAIN
        else
            read -p "Inserisci il tuo indirizzo IP pubblico: " PUBLIC_IP
        fi
        
        # Chiedi se configurare SSL/HTTPS
        read -p "Vuoi configurare SSL/HTTPS per una connessione sicura? (s/n): " configure_ssl
        if [[ "$configure_ssl" =~ ^[Ss]$ ]]; then
            USE_SSL=True
        fi
    fi
}

# Installazione dipendenze
install_dependencies() {
    log "Installazione dipendenze di sistema..."
    
    sudo apt update
    sudo DEBIAN_FRONTEND=noninteractive apt install -y \
        python3-pip \
        python3-venv \
        nginx \
        postgresql \
        postgresql-contrib \
        supervisor \
        mosquitto \
        mosquitto-clients

    # Installa certbot per SSL se richiesto
    if [ "$USE_SSL" = true ]; then
        sudo apt install -y certbot python3-certbot-nginx
    fi

    if [ $? -ne 0 ]; then
        error "Errore durante l'installazione delle dipendenze"
    fi
}

# Setup ambiente virtuale e dipendenze Python
setup_virtualenv() {
    log "Configurazione ambiente virtuale Python..."
    
    # Crea la directory principale se non esiste
    if [ ! -d "$APP_PATH" ]; then
        mkdir -p "$APP_PATH"
    fi
    
    # Crea e attiva l'ambiente virtuale
    python3 -m venv "$VENV_PATH"
    source "$VENV_PATH/bin/activate"
    
    pip install --upgrade pip wheel setuptools
    pip install -r "$PROJECT_PATH/requirements.txt"
    
    if [ $? -ne 0 ]; then
        error "Errore durante l'installazione delle dipendenze Python"
    fi
}

setup_database() {
    log "Configurazione PostgreSQL..."
    
    # Genera una password sicura per il database
    local db_password=$(openssl rand -base64 12)
    
    # Crea utente e database
    sudo -u postgres psql -c "CREATE USER cercollettiva WITH PASSWORD '${db_password}';"
    sudo -u postgres psql -c "CREATE DATABASE cercollettiva OWNER cercollettiva;"
    sudo -u postgres psql -c "ALTER USER cercollettiva CREATEDB;"
    
    # Salva la password in un file separato per uso successivo
    echo "DB_PASSWORD=${db_password}" > "$APP_PATH/.env"
    chmod 600 "$APP_PATH/.env"
}

# Funzione per configurare le impostazioni Django
configure_django_settings() {
    log "Configurazione impostazioni Django..."
    
    local settings_dir="$PROJECT_PATH/cercollettiva/settings"
    local settings_file="$settings_dir/local.py"
    
    # Crea la directory settings se non esiste
    mkdir -p "$settings_dir"
    touch "$settings_dir/__init__.py"
    
    # Genera chiavi segrete
    local django_secret_key=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
    local field_encryption_key=$(python -c '
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
')

    # Prepara l'array ALLOWED_HOSTS
    local allowed_hosts="['localhost', '127.0.0.1', '$(hostname -I | cut -d' ' -f1)'"
    
    if [ -n "$PUBLIC_DOMAIN" ]; then
        allowed_hosts="$allowed_hosts, '$PUBLIC_DOMAIN'"
    fi
    
    if [ -n "$PUBLIC_IP" ]; then
        allowed_hosts="$allowed_hosts, '$PUBLIC_IP'"
    fi
    
    allowed_hosts="$allowed_hosts]"
    
    # Prepara la lista CSRF_TRUSTED_ORIGINS se SSL è abilitato
    local csrf_trusted_origins=""
    if [ "$USE_SSL" = true ] && [ -n "$PUBLIC_DOMAIN" ]; then
        csrf_trusted_origins="CSRF_TRUSTED_ORIGINS = ['https://$PUBLIC_DOMAIN']"
    elif [ "$USE_SSL" = true ] && [ -n "$PUBLIC_IP" ]; then
        csrf_trusted_origins="CSRF_TRUSTED_ORIGINS = ['https://$PUBLIC_IP']"
    elif [ -n "$PUBLIC_DOMAIN" ]; then
        csrf_trusted_origins="CSRF_TRUSTED_ORIGINS = ['http://$PUBLIC_DOMAIN']"
    elif [ -n "$PUBLIC_IP" ]; then
        csrf_trusted_origins="CSRF_TRUSTED_ORIGINS = ['http://$PUBLIC_IP']"
    fi
    
    # Leggi password DB dal file .env
    source "$APP_PATH/.env"
    
    # Crea file settings/local.py
    cat > "$settings_file" << EOL
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = '${django_secret_key}'
FIELD_ENCRYPTION_KEY = '${field_encryption_key}'
DEBUG = False

ALLOWED_HOSTS = $allowed_hosts
$csrf_trusted_origins

# Impostazioni di sicurezza dei cookie
SESSION_COOKIE_SECURE = ${USE_SSL}
CSRF_COOKIE_SECURE = ${USE_SSL}
SECURE_SSL_REDIRECT = ${USE_SSL}
SECURE_HSTS_SECONDS = 31536000 if ${USE_SSL} else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = ${USE_SSL}
SECURE_HSTS_PRELOAD = ${USE_SSL}
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https') if ${USE_SSL} else None

# Sicurezza aggiuntiva
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'encrypted_model_fields',
    'widget_tweaks',
    'crispy_forms',
    'crispy_bootstrap5',
    'rest_framework',
    'channels',
    'core',
    'energy',
    'users',
    'documents',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'cercollettiva.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'cercollettiva.wsgi.application'
ASGI_APPLICATION = 'cercollettiva.asgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'cercollettiva',
        'USER': 'cercollettiva',
        'PASSWORD': '${DB_PASSWORD}',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Impostazioni per crittografia dei dati sensibili
ENCRYPTED_FIELDS_KEYDIR = os.path.join(BASE_DIR, 'keydir')

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 10}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

AUTH_USER_MODEL = 'users.CustomUser'

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Impostazioni di sicurezza per il superamento del GDPR
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB

# Impostazioni di logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': os.path.join('${LOGS_PATH}', 'django.log'),
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'WARNING',
            'propagate': True,
        },
    },
}
EOL

    # Configurazione directory per le chiavi di crittografia
    mkdir -p "$PROJECT_PATH/keydir"
    chmod 700 "$PROJECT_PATH/keydir"
    
    # Aggiorna la configurazione MQTT
    local mqtt_file="$settings_dir/mqtt.py"
    local mqtt_password=$(openssl rand -base64 12)
    cat > "$mqtt_file" << EOL
MQTT_BROKER = 'localhost'
MQTT_PORT = 1883
MQTT_USERNAME = 'cercollettiva'
MQTT_PASSWORD = '${mqtt_password}'
EOL

    chmod 600 "$settings_file"
    chmod 600 "$mqtt_file"
    
    # Salva mqtt password in .env
    echo "MQTT_PASSWORD=${mqtt_password}" >> "$APP_PATH/.env"
}

setup_django() {
    log "Configurazione Django..."
    
    # Configura le impostazioni
    configure_django_settings
    
    # Crea directory necessarie
    mkdir -p "$PROJECT_PATH/media"
    mkdir -p "$PROJECT_PATH/staticfiles"
    mkdir -p "$LOGS_PATH"
    
    # Imposta i permessi corretti
    sudo chown -R $SYSTEM_USER:$SYSTEM_USER "$APP_PATH"
    
    # Inizializza database
    source "$VENV_PATH/bin/activate"
    cd "$PROJECT_PATH"
    
    # Assicurati che tutte le app abbiano le loro migrazioni
    python manage.py makemigrations users
    python manage.py makemigrations core
    python manage.py makemigrations energy
    python manage.py makemigrations documents
    
    # Applica le migrazioni nell'ordine corretto
    python manage.py migrate users
    python manage.py migrate auth
    python manage.py migrate admin
    python manage.py migrate contenttypes
    python manage.py migrate sessions
    python manage.py migrate core
    python manage.py migrate energy
    python manage.py migrate documents
    
    # Raccolta file statici
    python manage.py collectstatic --noinput
    
    # Crea superuser
    echo -e "\nCreazione account amministratore"
    python manage.py createsuperuser
}

# Configurazione Nginx
setup_nginx() {
    log "Configurazione Nginx..."
    
    local protocol="http"
    local server_name="_"
    
    # Configura il server_name basato sul dominio o IP pubblico
    if [ -n "$PUBLIC_DOMAIN" ]; then
        server_name="$PUBLIC_DOMAIN"
    elif [ -n "$PUBLIC_IP" ]; then
        server_name="$PUBLIC_IP"
    fi
    
    # Crea la configurazione Nginx 
    sudo tee /etc/nginx/sites-available/cercollettiva > /dev/null << EOL
server {
    listen 80;
    server_name ${server_name};
    
    # Logging
    access_log /var/log/nginx/cercollettiva_access.log;
    error_log /var/log/nginx/cercollettiva_error.log;
    
    # Limitazione della dimensione del corpo delle richieste
    client_max_body_size 10M;
    
    # Configurazione dei file statici
    location /static/ {
        alias $PROJECT_PATH/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, max-age=2592000";
    }

    location /media/ {
        alias $PROJECT_PATH/media/;
        expires 7d;
        add_header Cache-Control "public, max-age=604800";
    }

    # Proxy per l'applicazione Django
    location / {
        proxy_set_header Host \$http_host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Impostazioni di sicurezza
        proxy_cookie_path / "/; HTTPOnly; Secure";
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header X-Frame-Options DENY;
    }
}
EOL

    sudo ln -sf /etc/nginx/sites-available/cercollettiva /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default
    sudo systemctl restart nginx
    
    # Configura SSL se richiesto
    if [ "$USE_SSL" = true ]; then
        if [ -n "$PUBLIC_DOMAIN" ]; then
            sudo certbot --nginx -d "$PUBLIC_DOMAIN" --non-interactive --agree-tos --email admin@"$PUBLIC_DOMAIN" --redirect
        elif [ -n "$PUBLIC_IP" ]; then
            log "${RED}AVVISO: Non è possibile ottenere un certificato SSL per un indirizzo IP. SSL non configurato.${NC}"
            log "${RED}Si consiglia di utilizzare un nome di dominio per una configurazione SSL sicura.${NC}"
        fi
    fi
}

# Configurazione Gunicorn
setup_gunicorn() {
    log "Configurazione Gunicorn..."
    
    sudo tee /etc/systemd/system/gunicorn.service > /dev/null << EOL
[Unit]
Description=CerCollettiva Gunicorn Daemon
After=network.target postgresql.service

[Service]
User=$SYSTEM_USER
Group=www-data
WorkingDirectory=$PROJECT_PATH
Environment="PATH=$VENV_PATH/bin"
Environment="DJANGO_SETTINGS_MODULE=cercollettiva.settings.local"
ExecStart=$VENV_PATH/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 cercollettiva.wsgi:application
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
EOL

    sudo systemctl daemon-reload
    sudo systemctl start gunicorn
    sudo systemctl enable gunicorn
}

# Configurazione MQTT
setup_mqtt() {
    log "Configurazione MQTT..."
    
    # Estrai le credenziali MQTT dal file .env
    source "$APP_PATH/.env"
    local mqtt_user="cercollettiva"
    
    sudo mosquitto_passwd -c /etc/mosquitto/passwd "$mqtt_user" "$MQTT_PASSWORD"
    
    sudo tee /etc/mosquitto/conf.d/default.conf > /dev/null << EOL
listener 1883 localhost
allow_anonymous false
password_file /etc/mosquitto/passwd

# Logging
log_dest file /var/log/mosquitto/mosquitto.log
connection_messages true
log_timestamp true
EOL

    # Assicura che il servizio Mosquitto sia configurato correttamente
    sudo systemctl restart mosquitto
    sudo systemctl enable mosquitto
}

# Configurazione Supervisor per processi MQTT
setup_supervisor() {
    log "Configurazione Supervisor..."
    
    sudo tee /etc/supervisor/conf.d/cercollettiva.conf > /dev/null << EOL
[program:cercollettiva_mqtt]
command=$VENV_PATH/bin/python $PROJECT_PATH/manage.py mqtt_client
directory=$PROJECT_PATH
user=$SYSTEM_USER
environment=DJANGO_SETTINGS_MODULE=cercollettiva.settings.local
autostart=true
autorestart=true
startretries=3
stdout_logfile=$LOGS_PATH/mqtt.log
stderr_logfile=$LOGS_PATH/mqtt_error.log
EOL

    sudo supervisorctl reread
    sudo supervisorctl update
}

# Configurazione del firewall
setup_firewall() {
    log "Configurazione del firewall..."
    
    # Installa ufw se non è presente
    if ! command -v ufw &> /dev/null; then
        sudo apt install -y ufw
    fi
    
    # Configura regole di base
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    
    # Consenti SSH
    sudo ufw allow ssh
    
    # Consenti HTTP e HTTPS
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    
    # Limita l'accesso MQTT solo al localhost
    sudo ufw deny 1883/tcp
    
    # Abilita il firewall
    sudo ufw --force enable
}

# Verifica e aggiunge l'utente al gruppo www-data se necessario
setup_user_permissions() {
    log "Configurazione dei permessi dell'utente..."
    
    # Aggiungi l'utente al gruppo www-data se non è già presente
    if ! groups "$SYSTEM_USER" | grep -q www-data; then
        sudo usermod -a -G www-data "$SYSTEM_USER"
        log "Utente $SYSTEM_USER aggiunto al gruppo www-data"
    fi
    
    # Assicurati che l'utente abbia accesso alle directory necessarie
    sudo chown -R "$SYSTEM_USER":www-data "$APP_PATH"
    sudo chmod -R 750 "$APP_PATH"
    sudo chmod -R 770 "$PROJECT_PATH/media"
    sudo chmod -R 770 "$LOGS_PATH"
}

# Funzione principale
main() {
    echo -e "${GREEN}=== Installazione CerCollettiva ===${NC}"
    
    setup_user
    check_prerequisites
    collect_network_info
    install_dependencies
    setup_virtualenv
    setup_database
    setup_django
    setup_user_permissions
    setup_nginx
    setup_gunicorn
    setup_mqtt
    setup_supervisor
    setup_firewall
    
    echo -e "\n${GREEN}=== Installazione completata! ===${NC}"
    
    # Mostra le informazioni di accesso all'applicazione
    if [ "$USE_SSL" = true ] && [ -n "$PUBLIC_DOMAIN" ]; then
        echo -e "Accedi all'applicazione: https://$PUBLIC_DOMAIN"
        echo -e "Pannello admin: https://$PUBLIC_DOMAIN/admin"
    elif [ -n "$PUBLIC_DOMAIN" ]; then
        echo -e "Accedi all'applicazione: http://$PUBLIC_DOMAIN"
        echo -e "Pannello admin: http://$PUBLIC_DOMAIN/admin"
    elif [ "$USE_SSL" = true ] && [ -n "$PUBLIC_IP" ]; then
        echo -e "Accedi all'applicazione: https://$PUBLIC_IP"
        echo -e "Pannello admin: https://$PUBLIC_IP/admin"
    elif [ -n "$PUBLIC_IP" ]; then
        echo -e "Accedi all'applicazione: http://$PUBLIC_IP"
        echo -e "Pannello admin: http://$PUBLIC_IP/admin"
    else
        echo -e "Accedi all'applicazione: http://$(hostname -I | cut -d' ' -f1)"
        echo -e "Pannello admin: http://$(hostname -I | cut -d' ' -f1)/admin"
    fi
    
    echo -e "\n${BLUE}=== Informazioni di sicurezza ===${NC}"
    echo -e "Assicurati di configurare un backup regolare del database e dei file di configurazione."
    echo -e "Rivedi periodicamente i log in $LOGS_PATH per identificare eventuali problemi."
    echo -e "Esegui regolarmente gli aggiornamenti di sicurezza con 'sudo apt update && sudo apt upgrade'."
    
    if [ "$USE_SSL" = false ]; then
        echo -e "\n${RED}AVVISO: L'applicazione non è configurata con SSL/HTTPS.${NC}"
        echo -e "${RED}Per una maggiore sicurezza e conformità al GDPR, si consiglia di configurare HTTPS.${NC}"
    fi
}

# Avvio
main
