#!/bin/bash

# Script di validazione setup CerCollettiva
# Verifica che tutte le configurazioni siano corrette

set -e

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Funzioni per logging
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
echo "║                CerCollettiva Setup Validation                ║"
echo "║              Verifica configurazioni sistema                 ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

VALIDATION_ERRORS=0

# Funzione per incrementare errori
increment_errors() {
    VALIDATION_ERRORS=$((VALIDATION_ERRORS + 1))
}

# Verifica file di configurazione
log "Verifica file di configurazione..."

# Verifica .env
if [ -f ".env" ]; then
    success "File .env presente"
    
    # Verifica variabili essenziali
    if grep -q "SECRET_KEY=" .env && ! grep -q "SECRET_KEY=django-insecure" .env; then
        success "SECRET_KEY configurato"
    else
        error "SECRET_KEY non configurato o usa valore di default"
        increment_errors
    fi
    
    if grep -q "DEBUG=False" .env; then
        success "DEBUG configurato per produzione"
    elif grep -q "DEBUG=True" .env; then
        warning "DEBUG abilitato (OK per sviluppo)"
    else
        error "DEBUG non configurato"
        increment_errors
    fi
else
    error "File .env mancante"
    increment_errors
fi

# Verifica configurazioni Docker
if [ -f "docker-compose.yml" ]; then
    success "docker-compose.yml presente"
    
    # Verifica sintassi YAML
    if command -v docker-compose &> /dev/null; then
        if docker-compose config > /dev/null 2>&1; then
            success "Sintassi docker-compose.yml valida"
        else
            error "Sintassi docker-compose.yml non valida"
            increment_errors
        fi
    else
        warning "docker-compose non installato, skip validazione"
    fi
else
    error "docker-compose.yml mancante"
    increment_errors
fi

# Verifica configurazioni Nginx
if [ -f "config/nginx/nginx.conf" ]; then
    success "Configurazione Nginx presente"
    
    if command -v nginx &> /dev/null; then
        if nginx -t -c "$(pwd)/config/nginx/nginx.conf" > /dev/null 2>&1; then
            success "Configurazione Nginx valida"
        else
            error "Configurazione Nginx non valida"
            increment_errors
        fi
    else
        warning "Nginx non installato, skip validazione"
    fi
else
    error "Configurazione Nginx mancante"
    increment_errors
fi

# Verifica configurazioni MQTT
if [ -f "config/mosquitto/mosquitto.conf" ]; then
    success "Configurazione Mosquitto presente"
else
    error "Configurazione Mosquitto mancante"
    increment_errors
fi

# Verifica script di setup
log "Verifica script di setup..."

if [ -f "scripts/setup.sh" ]; then
    if [ -x "scripts/setup.sh" ]; then
        success "Script setup.sh eseguibile"
    else
        warning "Script setup.sh non eseguibile (chmod +x scripts/setup.sh)"
    fi
else
    error "Script setup.sh mancante"
    increment_errors
fi

if [ -f "scripts/backup.sh" ]; then
    if [ -x "scripts/backup.sh" ]; then
        success "Script backup.sh eseguibile"
    else
        warning "Script backup.sh non eseguibile"
    fi
else
    error "Script backup.sh mancante"
    increment_errors
fi

if [ -f "scripts/restore.sh" ]; then
    if [ -x "scripts/restore.sh" ]; then
        success "Script restore.sh eseguibile"
    else
        warning "Script restore.sh non eseguibile"
    fi
else
    error "Script restore.sh mancante"
    increment_errors
fi

# Verifica documentazione
log "Verifica documentazione..."

DOCS_FILES=(
    "docs/README.md"
    "docs/ARCHITECTURE.md"
    "docs/API_DOCUMENTATION.md"
    "docs/DEVELOPER_GUIDE.md"
    "docs/DEPLOYMENT_GUIDE.md"
    "docs/SECURITY_GUIDE.md"
    "CONTRIBUTING.md"
    "CHANGELOG.md"
)

for doc_file in "${DOCS_FILES[@]}"; do
    if [ -f "$doc_file" ]; then
        success "Documentazione presente: $doc_file"
    else
        error "Documentazione mancante: $doc_file"
        increment_errors
    fi
