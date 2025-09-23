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

# Fix per Windows: aggiungi PATH di Windows al PATH di bash (Git Bash su Windows)
if [ -d "/c/Windows/System32" ]; then
    export PATH="$PATH:/c/Windows/System32"
    export PATH="$PATH:/c/Users/$USER/AppData/Local/Microsoft/WindowsApps"
elif [ -d "/mnt/c/Windows/System32" ]; then
    export PATH="$PATH:/mnt/c/Windows/System32"
    export PATH="$PATH:/mnt/c/Users/$USER/AppData/Local/Microsoft/WindowsApps"
fi

# Python 3.11+ - rilevamento cross-platform robusto
PYTHON_CMD=""

# Funzione per testare se un comando Python è valido
test_python() {
    local cmd="$1"
    local version
    version=$($cmd -c 'import sys; print(".".join(map(str, sys.version_info[:2])))' 2>/dev/null)
    if [ $? -eq 0 ] && [ -n "$version" ]; then
        local major=$(echo $version | cut -d. -f1)
        local minor=$(echo $version | cut -d. -f2)
        if [ "$major" -gt 3 ] || ([ "$major" -eq 3 ] && [ "$minor" -ge 11 ]); then
            PYTHON_CMD="$cmd"
            PYTHON_VERSION="$version"
            return 0
        fi
    fi
    return 1
}

# Prova diversi comandi Python in ordine di preferenza
for cmd in python3 python py; do
    if type "$cmd" >/dev/null 2>&1; then
        if test_python "$cmd"; then
            break
        fi
    fi
done

# Se non trova Python, prova con percorsi comuni su Windows
if [ -z "$PYTHON_CMD" ]; then
    for python_path in "/c/Users/$USER/AppData/Local/Microsoft/WindowsApps/python3.exe" "/c/Users/$USER/AppData/Local/Programs/Python/Python*/python.exe"; do
        if [ -f "$python_path" ]; then
            if test_python "$python_path"; then
                break
            fi
        fi
    done
fi

if [ -n "$PYTHON_CMD" ]; then
    success "Python $PYTHON_VERSION trovato ($PYTHON_CMD)"
else
    error "Python 3.11+ non trovato. Installa Python 3.11 o superiore."
    exit 1
fi

# pip - rilevamento cross-platform usando 'type' (bash builtin)
PIP_CMD=""

# Funzione per testare se un comando pip è valido
test_pip() {
    local cmd="$1"
    if $cmd --version &> /dev/null; then
        PIP_CMD="$cmd"
        return 0
    fi
    return 1
}

# Prova diversi comandi pip in ordine di preferenza usando 'type' (bash builtin)
for cmd in pip3 pip; do
    if type "$cmd" >/dev/null 2>&1; then
        if test_pip "$cmd"; then
            break
        fi
    fi
done

if [ -n "$PIP_CMD" ]; then
    success "pip trovato ($PIP_CMD)"
else
    error "pip non trovato. Installa pip per Python."
    exit 1
fi

# Git - usando 'type' (bash builtin)
if type git >/dev/null 2>&1; then
    success "Git trovato"
else
    error "Git non trovato"
    exit 1
fi

# Docker (opzionale) - usando 'type' (bash builtin)
if type docker >/dev/null 2>&1; then
    success "Docker trovato"
    DOCKER_AVAILABLE=true
else
    warning "Docker non trovato (opzionale per sviluppo)"
    DOCKER_AVAILABLE=false
fi

# Docker Compose (opzionale) - usando 'type' (bash builtin)
if type docker-compose >/dev/null 2>&1; then
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

# Crea ambiente virtuale con gestione filesystem WSL
log "Creazione ambiente virtuale Python..."

