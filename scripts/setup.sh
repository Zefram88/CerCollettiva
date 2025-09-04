#!/bin/bash

# Script di setup automatico per CerCollettiva
# Questo script configura l'ambiente di sviluppo completo

set -e  # Exit on any error

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funzione per logging
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✓${NC} $1"
}

warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

error() {
    echo -e "${RED}✗${NC} $1"
}

# Banner
echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    CerCollettiva Setup                       ║"
echo "║              Sistema di gestione CER/CEC                     ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Verifica prerequisiti
log "Verifica prerequisiti..."

# Python 3.11+
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if [[ $(echo "$PYTHON_VERSION >= 3.11" | bc -l) -eq 1 ]]; then
        success "Python $PYTHON_VERSION trovato"
    else
        error "Python 3.11+ richiesto, trovato $PYTHON_VERSION"
        exit 1
    fi
else
    error "Python 3 non trovato"
    exit 1
fi

# pip
if command -v pip3 &> /dev/null; then
    success "pip3 trovato"
else
    error "pip3 non trovato"
    exit 1
fi

# Git
if command -v git &> /dev/null; then
    success "Git trovato"
else
    error "Git non trovato"
    exit 1
fi

# Docker (opzionale)
if command -v docker &> /dev/null; then
    success "Docker trovato"
    DOCKER_AVAILABLE=true
else
    warning "Docker non trovato (opzionale per sviluppo)"
    DOCKER_AVAILABLE=false
fi

# Docker Compose (opzionale)
if command -v docker-compose &> /dev/null; then
    success "Docker Compose trovato"
    DOCKER_COMPOSE_AVAILABLE=true
else
    warning "Docker Compose non trovato (opzionale per sviluppo)"
    DOCKER_COMPOSE_AVAILABLE=false
fi

echo ""

# Scelta modalità di setup
log "Seleziona modalità di setup:"
echo "1) Sviluppo locale (SQLite, debug mode)"
echo "2) Sviluppo con Docker (PostgreSQL, Redis, MQTT)"
echo "3) Produzione (PostgreSQL, Redis, MQTT, Nginx)"
echo ""
read -p "Inserisci la tua scelta (1-3): " SETUP_MODE

case $SETUP_MODE in
    1)
        log "Setup modalità sviluppo locale..."
        SETUP_TYPE="local"
        ;;
    2)
        if [ "$DOCKER_AVAILABLE" = true ] && [ "$DOCKER_COMPOSE_AVAILABLE" = true ]; then
            log "Setup modalità sviluppo con Docker..."
            SETUP_TYPE="docker"
        else
            error "Docker e Docker Compose richiesti per questa modalità"
            exit 1
        fi
        ;;
    3)
        log "Setup modalità produzione..."
        SETUP_TYPE="production"
        ;;
    *)
        error "Scelta non valida"
        exit 1
        ;;
esac

# Crea ambiente virtuale
log "Creazione ambiente virtuale Python..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    success "Ambiente virtuale creato"
else
    warning "Ambiente virtuale già esistente"
fi

# Attiva ambiente virtuale
log "Attivazione ambiente virtuale..."
source venv/bin/activate
success "Ambiente virtuale attivato"

# Aggiorna pip
log "Aggiornamento pip..."
pip install --upgrade pip
success "pip aggiornato"

# Installa dipendenze
log "Installazione dipendenze Python..."
pip install -r requirements.txt
success "Dipendenze installate"

# Configurazione ambiente
log "Configurazione variabili d'ambiente..."

if [ ! -f ".env" ]; then
    if [ -f "env.example" ]; then
        cp env.example .env
        success "File .env creato da template"
    else
        warning "File env.example non trovato, creazione .env manuale"
        cat > .env << EOF
DEBUG=True
SECRET_KEY=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
FIELD_ENCRYPTION_KEY=$(python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')
DB_NAME=cercollettiva
DB_USER=cercollettiva_user
DB_PASSWORD=cercollettiva_pass
DB_HOST=localhost
DB_PORT=5432
REDIS_URL=redis://localhost:6379/1
MQTT_HOST=localhost
MQTT_PORT=1883
MQTT_USER=mqtt_user
MQTT_PASS=mqtt_pass
EOF
        success "File .env creato con valori di default"
    fi
else
    warning "File .env già esistente"
fi

# Configurazione specifica per modalità
case $SETUP_TYPE in
    "local")
        log "Configurazione per sviluppo locale..."
        # Modifica .env per sviluppo locale
        sed -i 's/DEBUG=False/DEBUG=True/' .env
        sed -i 's/DB_NAME=cercollettiva/DB_NAME=db.sqlite3/' .env
        success "Configurazione locale completata"
        ;;
    "docker")
        log "Configurazione per Docker..."
        # Modifica .env per Docker
        sed -i 's/DB_HOST=localhost/DB_HOST=db/' .env
        sed -i 's/REDIS_URL=redis:\/\/localhost:6379\/1/REDIS_URL=redis:\/\/:redis_pass@redis:6379\/1/' .env
        sed -i 's/MQTT_HOST=localhost/MQTT_HOST=mqtt/' .env
        success "Configurazione Docker completata"
        ;;
    "production")
        log "Configurazione per produzione..."
        # Modifica .env per produzione
        sed -i 's/DEBUG=True/DEBUG=False/' .env
        warning "Ricorda di configurare SECRET_KEY e password per produzione!"
        success "Configurazione produzione completata"
        ;;
