#!/bin/bash

###########################################
#  CerCollettiva - Installation Script   #
#  Version: 2.0                          #
#  Author: Andrea Bernardi               #
#  Date: Agosto 2025                     #
#  Updated for new project structure     #
###########################################

# Colori per output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Variabile per l'utente di sistema
SYSTEM_USER=""

# Configurazione base 
APP_NAME="CerCollettiva"
APP_ROOT=""  # Sarà impostato in setup_user
APP_PATH=""  # Sarà impostato in setup_user
VENV_PATH="" # Sarà impostato in setup_user
LOGS_PATH="" # Sarà impostato in setup_user

# Variabili aggiuntive per la configurazione di rete e sicurezza
PUBLIC_DOMAIN=""
PUBLIC_IP=""
USE_SSL=false

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
    
    local current_user=$(whoami)
    
    echo -e "Utente corrente: ${GREEN}$current_user${NC}"
    read -p "Vuoi utilizzare l'utente corrente per l'installazione? (s/n): " use_current_user
    
    if [[ "$use_current_user" =~ ^[Ss]$ ]]; then
        SYSTEM_USER="$current_user"
    else
        read -p "Inserisci il nome dell'utente da utilizzare: " SYSTEM_USER
        
        if ! id "$SYSTEM_USER" &>/dev/null; then
            error "L'utente $SYSTEM_USER non esiste. Crealo prima di continuare."
        fi
    fi
    
    # Aggiorna i percorsi di configurazione
    APP_ROOT="/home/$SYSTEM_USER"
    APP_PATH="$APP_ROOT/$APP_NAME"
    VENV_PATH="$APP_PATH/venv"
    LOGS_PATH="$APP_PATH/logs"
    
    log "L'installazione verrà eseguita per l'utente: ${GREEN}$SYSTEM_USER${NC}"
    log "Directory di installazione: $APP_PATH"
}

# Verifica prerequisiti
check_prerequisites() {
    log "Verifica prerequisiti..."
    
    if [ "$EUID" -eq 0 ]; then
        error "Non eseguire questo script come root"
    fi

    # Verifica presenza manage.py nella directory corrente
    if [ ! -f "./manage.py" ]; then
        error "File manage.py non trovato. Assicurati di essere nella directory root del progetto"
    fi

    # Verifica spazio disponibile
    local available_space=$(df -m "$HOME" | awk 'NR==2 {print $4}')
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
    
    read -p "Vuoi esporre l'applicazione su internet? (s/n): " expose_online
    if [[ "$expose_online" =~ ^[Ss]$ ]]; then
        read -p "Hai un dominio per questa applicazione? (s/n): " has_domain
        if [[ "$has_domain" =~ ^[Ss]$ ]]; then
            read -p "Inserisci il tuo dominio (es. cercollettiva.example.com): " PUBLIC_DOMAIN
        else
            read -p "Inserisci il tuo indirizzo IP pubblico: " PUBLIC_IP
        fi
        
        read -p "Vuoi configurare SSL/HTTPS per una connessione sicura? (s/n): " configure_ssl
        if [[ "$configure_ssl" =~ ^[Ss]$ ]]; then
            USE_SSL=true
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
        mosquitto-clients \
        redis-server \
        rsync

    if [ "$USE_SSL" = true ]; then
        sudo apt install -y certbot python3-certbot-nginx
    fi

    if [ $? -ne 0 ]; then
        error "Errore durante l'installazione delle dipendenze"
    fi
}

# Copia progetto nella nuova posizione
copy_project() {
    log "Copia del progetto in $APP_PATH..."
    
    mkdir -p "$APP_PATH"
    
    # Copia tutto il contenuto della directory corrente escludendo venv, db e cache
    rsync -av \
        --exclude='venv' \
        --exclude='*.sqlite3' \
        --exclude='__pycache__' \
        --exclude='.git' \
        --exclude='staticfiles' \
        --exclude='media' \
        --exclude='logs' \
        ./ "$APP_PATH/"
    
    if [ $? -ne 0 ]; then
        error "Errore durante la copia del progetto"
    fi
}

# Setup ambiente virtuale e dipendenze Python
setup_virtualenv() {
    log "Configurazione ambiente virtuale Python..."
    
    # Crea e attiva l'ambiente virtuale
    python3 -m venv "$VENV_PATH"
    source "$VENV_PATH/bin/activate"
    
    pip install --upgrade pip wheel setuptools
    
    # Installa le dipendenze dal file requirements.txt
    if [ -f "$APP_PATH/app/requirements.txt" ]; then
        pip install -r "$APP_PATH/app/requirements.txt"
    else
        # Installa le dipendenze principali direttamente
        pip install \
            Django==5.0 \
            channels==4.0.0 \
            channels-redis==4.1.0 \
            crispy-bootstrap5==2023.10 \
            daphne==4.0.0 \
            django-cors-headers==4.3.1 \
            django-crispy-forms==2.1 \
            django-encrypted-model-fields==0.6.5 \
            django-filter==23.4 \
            djangorestframework==3.14.0 \
            django-widget-tweaks==1.5.0 \
            django-extensions \
            geopy==2.4.1 \
            gunicorn==21.2.0 \
            paho-mqtt>=2.0.0 \
            python-dotenv==1.0.0 \
            psycopg2-binary==2.9.9 \
            requests==2.31.0 \
            whitenoise==6.6.0 \
            openpyxl \
            pandas \
            cryptography
    fi
    
    if [ $? -ne 0 ]; then
        error "Errore durante l'installazione delle dipendenze Python"
    fi
}

