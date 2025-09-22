#!/bin/bash

# Script di setup automatico per CerCollettiva
# Sistema modernizzato per il nuovo setup Docker autonomo
# Supporta: sviluppo locale, Docker (dev/staging/prod)

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
echo "║                    v2.0 - Autonomo                          ║"
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
echo "2) Sviluppo con Docker (PostgreSQL, Redis, MQTT, auto-rilevamento)"
echo "3) Staging con Docker (HTTPS self-signed, monitoring)"
echo "4) Produzione con Docker (HTTPS Let's Encrypt, monitoring)"
echo ""
read -p "Inserisci la tua scelta (1-4): " SETUP_MODE

case $SETUP_MODE in
    1)
        log "Setup modalità sviluppo locale..."
        SETUP_TYPE="local"
        ;;
    2)
        if [ "$DOCKER_AVAILABLE" = true ] && [ "$DOCKER_COMPOSE_AVAILABLE" = true ]; then
            log "Setup modalità sviluppo con Docker..."
            SETUP_TYPE="docker_dev"
        else
            error "Docker e Docker Compose richiesti per questa modalità"
            exit 1
        fi
        ;;
    3)
        if [ "$DOCKER_AVAILABLE" = true ] && [ "$DOCKER_COMPOSE_AVAILABLE" = true ]; then
            log "Setup modalità staging con Docker..."
            SETUP_TYPE="docker_staging"
        else
            error "Docker e Docker Compose richiesti per questa modalità"
            exit 1
        fi
        ;;
    4)
        if [ "$DOCKER_AVAILABLE" = true ] && [ "$DOCKER_COMPOSE_AVAILABLE" = true ]; then
            log "Setup modalità produzione con Docker..."
            SETUP_TYPE="docker_prod"
        else
            error "Docker e Docker Compose richiesti per questa modalità"
            exit 1
        fi
        ;;
    *)
        error "Scelta non valida"
        exit 1
        ;;
esac

# Setup per modalità Docker
if [[ $SETUP_TYPE == docker_* ]]; then
    log "Setup modalità Docker..."
    
    # Verifica che docker-compose.yml esista
    if [ ! -f "docker-compose.yml" ]; then
        error "File docker-compose.yml non trovato"
        exit 1
    fi
    
    # Avvio servizi Docker
    case $SETUP_TYPE in
        "docker_dev")
            log "Avvio servizi Docker per sviluppo..."
            docker-compose --profile dev up -d
            success "Servizi Docker avviati (modalità sviluppo)"
            ;;
        "docker_staging")
            log "Avvio servizi Docker per staging..."
            docker-compose --profile staging up -d
            success "Servizi Docker avviati (modalità staging)"
            ;;
        "docker_prod")
            # Verifica variabili d'ambiente per produzione
            if [ -z "$DOMAIN" ] || [ -z "$LETSENCRYPT_EMAIL" ]; then
                echo ""
                warning "Per la modalità produzione sono richieste le seguenti variabili:"
                read -p "Dominio (es. example.com): " DOMAIN
                read -p "Email per Let's Encrypt: " LETSENCRYPT_EMAIL
                export DOMAIN
                export LETSENCRYPT_EMAIL
            fi
            
            log "Avvio servizi Docker per produzione..."
            docker-compose --profile prod up -d
            success "Servizi Docker avviati (modalità produzione)"
            ;;
    esac
    
    # Attesa servizi
    log "Attesa che i servizi siano pronti..."
    sleep 15
    
    # Verifica stato servizi
    log "Verifica stato servizi Docker..."
    docker-compose ps
    
    echo ""
    success "Setup Docker completato!"
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                    Setup Docker Completato!                  ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    case $SETUP_TYPE in
        "docker_dev")
            echo -e "${BLUE}Accesso:${NC}"
            echo "  Applicazione: http://127.0.0.1/"
            echo "  Setup: http://127.0.0.1/setup"
            echo "  Admin: http://127.0.0.1/ceradmin/"
            echo ""
            echo -e "${BLUE}Comandi utili:${NC}"
            echo "  Logs: docker-compose --profile dev logs -f"
            echo "  Stop: docker-compose --profile dev down"
            echo "  Restart: docker-compose --profile dev restart"
            ;;
        "docker_staging")
            echo -e "${BLUE}Accesso:${NC}"
            echo "  Applicazione: https://localhost (accetta certificato self-signed)"
            echo "  Setup: https://localhost/setup"
            echo "  Admin: https://localhost/ceradmin/"
            echo "  Grafana: http://localhost:3000/ (admin/admin)"
            echo "  Prometheus: http://localhost:9090/"
            echo ""
            echo -e "${BLUE}Comandi utili:${NC}"
            echo "  Logs: docker-compose --profile staging logs -f"
            echo "  Stop: docker-compose --profile staging down"
            echo "  Restart: docker-compose --profile staging restart"
            ;;
        "docker_prod")
            echo -e "${BLUE}Accesso:${NC}"
            echo "  Applicazione: https://$DOMAIN"
            echo "  Setup: https://$DOMAIN/setup"
            echo "  Admin: https://$DOMAIN/ceradmin/"
            echo "  Grafana: https://$DOMAIN:3000/ (admin/admin)"
            echo "  Prometheus: https://$DOMAIN:9090/"
            echo ""
            echo -e "${BLUE}Comandi utili:${NC}"
            echo "  Logs: docker-compose --profile prod logs -f"
            echo "  Stop: docker-compose --profile prod down"
            echo "  Restart: docker-compose --profile prod restart"
            echo "  Rinnovo certificati: docker-compose --profile prod exec nginx certbot renew"
            ;;
    esac
    
    echo ""
    echo -e "${BLUE}Documentazione:${NC}"
    echo "  - Modalità di deployment: docs/DEPLOYMENT_MODES.md"
    echo "  - Troubleshooting: docs/DEPLOYMENT_MODES.md#troubleshooting"
    echo ""
    echo -e "${GREEN}Buon lavoro con CerCollettiva! 🚀${NC}"
    exit 0
