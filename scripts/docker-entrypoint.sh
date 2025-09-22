#!/bin/bash
# Docker Entrypoint Script per CerCollettiva
# Esegue setup automatico al primo avvio del container

set -e

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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
    exit 1
}

# Banner
echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                CerCollettiva Docker Entrypoint               ║"
echo "║              Setup automatico al primo avvio                 ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Funzione per gestire errori
# trap 'error "Setup failed at line $LINENO"' ERR  # Disabilitato per compatibilità

# Environment settings con backward compatibility
DEPLOYMENT_MODE="${DEPLOYMENT_MODE:-production}"

# Backward compatibility: "prod" → "production", "dev" → "development"
case "$DEPLOYMENT_MODE" in
    "prod") 
        DEPLOYMENT_MODE="production"
        warning "DEPLOYMENT_MODE='prod' è deprecato, usa 'production'"
        ;;
    "dev")
        DEPLOYMENT_MODE="development" 
        warning "DEPLOYMENT_MODE='dev' è deprecato, usa 'development'"
        ;;
esac

DEV_MODE="${DEV_MODE:-false}"
log "DEPLOYMENT_MODE=$DEPLOYMENT_MODE"
log "DEV_MODE=$DEV_MODE"
log "DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE"

# Attendi secrets (se montato)
log "Verifica directory /secrets..."
if [ -d "/secrets" ]; then
    log "Directory /secrets trovata, attesa secrets..."
    i=0; while [ ! -f "/secrets/django_secret_key" ] || [ ! -f "/secrets/field_encryption_key" ]; do
        if [ $i -ge 60 ]; then error "Timeout attesa secrets"; break; fi
        log "Attesa secrets... ($i/60)"; sleep 1; i=$((i+1));
    done
    # Importa le chiavi dal volume secrets
    SECRET_KEY=$(cat /secrets/django_secret_key | tr -d '\n')
    FIELD_ENCRYPTION_KEY=$(cat /secrets/field_encryption_key | tr -d '\n')
    export SECRET_KEY
    export FIELD_ENCRYPTION_KEY
    success "Chiavi di sicurezza importate da /secrets"
    
    # REDIS_PASSWORD da secrets se non già impostato
    if [ -z "$REDIS_PASSWORD" ] && [ -f "/secrets/redis_password" ]; then
        REDIS_PASSWORD=$(cat /secrets/redis_password)
        export REDIS_PASSWORD
        success "REDIS_PASSWORD importata da /secrets"
    fi
else
    warning "Directory /secrets non trovata, usando chiavi di default"
    # Usa chiavi di default per test
    SECRET_KEY="django-insecure-test-key-for-development-only-change-in-production"
    FIELD_ENCRYPTION_KEY="7OmLozExKYcMJCO7Jof_OGnnRm2-P1zYpnY3eLG7EWE="
    export SECRET_KEY
    export FIELD_ENCRYPTION_KEY
    success "Chiavi di default impostate per test"
fi

# Costruisci REDIS_URL coerente dall'ambiente e allinealo a /app/.env
REDIS_HOST=${REDIS_HOST:-redis}
REDIS_PORT=${REDIS_PORT:-6379}
REDIS_DB=${REDIS_DB:-1}
if [ -n "$REDIS_PASSWORD" ]; then
    REDIS_URL="redis://:$REDIS_PASSWORD@$REDIS_HOST:$REDIS_PORT/$REDIS_DB"
else
    REDIS_URL="redis://$REDIS_HOST:$REDIS_PORT/$REDIS_DB"
fi
export REDIS_URL
log "REDIS_URL (sintetizzato)=$REDIS_URL"

# ----------------------------------------------------
# NUOVO BLOCCO DI ATTESA ROBUSTO PER IL DATABASE
# ----------------------------------------------------
DB_HOST=${DB_HOST:-db}
DB_USER=${DB_USER:-cercollettiva_user}
DB_NAME=${DB_NAME:-cercollettiva}

log "Attesa che il database sia pronto su $DB_HOST..."
until pg_isready -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME"; do
  echo >&2 "Database non ancora disponibile - in attesa..."
  sleep 1
done
success "Database è pronto!"
# ----------------------------------------------------

# Verifica se è il primo avvio
if [ ! -f "/app/.setup_complete" ]; then
    log "Primo avvio rilevato - avvio setup automatico..."
    
    # Crea file .env se non esiste
    if [ ! -f "/app/.env" ]; then
        log "Creazione file .env con configurazione base..."
        cat > /app/.env << EOF
# Configurazione base CerCollettiva
SECRET_KEY="$SECRET_KEY"
FIELD_ENCRYPTION_KEY="$FIELD_ENCRYPTION_KEY"
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1
EOF
        success "File .env creato con configurazione base"
    else
        log "File .env già esistente"
        # Aggiorna chiavi nel file .env esistente
        log "Aggiornamento chiavi di sicurezza..."
        sed -i "s/SECRET_KEY=.*/SECRET_KEY=\"$SECRET_KEY\"/" /app/.env
        sed -i "s/FIELD_ENCRYPTION_KEY=.*/FIELD_ENCRYPTION_KEY=\"$FIELD_ENCRYPTION_KEY\"/" /app/.env
    fi
    
    # Esegui migrazioni database
    log "Esecuzione migrazioni database..."
    python manage.py migrate --noinput
    
    # Raccogli file statici
    log "Raccolta file statici..."
    python manage.py collectstatic --noinput
    
    # Crea directory necessarie
    log "Creazione directory necessarie..."
    mkdir -p /app/logs /app/media /app/staticfiles
    
    # Verifica configurazione Django
    log "Verifica configurazione Django..."
    if [ "$DEPLOYMENT_MODE" = "production" ]; then
        python manage.py check --deploy
    else
        python manage.py check
    fi
    
    # Marca setup come completato
    touch /app/.setup_complete
    success "Setup automatico completato con successo!"
    
    echo -e "${GREEN}"
    echo "╔═════════════════════════════════════════════════════════════╗"
    echo "║                    Setup Completato!                        ║"
    echo "║              CerCollettiva pronto per l'uso                 ║"
    echo "╚═════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""
    echo -e "${BLUE}Accesso all'applicazione:${NC}"
    echo "  - Applicazione: http://localhost:8000/"
    echo "  - Setup iniziale: http://localhost:8000/setup"
    echo "  - Admin: http://localhost:8000/ceradmin/"
    echo ""
    echo -e "${YELLOW}Prossimo passo:${NC}"
    echo "  Vai su http://localhost:8000/setup per creare il superuser"
    echo ""
    
else
    log "Setup già completato - avvio applicazione..."
fi

# (Opzionale) Genera migrazioni in DEV quando esplicitamente richiesto
if [ "${AUTO_MAKEMIGRATIONS:-false}" = "true" ]; then
    log "Generazione migrazioni (AUTO_MAKEMIGRATIONS=true) ..."
    python manage.py makemigrations || warning "makemigrations ha restituito un codice di errore"
fi

# Applica sempre le migrazioni all'avvio (idempotente/sicuro in prod)
if [ "${AUTO_MIGRATE:-true}" = "true" ]; then
    log "Applicazione migrazioni database (AUTO_MIGRATE=true) ..."
    python manage.py migrate --noinput
fi

# Avvia applicazione
log "Avvio applicazione CerCollettiva..."
exec "$@"
