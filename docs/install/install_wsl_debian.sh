#!/bin/bash

###########################################
#  CerCollettiva - Installation Script    #
#  Version: 1.3                           #
#  Author: Andrea Bernardi               #
#  Date: Febbraio 2025                   #
#  Modificato: Marzo 2025 (WSL Version)  #
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
WSL_MODE=true  # Modalità WSL attivata

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
    
    # In WSL, utilizziamo direttamente l'utente corrente
    SYSTEM_USER="$current_user"
    log "WSL rilevato: utilizzo automatico dell'utente corrente: ${GREEN}$SYSTEM_USER${NC}"
    
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

    # Verifica che siamo in WSL
    if ! grep -qi microsoft /proc/version; then
        log "${YELLOW}AVVISO: Questo script è ottimizzato per WSL ma sembra che tu non stia usando WSL.${NC}"
        read -p "Vuoi continuare comunque? (s/n): " continue_anyway
        if [[ ! "$continue_anyway" =~ ^[Ss]$ ]]; then
            error "Installazione annullata."
        fi
        WSL_MODE=false
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

}

# Raccolta informazioni per l'esposizione su internet
collect_network_info() {
    log "Configurazione della rete per WSL..."
    
    # Ottieni l'IP della macchina Windows host
    local windows_ip=$(ip route | grep default | awk '{print $3}')
    log "IP del computer Windows host: ${GREEN}$windows_ip${NC}"
    
    # Utilizzamos l'indirizzo locale per lo sviluppo in WSL
    PUBLIC_IP=$(hostname -I | awk '{print $1}')
    log "IP di WSL: ${GREEN}$PUBLIC_IP${NC}"
    
    # In WSL, generalmente non esponiamo direttamente su internet
    read -p "Vuoi configurare l'applicazione solo per sviluppo locale? (s/n): " local_dev
    if [[ "$local_dev" =~ ^[Ss]$ ]]; then
        log "Configurazione per sviluppo locale. L'applicazione sarà accessibile solo dal tuo computer."
    else
        # Chiedi informazioni sul dominio o IP pubblico
        read -p "Hai un dominio per questa applicazione? (s/n): " has_domain
        if [[ "$has_domain" =~ ^[Ss]$ ]]; then
            read -p "Inserisci il tuo dominio (es. cercollettiva.example.com): " PUBLIC_DOMAIN
            
            # Avviso per la configurazione del port forwarding
            log "${RED}AVVISO: Per rendere l'applicazione accessibile da internet devi configurare:${NC}"
            log "${RED}1. Port forwarding sul tuo router (porte 80/443 -> $windows_ip)${NC}"
            log "${RED}2. Port forwarding in Windows (porte 80/443 -> $PUBLIC_IP)${NC}"
        fi
        
        # Chiedi se configurare SSL/HTTPS
        read -p "Vuoi configurare SSL/HTTPS per una connessione sicura? (s/n): " configure_ssl
        if [[ "$configure_ssl" =~ ^[Ss]$ ]]; then
            USE_SSL=True
            log "${RED}NOTA: Per SSL in WSL potrebbero essere necessarie configurazioni aggiuntive sul sistema Windows host.${NC}"
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
    
    # Verifica se i servizi sono in esecuzione (problematico in WSL)
    check_services
}

# Verifica e avvia i servizi necessari
check_services() {
    log "Verifica e avvio servizi in WSL..."
    
    # In WSL i servizi potrebbero non avviarsi automaticamente
    # Verifica PostgreSQL
    if ! pg_isready &>/dev/null; then
        log "Avvio PostgreSQL..."
        # Prova a inizializzare il cluster PostgreSQL se necessario
        if [ ! -d "/var/lib/postgresql/14/main" ] && [ -d "/usr/lib/postgresql/14" ]; then
            sudo mkdir -p /var/lib/postgresql/14/main
            sudo chown -R postgres:postgres /var/lib/postgresql/14/main
            sudo -u postgres /usr/lib/postgresql/14/bin/initdb -D /var/lib/postgresql/14/main
        fi
        sudo service postgresql start
    fi
    
    # Verifica Nginx
    if ! pgrep nginx &>/dev/null; then
        log "Avvio Nginx..."
        sudo service nginx start
    fi
    
    # Verifica Mosquitto
    if ! pgrep mosquitto &>/dev/null; then
        log "Avvio Mosquitto..."
        sudo service mosquitto start
    fi
    
    # Verifica Supervisor
    if ! pgrep supervisord &>/dev/null; then
        log "Avvio Supervisor..."
        sudo service supervisor start
    fi
    
    # Prompt per l'attivazione automatica all'avvio di WSL
    log "In WSL, i servizi non si avviano automaticamente al riavvio."
    read -p "Vuoi creare uno script di avvio per i servizi? (s/n): " create_startup
    if [[ "$create_startup" =~ ^[Ss]$ ]]; then
        create_startup_script
    fi
}