fi

# Setup per modalità locale (senza Docker)
log "Setup modalità locale..."

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

# Configurazione ambiente locale
log "Configurazione variabili d'ambiente per sviluppo locale..."

# Crea .env per sviluppo locale
cat > .env << EOF
# Configurazione sviluppo locale
DEBUG=True
DJANGO_SETTINGS_MODULE=cercollettiva.settings.local
SECRET_KEY=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
FIELD_ENCRYPTION_KEY=$(python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')

# Database SQLite per sviluppo locale
DB_NAME=db.sqlite3
DB_USER=
DB_PASSWORD=
DB_HOST=
DB_PORT=

# Redis (opzionale per sviluppo locale)
REDIS_URL=redis://localhost:6379/1

# MQTT (opzionale per sviluppo locale)
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
MQTT_BROKER_USERNAME=
MQTT_BROKER_PASSWORD=

# Configurazione locale
ALLOWED_HOSTS=localhost,127.0.0.1
DEV_MODE=true
ENABLE_DEBUG_TOOLBAR=True
DJANGO_LOG_LEVEL=DEBUG
EOF

success "File .env creato per sviluppo locale"

# Setup database SQLite
log "Setup database SQLite..."
python manage.py migrate
success "Database SQLite configurato"

# Creazione superuser (opzionale)
echo ""
read -p "Vuoi creare un superuser? (y/n): " CREATE_SUPERUSER
if [[ $CREATE_SUPERUSER =~ ^[Yy]$ ]]; then
    log "Creazione superuser..."
    python manage.py createsuperuser
    success "Superuser creato"
else
    warning "Superuser non creato (puoi crearlo successivamente con: python manage.py createsuperuser)"
fi

# Raccolta file statici
log "Raccolta file statici..."
python manage.py collectstatic --noinput
success "File statici raccolti"

# Creazione directory necessarie
log "Creazione directory necessarie..."
mkdir -p logs media staticfiles
success "Directory create"

# Test configurazione
log "Test configurazione..."
python manage.py check
success "Configurazione Django verificata"

# Avvio servizi
echo ""
log "Setup locale completato con successo!"
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                    Setup Locale Completato!                  ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${BLUE}Per avviare il server di sviluppo:${NC}"
echo "  source venv/bin/activate"
echo "  python manage.py runserver"
echo ""
echo -e "${BLUE}Accesso:${NC}"
echo "  Applicazione: http://127.0.0.1:8000/"
echo "  Setup: http://127.0.0.1:8000/setup"
echo "  Admin: http://127.0.0.1:8000/ceradmin/"
echo ""
echo -e "${BLUE}Comandi utili:${NC}"
echo "  Test: python manage.py test"
echo "  Shell: python manage.py shell"
echo "  Migrazioni: python manage.py makemigrations && python manage.py migrate"
echo "  Superuser: python manage.py createsuperuser"
echo ""

# Avvio automatico (opzionale)
read -p "Vuoi avviare il server di sviluppo ora? (y/n): " START_SERVER
if [[ $START_SERVER =~ ^[Yy]$ ]]; then
    log "Avvio server di sviluppo..."
    echo ""
    echo -e "${BLUE}Server in avvio su http://127.0.0.1:8000/${NC}"
    echo -e "${YELLOW}Premi Ctrl+C per fermare il server${NC}"
    echo ""
    python manage.py runserver
fi

echo ""
echo -e "${BLUE}Documentazione:${NC}"
echo "  - Modalità di deployment: docs/DEPLOYMENT_MODES.md"
echo "  - Sviluppo locale: docs/guides/development.md"
echo "  - Troubleshooting: docs/DEPLOYMENT_MODES.md#troubleshooting"
echo ""
echo -e "${GREEN}Buon lavoro con CerCollettiva! 🚀${NC}"