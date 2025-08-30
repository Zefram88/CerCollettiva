#!/bin/bash

###########################################
#  CerCollettiva - Dev Setup Script      #
#  Version: 1.0                          #
#  For local development only            #
###########################################

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

# Verifica prerequisiti
check_prerequisites() {
    log "Verifica prerequisiti..."
    
    if [ ! -f "./manage.py" ]; then
        error "File manage.py non trovato. Esegui lo script dalla root del progetto"
    fi
    
    if ! command -v python3 &> /dev/null; then
        error "Python3 non è installato"
    fi
    
    if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
        error "pip non è installato"
    fi
}

# Setup ambiente virtuale
setup_venv() {
    log "Configurazione ambiente virtuale..."
    
    if [ -d "venv" ]; then
        read -p "L'ambiente virtuale esiste già. Vuoi ricrearlo? (s/n): " recreate
        if [[ "$recreate" =~ ^[Ss]$ ]]; then
            rm -rf venv
            python3 -m venv venv
        fi
    else
        python3 -m venv venv
    fi
    
    source venv/bin/activate
    
    pip install --upgrade pip wheel setuptools
}

# Installa dipendenze
install_dependencies() {
    log "Installazione dipendenze Python..."
    
    source venv/bin/activate
    
    # Installa Django e dipendenze core
    pip install Django==5.0 psycopg2-binary python-dotenv
    
    # Installa altre dipendenze principali
    pip install \
        djangorestframework \
        channels \
        django-crispy-forms \
        crispy-bootstrap5 \
        django-widget-tweaks \
        django-filter \
        django-extensions \
        paho-mqtt
    
    # Installa dipendenze addizionali
    pip install \
        channels-redis \
        daphne \
        django-cors-headers \
        django-encrypted-model-fields \
        geopy \
        whitenoise \
        openpyxl \
        pandas \
        cryptography \
        requests
    
    # Se esiste requirements.txt in app/, installalo
    if [ -f "app/requirements.txt" ]; then
        pip install -r app/requirements.txt
    fi

    # Se esiste requirements.txt nella root, installalo
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    fi
}

# Setup database SQLite per sviluppo
setup_database() {
    log "Configurazione database SQLite..."
    
    source venv/bin/activate
    
    # Rimuovi vecchio database se esiste
    if [ -f "db.sqlite3" ]; then
        read -p "Il database esiste già. Vuoi ricrearlo? (s/n): " recreate_db
        if [[ "$recreate_db" =~ ^[Ss]$ ]]; then
            rm -f db.sqlite3
        else
            return
        fi
    fi
    
    # Crea migrazioni
    python manage.py makemigrations users
    python manage.py makemigrations core
    python manage.py makemigrations energy
    python manage.py makemigrations documents
    
    # Applica migrazioni
    python manage.py migrate
    
    # Crea superuser
    echo -e "\n${GREEN}Creazione account amministratore${NC}"
    python manage.py createsuperuser
}

# Crea file .env se non esiste
setup_env() {
    log "Configurazione file .env..."
    
    if [ -f ".env" ]; then
        log "File .env già esistente, mantenuto"
        return
    fi
    
    cat > .env << 'EOL'
# Configurazione Django
DJANGO_SETTINGS_MODULE=cercollettiva.settings.local
DEBUG=True
SECRET_KEY=django-insecure-development-key-change-in-production

# Database SQLite (sviluppo)
# Per PostgreSQL, decommenta e configura:
# DB_NAME=cercollettiva_dev
# DB_USER=cercollettiva_user
# DB_PASSWORD=your_password
# DB_HOST=localhost
# DB_PORT=5432

# MQTT (opzionale per sviluppo)
MQTT_HOST=localhost
MQTT_PORT=1883
MQTT_USER=dev_user
MQTT_PASS=dev_password

# Redis (opzionale per sviluppo)
REDIS_URL=redis://localhost:6379/1

# Host consentiti
ALLOWED_HOSTS=localhost,127.0.0.1

# Email (console per sviluppo)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EOL
    
    log "File .env creato con configurazione di sviluppo"
}

# Crea directory necessarie
create_directories() {
    log "Creazione directory necessarie..."
    
    mkdir -p media
    mkdir -p staticfiles
    mkdir -p logs
    mkdir -p keydir
    
    chmod 700 keydir
}

# Raccolta file statici
collect_static() {
    log "Raccolta file statici..."
    
    source venv/bin/activate
    python manage.py collectstatic --noinput
}

# Test installazione
test_installation() {
    log "Test dell'installazione..."
    
    source venv/bin/activate
    
    # Verifica che Django sia installato correttamente
    python -c "import django; print(f'Django {django.get_version()} installato correttamente')"
    
    # Verifica che le app siano configurate
    python manage.py check
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Installazione completata con successo!${NC}"
    else
        error "Ci sono problemi con l'installazione"
    fi
}

# Crea script di utilità locali
create_local_scripts() {
    log "Creazione script di utilità..."
    
    # Script per avviare il server
    cat > runserver.sh << 'EOL'
#!/bin/bash
source venv/bin/activate
python manage.py runserver
EOL
    
    # Script per shell Django
    cat > shell.sh << 'EOL'
#!/bin/bash
source venv/bin/activate
python manage.py shell_plus --ipython
EOL
    
    # Script per migrazioni
    cat > migrate.sh << 'EOL'
#!/bin/bash
source venv/bin/activate
python manage.py makemigrations
python manage.py migrate
EOL
    
    chmod +x *.sh
    
    log "Script di utilità creati: runserver.sh, shell.sh, migrate.sh"
}

# Main
main() {
    echo -e "${GREEN}=== Setup Ambiente di Sviluppo CerCollettiva ===${NC}"
    
    check_prerequisites
    setup_venv
    install_dependencies
    setup_env
    create_directories
    setup_database
    collect_static
    create_local_scripts
    test_installation
    
    echo -e "\n${GREEN}=== Setup completato! ===${NC}"
    echo -e "Per avviare il server di sviluppo:"
    echo -e "  ${BLUE}./runserver.sh${NC} oppure ${BLUE}source venv/bin/activate && python manage.py runserver${NC}"
    echo -e "\nAccedi a:"
    echo -e "  Applicazione: ${GREEN}http://127.0.0.1:8000/${NC}"
    echo -e "  Admin: ${GREEN}http://127.0.0.1:8000/ceradmin/${NC}"
    echo -e "\nScript di utilità disponibili:"
    echo -e "  ${BLUE}./runserver.sh${NC} - Avvia il server di sviluppo"
    echo -e "  ${BLUE}./shell.sh${NC} - Apri shell Django interattiva"
    echo -e "  ${BLUE}./migrate.sh${NC} - Esegui migrazioni"
}

main