done

# Verifica ambiente Python
log "Verifica ambiente Python..."

if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if [[ $(echo "$PYTHON_VERSION >= 3.11" | bc -l) -eq 1 ]]; then
        success "Python $PYTHON_VERSION OK"
    else
        error "Python 3.11+ richiesto, trovato $PYTHON_VERSION"
        increment_errors
    fi
else
    error "Python3 non trovato"
    increment_errors
fi

# Verifica ambiente virtuale
if [ -d "venv" ]; then
    success "Ambiente virtuale presente"
    
    # Verifica attivazione
    if [ -n "$VIRTUAL_ENV" ]; then
        success "Ambiente virtuale attivo"
    else
        warning "Ambiente virtuale non attivo (source venv/bin/activate)"
    fi
else
    warning "Ambiente virtuale non trovato"
fi

# Verifica dipendenze Python
if [ -f "requirements.txt" ]; then
    success "requirements.txt presente"
    
    if [ -n "$VIRTUAL_ENV" ]; then
        if pip list > /dev/null 2>&1; then
            success "Pip funzionante"
            
            # Verifica Django
            if python -c "import django; print(django.get_version())" > /dev/null 2>&1; then
                DJANGO_VERSION=$(python -c "import django; print(django.get_version())")
                success "Django $DJANGO_VERSION installato"
            else
                error "Django non installato"
                increment_errors
            fi
        else
            error "Pip non funzionante"
            increment_errors
        fi
    fi
else
    error "requirements.txt mancante"
    increment_errors
fi

# Verifica database (se Django configurato)
if [ -n "$VIRTUAL_ENV" ] && python -c "import django" > /dev/null 2>&1; then
    log "Verifica configurazione Django..."
    
    # Test configurazione Django
    if python manage.py check > /dev/null 2>&1; then
        success "Configurazione Django valida"
    else
        error "Configurazione Django non valida"
        increment_errors
    fi
    
    # Test connessione database
    if python manage.py dbshell -c "SELECT 1;" > /dev/null 2>&1; then
        success "Connessione database OK"
    else
        warning "Connessione database fallita (verifica configurazione DB)"
    fi
fi

# Verifica servizi esterni
log "Verifica servizi esterni..."

# Verifica PostgreSQL
if command -v psql &> /dev/null; then
    if pg_isready > /dev/null 2>&1; then
        success "PostgreSQL disponibile"
    else
        warning "PostgreSQL non disponibile"
    fi
else
    warning "PostgreSQL client non installato"
fi

# Verifica Redis
if command -v redis-cli &> /dev/null; then
    if redis-cli ping > /dev/null 2>&1; then
        success "Redis disponibile"
    else
        warning "Redis non disponibile"
    fi
else
    warning "Redis client non installato"
fi

# Verifica MQTT
if command -v mosquitto_pub &> /dev/null; then
    if mosquitto_pub -h localhost -t test -m "test" > /dev/null 2>&1; then
        success "MQTT broker disponibile"
    else
        warning "MQTT broker non disponibile"
    fi
else
    warning "MQTT client non installato"
fi

# Verifica Docker
if command -v docker &> /dev/null; then
    if docker info > /dev/null 2>&1; then
        success "Docker disponibile"
    else
        warning "Docker non disponibile"
    fi
else
    warning "Docker non installato"
fi

# Risultato finale
echo ""
log "Validazione completata!"

if [ $VALIDATION_ERRORS -eq 0 ]; then
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                    Validazione Completata!                   ║${NC}"
    echo -e "${GREEN}║                  Tutte le configurazioni OK                  ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${GREEN}Il setup di CerCollettiva è pronto per l'uso! 🚀${NC}"
    exit 0
else
    echo -e "${RED}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║                    Validazione Fallita!                      ║${NC}"
    echo -e "${RED}║                $VALIDATION_ERRORS errori trovati                ║${NC}"
    echo -e "${RED}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${YELLOW}Risolvi gli errori sopra indicati e riprova la validazione.${NC}"
    exit 1
fi