# Verifica se siamo su filesystem Windows (DrvFs) - problema di permessi
if [[ "$PWD" == /mnt/* ]]; then
    warning "Rilevato filesystem Windows (DrvFs) - possibile problema di permessi"
    log "Creazione ambiente virtuale nel filesystem Linux di WSL..."
    
    # Crea ambiente virtuale nel filesystem Linux
    VENV_PATH="$HOME/.local/share/venv/$(basename "$PWD")"
    mkdir -p "$(dirname "$VENV_PATH")"
    
    if [ ! -d "$VENV_PATH" ]; then
        log "Creazione ambiente virtuale in $VENV_PATH..."
        if timeout 60 $PYTHON_CMD -m venv "$VENV_PATH"; then
            success "Ambiente virtuale creato in filesystem Linux"
        else
            error "Timeout o errore nella creazione dell'ambiente virtuale"
            exit 1
        fi
    else
        warning "Ambiente virtuale già esistente in filesystem Linux"
    fi
    
    # Crea symlink per compatibilità (rimuovi symlink esistente se presente)
    rm -f venv
    ln -sf "$VENV_PATH" venv
else
    # Filesystem Linux normale
    if [ ! -d "venv" ]; then
        log "Creazione ambiente virtuale in corso..."
        if timeout 60 $PYTHON_CMD -m venv venv; then
            success "Ambiente virtuale creato"
        else
            error "Timeout o errore nella creazione dell'ambiente virtuale"
            log "Tentativo con approccio alternativo..."
            if $PYTHON_CMD -m venv --clear venv; then
                success "Ambiente virtuale creato (approccio alternativo)"
            else
                error "Impossibile creare ambiente virtuale"
                exit 1
            fi
        fi
    else
        warning "Ambiente virtuale già esistente"
    fi
fi

# Attiva ambiente virtuale (compatibilità Windows)
log "Attivazione ambiente virtuale..."
if [ -f "venv/bin/activate" ]; then
    # Linux/macOS
    source venv/bin/activate
elif [ -f "venv/Scripts/activate" ]; then
    # Windows
    source venv/Scripts/activate
else
    error "Script di attivazione ambiente virtuale non trovato"
    exit 1
fi
success "Ambiente virtuale attivato"

# Aggiorna pip
log "Aggiornamento pip..."
$PIP_CMD install --upgrade pip
success "pip aggiornato"

# Installa dipendenze
log "Installazione dipendenze Python..."
$PIP_CMD install -r requirements.txt
success "Dipendenze installate"

# Configurazione ambiente locale
log "Configurazione variabili d'ambiente per sviluppo locale..."

# Crea .env per sviluppo locale
cat > .env << EOF
# Configurazione sviluppo locale
DEBUG=True
DJANGO_SETTINGS_MODULE=cercollettiva.settings.local
SECRET_KEY=$($PYTHON_CMD -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
FIELD_ENCRYPTION_KEY=$($PYTHON_CMD -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')

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
$PYTHON_CMD manage.py migrate
success "Database SQLite configurato"

# Creazione superuser (opzionale)
echo ""
read -p "Vuoi creare un superuser? (y/n): " CREATE_SUPERUSER
if [[ $CREATE_SUPERUSER =~ ^[Yy]$ ]]; then
    log "Creazione superuser..."
    $PYTHON_CMD manage.py createsuperuser
    success "Superuser creato"
else
    warning "Superuser non creato (puoi crearlo successivamente con: $PYTHON_CMD manage.py createsuperuser)"
fi

# Raccolta file statici
log "Raccolta file statici..."
$PYTHON_CMD manage.py collectstatic --noinput
success "File statici raccolti"

# Creazione directory necessarie
log "Creazione directory necessarie..."
mkdir -p logs media staticfiles
success "Directory create"

# Test configurazione
log "Test configurazione..."
$PYTHON_CMD manage.py check
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
if [ -f "venv/bin/activate" ]; then
    echo "  source venv/bin/activate"
else
    echo "  venv\\Scripts\\activate  # Windows"
fi
echo "  $PYTHON_CMD manage.py runserver"
echo ""
echo -e "${BLUE}Accesso:${NC}"
echo "  Applicazione: http://127.0.0.1:8000/"
echo "  Setup: http://127.0.0.1:8000/setup"
echo "  Admin: http://127.0.0.1:8000/ceradmin/"
echo ""
echo -e "${BLUE}Comandi utili:${NC}"
echo "  Test: $PYTHON_CMD manage.py test"
echo "  Shell: $PYTHON_CMD manage.py shell"
echo "  Migrazioni: $PYTHON_CMD manage.py makemigrations && $PYTHON_CMD manage.py migrate"
echo "  Superuser: $PYTHON_CMD manage.py createsuperuser"
echo ""

# Avvio automatico (opzionale)
read -p "Vuoi avviare il server di sviluppo ora? (y/n): " START_SERVER
if [[ $START_SERVER =~ ^[Yy]$ ]]; then
    log "Avvio server di sviluppo..."
    echo ""
    echo -e "${BLUE}Server in avvio su http://127.0.0.1:8000/${NC}"
    echo -e "${YELLOW}Premi Ctrl+C per fermare il server${NC}"
    echo ""
    $PYTHON_CMD manage.py runserver
fi

echo ""
echo -e "${BLUE}Documentazione:${NC}"
echo "  - Modalità di deployment: docs/DEPLOYMENT_MODES.md"
echo "  - Sviluppo locale: docs/guides/development.md"
echo "  - Troubleshooting: docs/DEPLOYMENT_MODES.md#troubleshooting"
echo ""
echo -e "${GREEN}Buon lavoro con CerCollettiva! 🚀${NC}"