setup_database() {
    log "Configurazione PostgreSQL..."
    
    # Genera una password sicura per il database
    local db_password=$(openssl rand -base64 12)
    
    # Crea utente e database
    sudo -u postgres psql <<EOF
CREATE USER cercollettiva WITH PASSWORD '${db_password}';
CREATE DATABASE cercollettiva OWNER cercollettiva;
ALTER USER cercollettiva CREATEDB;
CREATE DATABASE test_cercollettiva OWNER cercollettiva;
EOF
    
    # Salva la configurazione nel file .env
    cat > "$APP_PATH/.env" << EOL
# Django Configuration
DJANGO_SETTINGS_MODULE=cercollettiva.settings.production
DEBUG=False
SECRET_KEY=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')

# Database PostgreSQL
DB_NAME=cercollettiva
DB_USER=cercollettiva
DB_PASSWORD=${db_password}
DB_HOST=localhost
DB_PORT=5432

# MQTT Configuration
MQTT_HOST=localhost
MQTT_PORT=1883
MQTT_USER=cercollettiva
MQTT_PASS=$(openssl rand -base64 12)

# Redis
REDIS_URL=redis://localhost:6379/1

# Allowed Hosts
ALLOWED_HOSTS=localhost,127.0.0.1${PUBLIC_DOMAIN:+,$PUBLIC_DOMAIN}${PUBLIC_IP:+,$PUBLIC_IP}

# Email
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EOL
    
    chmod 600 "$APP_PATH/.env"
}

setup_django() {
    log "Configurazione Django..."
    
    # Crea directory necessarie
    mkdir -p "$APP_PATH/media"
    mkdir -p "$APP_PATH/staticfiles"
    mkdir -p "$APP_PATH/keydir"
    mkdir -p "$LOGS_PATH"
    
    # Imposta i permessi corretti
    sudo chown -R $SYSTEM_USER:$SYSTEM_USER "$APP_PATH"
    chmod 700 "$APP_PATH/keydir"
    
    # Inizializza database
    source "$VENV_PATH/bin/activate"
    cd "$APP_PATH"
    
    # Crea migrazioni per tutte le app
    python manage.py makemigrations users
    python manage.py makemigrations core
    python manage.py makemigrations energy
    python manage.py makemigrations documents
    
    # Applica tutte le migrazioni
    python manage.py migrate
    
    # Raccolta file statici
    python manage.py collectstatic --noinput
    
    # Crea superuser
    echo -e "\nCreazione account amministratore"
    python manage.py createsuperuser
}