create_startup_script() {
    local startup_script="$APP_ROOT/start_services.sh"
    
    cat > "$startup_script" << 'EOL'
#!/bin/bash
echo "Avvio servizi per CerCollettiva..."
sudo service postgresql start
sudo service nginx start
sudo service mosquitto start
sudo service supervisor start
sudo service gunicorn start
echo "Servizi avviati!"
EOL

    chmod +x "$startup_script"
    log "Script di avvio creato in ${GREEN}$startup_script${NC}"
    log "Per avviare i servizi all'avvio di WSL, aggiungi queste righe al tuo .bashrc or .zshrc:"
    log "${GREEN}if [ -f ~/start_services.sh ]; then"
    log "    ~/start_services.sh"
    log "fi${NC}"
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
    
    # In ambiente WSL di sviluppo, aggiungiamo l'IP Windows host per maggiore flessibilità
    local windows_ip=$(ip route | grep default | awk '{print $3}')
    allowed_hosts="$allowed_hosts, '$windows_ip'"
    
    allowed_hosts="$allowed_hosts]"
    
    # Attiva DEBUG mode in WSL per il development
    local debug_mode="True" 
    if [ "$WSL_MODE" = true ]; then
        debug_mode="True"
        log "DEBUG attivato per l'ambiente di sviluppo WSL"
    else
        debug_mode="False"
    fi
    
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
DEBUG = ${debug_mode}

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
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
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
    log "Configurazione Nginx per WSL..."
    
    local server_name="_"
    
    # Configura il server_name basato sul dominio o IP pubblico
    if [ -n "$PUBLIC_DOMAIN" ]; then
        server_name="$PUBLIC_DOMAIN"
    elif [ -n "$PUBLIC_IP" ]; then
        server_name="$PUBLIC_IP"
    fi
    
    # Aggiungi l'IP del computer host Windows all'elenco server_name
    local windows_ip=$(ip route | grep default | awk '{print $3}')
    server_name="${server_name} $windows_ip"
    
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
            log "Tentativo di configurazione SSL con Certbot..."
            log "${YELLOW}NOTA: La configurazione SSL in WSL potrebbe richiedere passaggi aggiuntivi.${NC}"
            sudo certbot --nginx -d "$PUBLIC_DOMAIN" --non-interactive --agree-tos --email admin@"$PUBLIC_DOMAIN" --redirect
        elif [ -n "$PUBLIC_IP" ]; then
            log "${RED}AVVISO: Non è possibile ottenere un certificato SSL per un indirizzo IP. SSL non configurato.${NC}"
            log "${RED}Si consiglia di utilizzare un nome di dominio per una configurazione SSL sicura.${NC}"
        fi
    fi
    
    # Istruzioni per il port forwarding in Windows
    log "${YELLOW}IMPORTANTE: Per accedere all'applicazione da Windows, aggiungi al file hosts:${NC}"
    log "${YELLOW}$PUBLIC_IP    cercollettiva.local${NC}"
    log "${YELLOW}Il file hosts si trova in: C:\\Windows\\System32\\drivers\\etc\\hosts${NC}"
}

