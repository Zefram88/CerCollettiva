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
trap 'error "Setup failed at line $LINENO"' ERR

# DJANGO_SETTINGS_MODULE è impostato dal docker-compose (prod/dev)
log "DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE"

# Attesa secrets (se montato)
if [ -d "/secrets" ]; then
    i=0; while [ ! -f "/secrets/redis_password" ] || [ ! -f "/secrets/app.env" ]; do
        if [ $i -ge 30 ]; then warning "Timeout attesa /secrets"; break; fi
        log "Attesa /secrets..."; sleep 1; i=$((i+1));
    done
    # Importa app.env se presente (non sovrascrive variabili già esportate)
    if [ -f "/secrets/app.env" ]; then
        set -a; . /secrets/app.env; set +a
        success "app.env importato da /secrets"
    fi
    # REDIS_PASSWORD da secrets se non già impostato
    if [ -z "$REDIS_PASSWORD" ] && [ -f "/secrets/redis_password" ]; then
        REDIS_PASSWORD=$(cat /secrets/redis_password)
        export REDIS_PASSWORD
        success "REDIS_PASSWORD importata da /secrets"
    fi
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

# Verifica se è il primo avvio
if [ ! -f "/app/.setup_complete" ]; then
    log "Primo avvio rilevato - avvio setup automatico..."
    
    # Genera chiavi di sicurezza
    log "Generazione SECRET_KEY e FIELD_ENCRYPTION_KEY..."
    SECRET_KEY=$(python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
    FIELD_ENCRYPTION_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
    
    # Crea file .env se non esiste
    if [ ! -f "/app/.env" ]; then
        log "Creazione file .env da template..."
        if [ -f "/app/env.example" ]; then
            cp /app/env.example /app/.env
            success "File .env creato da env.example"
        else
            error "File env.example non trovato"
        fi
    else
        log "File .env già esistente"
    fi
    
    # Aggiorna chiavi nel file .env
    log "Aggiornamento chiavi di sicurezza..."
    sed -i "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" /app/.env
    sed -i "s/FIELD_ENCRYPTION_KEY=.*/FIELD_ENCRYPTION_KEY=$FIELD_ENCRYPTION_KEY/" /app/.env
    
    # Attendi dipendenze database
    log "Attesa dipendenze database..."
    python /app/scripts/wait-for-db.py
    
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
    python manage.py check --deploy
    
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