esac

# Setup database
log "Setup database..."

case $SETUP_TYPE in
    "local")
        log "Esecuzione migrazioni SQLite..."
        python manage.py migrate
        success "Database SQLite configurato"
        ;;
    "docker")
        log "Avvio servizi Docker..."
        docker-compose up -d db redis mqtt
        log "Attesa servizi..."
        sleep 10
        log "Esecuzione migrazioni PostgreSQL..."
        python manage.py migrate
        success "Database PostgreSQL configurato"
        ;;
    "production")
        log "Esecuzione migrazioni PostgreSQL..."
        python manage.py migrate
        success "Database PostgreSQL configurato"
        ;;
esac

# Creazione superuser
log "Creazione superuser..."
echo ""
echo "Creazione account amministratore:"
python manage.py createsuperuser
success "Superuser creato"

# Raccolta file statici
log "Raccolta file statici..."
python manage.py collectstatic --noinput
success "File statici raccolti"

# Creazione directory necessarie
log "Creazione directory necessarie..."
mkdir -p logs media staticfiles
success "Directory create"

# Setup MQTT (se non Docker)
if [ "$SETUP_TYPE" != "docker" ]; then
    log "Configurazione MQTT..."
    warning "Ricorda di installare e configurare Mosquitto MQTT broker"
    warning "Configurazione: config/mosquitto/mosquitto.conf"
fi

# Setup monitoring
log "Configurazione monitoring..."
if [ "$SETUP_TYPE" = "docker" ]; then
    log "Avvio servizi monitoring..."
    docker-compose up -d prometheus grafana
    success "Monitoring configurato"
else
    warning "Monitoring disponibile solo con Docker"
fi

# Test configurazione
log "Test configurazione..."
python manage.py check
success "Configurazione Django verificata"

# Avvio servizi
echo ""
log "Setup completato con successo!"
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                    Setup Completato!                        ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

case $SETUP_TYPE in
    "local")
        echo -e "${BLUE}Per avviare il server di sviluppo:${NC}"
        echo "  source venv/bin/activate"
        echo "  python manage.py runserver"
        echo ""
        echo -e "${BLUE}Accesso:${NC}"
        echo "  Applicazione: http://127.0.0.1:8000/"
        echo "  Admin: http://127.0.0.1:8000/ceradmin/"
        ;;
    "docker")
        echo -e "${BLUE}Per avviare tutti i servizi:${NC}"
        echo "  docker-compose up -d"
        echo ""
        echo -e "${BLUE}Per avviare solo l'applicazione:${NC}"
        echo "  source venv/bin/activate"
        echo "  python manage.py runserver"
        echo ""
        echo -e "${BLUE}Accesso:${NC}"
        echo "  Applicazione: http://127.0.0.1:8000/"
        echo "  Admin: http://127.0.0.1:8000/ceradmin/"
        echo "  Grafana: http://127.0.0.1:3000/ (admin/admin)"
        echo "  Prometheus: http://127.0.0.1:9090/"
        ;;
    "production")
        echo -e "${BLUE}Per avviare in produzione:${NC}"
        echo "  gunicorn --bind 0.0.0.0:8000 cercollettiva.wsgi:application"
        echo ""
        echo -e "${BLUE}O con Docker:${NC}"
        echo "  docker-compose -f docker-compose.prod.yml up -d"
        echo ""
        echo -e "${YELLOW}Ricorda di:${NC}"
        echo "  - Configurare SSL/HTTPS"
        echo "  - Configurare backup automatici"
        echo "  - Configurare monitoring"
        echo "  - Aggiornare SECRET_KEY e password"
        ;;
esac

echo ""
echo -e "${BLUE}Documentazione:${NC}"
echo "  - Architettura: docs/ARCHITECTURE.md"
echo "  - API: docs/API_DOCUMENTATION.md"
echo "  - Troubleshooting: TROUBLESHOOTING.md"
echo ""
echo -e "${GREEN}Buon lavoro con CerCollettiva! 🚀${NC}"