# Configurazione Gunicorn
setup_gunicorn() {
    log "Configurazione Gunicorn per WSL..."
    
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

    # In WSL systemd non funziona normalmente
    log "In WSL dovremo avviare Gunicorn manualmente (incluso nello script di avvio)"
    
    # Crea uno script per avviare gunicorn manualmente
    cat > "$APP_PATH/start_gunicorn.sh" << EOL
#!/bin/bash
cd $PROJECT_PATH
source $VENV_PATH/bin/activate
export DJANGO_SETTINGS_MODULE=cercollettiva.settings.local
$VENV_PATH/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 cercollettiva.wsgi:application
EOL

    chmod +x "$APP_PATH/start_gunicorn.sh"
    
    # Aggiunge Gunicorn allo script di avvio dei servizi
    local startup_content=$(cat "$APP_ROOT/start_services.sh" 2>/dev/null || echo "#!/bin/bash
echo \"Avvio servizi per CerCollettiva...\"
sudo service postgresql start
sudo service nginx start
sudo service mosquitto start
sudo service supervisor start")
    
    echo "$startup_content
# Avvia Gunicorn in background
nohup $APP_PATH/start_gunicorn.sh > $LOGS_PATH/gunicorn.log 2>&1 &
echo \"Servizi avviati!\"" > "$APP_ROOT/start_services.sh"
    
    chmod +x "$APP_ROOT/start_services.sh"
    
    # Crea un servizio per Gunicorn con supervisord come alternativa
    log "Configurazione di Supervisor per gestire Gunicorn..."
    sudo tee /etc/supervisor/conf.d/gunicorn.conf > /dev/null << EOL
[program:gunicorn]
command=$VENV_PATH/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 cercollettiva.wsgi:application
directory=$PROJECT_PATH
user=$SYSTEM_USER
environment=DJANGO_SETTINGS_MODULE=cercollettiva.settings.local
autostart=true
autorestart=true
startretries=3
stdout_logfile=$LOGS_PATH/gunicorn.log
stderr_logfile=$LOGS_PATH/gunicorn_error.log
EOL

    sudo supervisorctl reread
    sudo supervisorctl update
}

# Configurazione MQTT
setup_mqtt() {
    log "Configurazione MQTT per WSL..."
    
    # Estrai le credenziali MQTT dal file .env
    source "$APP_PATH/.env"
    local mqtt_user="cercollettiva"
    
    # In WSL, è possibile che il file di password non esista ancora
    sudo mkdir -p /etc/mosquitto
    sudo touch /etc/mosquitto/passwd
    
    sudo mosquitto_passwd -c /etc/mosquitto/passwd "$mqtt_user" "$MQTT_PASSWORD"
    
    sudo mkdir -p /etc/mosquitto/conf.d
    sudo tee /etc/mosquitto/conf.d/default.conf > /dev/null << EOL
listener 1883 localhost
allow_anonymous false
password_file /etc/mosquitto/passwd

# Logging
log_dest file /var/log/mosquitto/mosquitto.log
log_dest stdout
connection_messages true
log_timestamp true
EOL

    # Crea directory log se non esiste
    sudo mkdir -p /var/log/mosquitto
    sudo chmod 777 /var/log/mosquitto
    
    # Assicura che il servizio Mosquitto sia configurato correttamente
    sudo service mosquitto restart
}

# Configurazione Supervisor per processi MQTT
setup_supervisor() {
    log "Configurazione Supervisor per WSL..."
    
    sudo mkdir -p /etc/supervisor/conf.d
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

# Configurazione del firewall in WSL non è necessaria normalmente
setup_firewall() {
    log "Configurazione firewall non necessaria in WSL (utilizza il firewall di Windows)..."
    
    log "Per la sicurezza, usa il Firewall di Windows Defender per proteggere le porte 80 e 443"
    log "Se vuoi esporre l'applicazione online, configura le regole appropriate nel Firewall di Windows"
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

# Crea uno script per far ripartire l'applicazione e i servizi rapidamente
create_management_scripts() {
    log "Creazione script di gestione..."
    
    # Script per riavviare l'applicazione
    cat > "$APP_PATH/restart.sh" << EOL
#!/bin/bash
echo "Riavvio CerCollettiva..."
# Riavvia Gunicorn
sudo supervisorctl restart gunicorn
# Riavvia il client MQTT
sudo supervisorctl restart cercollettiva_mqtt
echo "CerCollettiva riavviato!"
EOL
    
    # Script per aggiornare l'applicazione
    cat > "$APP_PATH/update.sh" << EOL
#!/bin/bash
echo "Aggiornamento CerCollettiva..."
cd $PROJECT_PATH
# Attiva ambiente virtuale
source $VENV_PATH/bin/activate
# Pull nuovi cambiamenti (assumendo git)
git pull
# Installa nuove dipendenze
pip install -r requirements.txt
# Applica migrazioni
python manage.py migrate
# Raccolta file statici
python manage.py collectstatic --noinput
# Riavvia l'applicazione
$APP_PATH/restart.sh
echo "CerCollettiva aggiornato!"
EOL
    
    # Script per visualizzare i log
    cat > "$APP_PATH/logs.sh" << EOL
#!/bin/bash
echo "Mostra ultimi log di CerCollettiva..."
echo "=== LOG DJANGO ==="
tail -n 50 $LOGS_PATH/django.log
echo "=== LOG GUNICORN ==="
tail -n 50 $LOGS_PATH/gunicorn.log
echo "=== LOG MQTT ==="
tail -n 50 $LOGS_PATH/mqtt.log
EOL
    
    # Rendi eseguibili gli script
    chmod +x "$APP_PATH/restart.sh"
    chmod +x "$APP_PATH/update.sh"
    chmod +x "$APP_PATH/logs.sh"
    
    log "Script di gestione creati in ${GREEN}$APP_PATH${NC}"
}

# Configurazione specifica per sviluppo in WSL
setup_wsl_development() {
    log "Configurazione ambiente di sviluppo in WSL..."
    
    # Crea un file env per lo sviluppo con DEBUG=True
    local settings_dir="$PROJECT_PATH/cercollettiva/settings"
    local dev_settings="$settings_dir/dev.py"
    
    cat > "$dev_settings" << EOL
from .local import *

# Impostazioni per sviluppo
DEBUG = True
ALLOWED_HOSTS = ['*']

# Disattiva alcune restrizioni di sicurezza per lo sviluppo
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

# Attiva toolbar di debug se installata
try:
    import debug_toolbar
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
    INTERNAL_IPS = ['127.0.0.1']
except ImportError:
    pass

# Configurazione logging più dettagliata
LOGGING['loggers']['django']['level'] = 'DEBUG'
EOL
    
    # Script per avviare in modalità sviluppo
    cat > "$APP_PATH/rundev.sh" << EOL
#!/bin/bash
cd $PROJECT_PATH
source $VENV_PATH/bin/activate
export DJANGO_SETTINGS_MODULE=cercollettiva.settings.dev
python manage.py runserver 0.0.0.0:8000
EOL
    
    chmod +x "$APP_PATH/rundev.sh"
    
    log "Ambiente di sviluppo configurato. Utilizza ${GREEN}$APP_PATH/rundev.sh${NC} per avviare il server di sviluppo"
}

# Funzione principale
main() {
    echo -e "${GREEN}=== Installazione CerCollettiva per WSL ===${NC}"
    
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
    create_management_scripts
    
    # Configurazione specifica per WSL development
    if [ "$WSL_MODE" = true ]; then
        setup_wsl_development
    fi
    
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
        echo -e "Accedi all'applicazione: http://$(hostname -I | awk '{print $1}')"
        echo -e "Pannello admin: http://$(hostname -I | awk '{print $1}')/admin"
    fi
    
    local windows_ip=$(ip route | grep default | awk '{print $3}')
    echo -e "\nPer accedere dal browser Windows, puoi usare: http://$PUBLIC_IP"
    echo -e "Oppure aggiungi 'cercollettiva.local' al tuo file hosts di Windows puntando a $PUBLIC_IP"
    
    echo -e "\n${BLUE}=== Informazioni per WSL ===${NC}"
    echo -e "1. Per avviare tutti i servizi: ${GREEN}~/start_services.sh${NC}"
    echo -e "2. Per modalità sviluppo: ${GREEN}$APP_PATH/rundev.sh${NC}"
    echo -e "3. Per riavviare l'app: ${GREEN}$APP_PATH/restart.sh${NC}"
    echo -e "4. Per visualizzare i log: ${GREEN}$APP_PATH/logs.sh${NC}"
    
    echo -e "\n${BLUE}=== Considerazioni per WSL ===${NC}"
    echo -e "1. I servizi non si avviano automaticamente al riavvio di WSL"
    echo -e "2. Utilizzare lo script start_services.sh all'avvio di WSL"
    echo -e "3. Per accesso da Windows, aggiungi una riga al file hosts di Windows:"
    echo -e "   ${GREEN}$PUBLIC_IP    cercollettiva.local${NC}"
    echo -e "4. Il file hosts si trova in: C:\\Windows\\System32\\drivers\\etc\\hosts"
    
    if [ "$USE_SSL" = false ]; then
        echo -e "\n${RED}AVVISO: L'applicazione non è configurata con SSL/HTTPS.${NC}"
        echo -e "${RED}In un ambiente di sviluppo WSL questo non è un problema.${NC}"
    fi
}

# Avvio
main