# Configurazione Nginx
setup_nginx() {
    log "Configurazione Nginx..."
    
    local server_name="_"
    
    if [ -n "$PUBLIC_DOMAIN" ]; then
        server_name="$PUBLIC_DOMAIN"
    elif [ -n "$PUBLIC_IP" ]; then
        server_name="$PUBLIC_IP"
    fi
    
    sudo tee /etc/nginx/sites-available/cercollettiva > /dev/null << EOL
server {
    listen 80;
    server_name ${server_name};
    
    access_log /var/log/nginx/cercollettiva_access.log;
    error_log /var/log/nginx/cercollettiva_error.log;
    
    client_max_body_size 10M;
    
    location /static/ {
        alias $APP_PATH/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, max-age=2592000";
    }

    location /media/ {
        alias $APP_PATH/media/;
        expires 7d;
        add_header Cache-Control "public, max-age=604800";
    }

    location / {
        proxy_set_header Host \$http_host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        
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
    if [ "$USE_SSL" = true ] && [ -n "$PUBLIC_DOMAIN" ]; then
        sudo certbot --nginx -d "$PUBLIC_DOMAIN" --non-interactive --agree-tos --email admin@"$PUBLIC_DOMAIN" --redirect
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
WorkingDirectory=$APP_PATH
Environment="PATH=$VENV_PATH/bin"
Environment="DJANGO_SETTINGS_MODULE=cercollettiva.settings.production"
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
    
    # Crea password file per mosquitto
    sudo touch /etc/mosquitto/passwd
    sudo mosquitto_passwd -b /etc/mosquitto/passwd "$MQTT_USER" "$MQTT_PASS"
    
    sudo tee /etc/mosquitto/conf.d/default.conf > /dev/null << EOL
listener 1883 localhost
allow_anonymous false
password_file /etc/mosquitto/passwd

log_dest file /var/log/mosquitto/mosquitto.log
connection_messages true
log_timestamp true
EOL

    sudo systemctl restart mosquitto
    sudo systemctl enable mosquitto
}

# Configurazione Redis
setup_redis() {
    log "Configurazione Redis..."
    
    sudo systemctl start redis-server
    sudo systemctl enable redis-server
}

# Configurazione del firewall
setup_firewall() {
    log "Configurazione del firewall..."
    
    if ! command -v ufw &> /dev/null; then
        sudo apt install -y ufw
    fi
    
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    sudo ufw allow ssh
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    sudo ufw deny 1883/tcp
    
    sudo ufw --force enable
}

# Verifica e aggiunge l'utente al gruppo www-data
setup_user_permissions() {
    log "Configurazione dei permessi dell'utente..."
    
    if ! groups "$SYSTEM_USER" | grep -q www-data; then
        sudo usermod -a -G www-data "$SYSTEM_USER"
        log "Utente $SYSTEM_USER aggiunto al gruppo www-data"
    fi
    
    sudo chown -R "$SYSTEM_USER":www-data "$APP_PATH"
    sudo chmod -R 750 "$APP_PATH"
    sudo chmod -R 770 "$APP_PATH/media"
    sudo chmod -R 770 "$LOGS_PATH"
}

# Crea script di utilità
create_utility_scripts() {
    log "Creazione script di utilità..."
    
    # Script per avviare il server di sviluppo
    cat > "$APP_PATH/rundev.sh" << 'EOL'
#!/bin/bash
source venv/bin/activate
python manage.py runserver 0.0.0.0:8000
EOL
    
    # Script per riavviare i servizi
    cat > "$APP_PATH/restart.sh" << 'EOL'
#!/bin/bash
sudo systemctl restart gunicorn
sudo systemctl restart nginx
sudo systemctl restart mosquitto
echo "Servizi riavviati con successo"
EOL
    
    # Script per vedere i log
    cat > "$APP_PATH/logs.sh" << 'EOL'
#!/bin/bash
echo "=== Gunicorn Logs ==="
sudo journalctl -u gunicorn -n 50 --no-pager
echo ""
echo "=== Nginx Error Logs ==="
sudo tail -n 50 /var/log/nginx/cercollettiva_error.log
EOL
    
    chmod +x "$APP_PATH"/*.sh
}

# Funzione principale
main() {
    echo -e "${GREEN}=== Installazione CerCollettiva v2.0 ===${NC}"
    
    setup_user
    check_prerequisites
    collect_network_info
    install_dependencies
    copy_project
    setup_virtualenv
    setup_database
    setup_django
    setup_user_permissions
    setup_nginx
    setup_gunicorn
    setup_mqtt
    setup_redis
    setup_firewall
    create_utility_scripts
    
    echo -e "\n${GREEN}=== Installazione completata! ===${NC}"
    
    # Mostra le informazioni di accesso
    if [ "$USE_SSL" = true ] && [ -n "$PUBLIC_DOMAIN" ]; then
        echo -e "Accedi all'applicazione: https://$PUBLIC_DOMAIN"
        echo -e "Pannello admin: https://$PUBLIC_DOMAIN/ceradmin/"
    elif [ -n "$PUBLIC_DOMAIN" ]; then
        echo -e "Accedi all'applicazione: http://$PUBLIC_DOMAIN"
        echo -e "Pannello admin: http://$PUBLIC_DOMAIN/ceradmin/"
    elif [ -n "$PUBLIC_IP" ]; then
        echo -e "Accedi all'applicazione: http://$PUBLIC_IP"
        echo -e "Pannello admin: http://$PUBLIC_IP/ceradmin/"
    else
        echo -e "Accedi all'applicazione: http://$(hostname -I | cut -d' ' -f1)"
        echo -e "Pannello admin: http://$(hostname -I | cut -d' ' -f1)/ceradmin/"
    fi
    
    echo -e "\n${BLUE}=== Informazioni di sicurezza ===${NC}"
    echo -e "File di configurazione: $APP_PATH/.env"
    echo -e "Log directory: $LOGS_PATH"
    echo -e "Script di utilità disponibili in: $APP_PATH/"
    echo -e "  - rundev.sh: Avvia server di sviluppo"
    echo -e "  - restart.sh: Riavvia tutti i servizi"
    echo -e "  - logs.sh: Visualizza i log"
    
    if [ "$USE_SSL" = false ]; then
        echo -e "\n${RED}AVVISO: L'applicazione non è configurata con SSL/HTTPS.${NC}"
        echo -e "${RED}Per maggiore sicurezza, si consiglia di configurare HTTPS.${NC}"
    fi
}

# Avvio
main