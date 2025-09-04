#!/bin/bash

# Script di restore per CerCollettiva
# Questo script ripristina backup del database, file media e configurazioni

set -e  # Exit on any error

# Configurazione
BACKUP_DIR="/backups/cercollettiva"

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
echo "║                    CerCollettiva Restore                     ║"
echo "║              Sistema di ripristino backup                   ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Verifica parametri
if [ $# -eq 0 ]; then
    error "Uso: $0 <backup_file> [--force]"
    echo ""
    echo "Esempi:"
    echo "  $0 cercollettiva_backup_20240101_120000.tar.gz"
    echo "  $0 cercollettiva_backup_20240101_120000.tar.gz --force"
    echo ""
    echo "Backup disponibili:"
    if [ -d "$BACKUP_DIR" ]; then
        ls -la "$BACKUP_DIR"/*.tar.gz 2>/dev/null || echo "  Nessun backup trovato"
    else
        echo "  Directory backup non trovata: $BACKUP_DIR"
    fi
    exit 1
fi

BACKUP_FILE="$1"
FORCE_RESTORE=false

if [ "$2" = "--force" ]; then
    FORCE_RESTORE=true
fi

# Verifica file backup
if [ ! -f "$BACKUP_FILE" ]; then
    # Prova nella directory backup
    if [ -f "$BACKUP_DIR/$BACKUP_FILE" ]; then
        BACKUP_FILE="$BACKUP_DIR/$BACKUP_FILE"
    else
        error "File backup non trovato: $BACKUP_FILE"
        exit 1
    fi
fi

log "File backup: $BACKUP_FILE"

# Verifica integrità backup
log "Verifica integrità backup..."
if ! tar -tzf "$BACKUP_FILE" > /dev/null 2>&1; then
    error "File backup corrotto o non valido!"
    exit 1
fi
success "Backup verificato"

# Estrai backup
TEMP_DIR=$(mktemp -d)
log "Estrazione backup in: $TEMP_DIR"
tar -xzf "$BACKUP_FILE" -C "$TEMP_DIR"
success "Backup estratto"

# Trova directory backup estratta
BACKUP_DATE_DIR=$(find "$TEMP_DIR" -maxdepth 1 -type d -name "cercollettiva_backup_*" | head -1)
if [ -z "$BACKUP_DATE_DIR" ]; then
    error "Struttura backup non valida"
    exit 1
fi

log "Directory backup: $BACKUP_DATE_DIR"

# Conferma restore
if [ "$FORCE_RESTORE" = false ]; then
    echo ""
    warning "ATTENZIONE: Questa operazione sovrascriverà i dati esistenti!"
    echo ""
    echo "Dati che verranno ripristinati:"
    echo "  - Database PostgreSQL"
    echo "  - File media"
    echo "  - Configurazioni"
    echo "  - Logs"
    echo ""
    read -p "Sei sicuro di voler continuare? (yes/no): " CONFIRM
    if [ "$CONFIRM" != "yes" ]; then
        log "Operazione annullata"
        rm -rf "$TEMP_DIR"
        exit 0
    fi
fi

# Stop servizi (se Docker)
if command -v docker-compose &> /dev/null && [ -f "docker-compose.yml" ]; then
    log "Stop servizi Docker..."
    docker-compose down
    success "Servizi fermati"
fi

# Restore database
log "Ripristino database..."
if [ -f "$BACKUP_DATE_DIR/database.dump" ]; then
    if command -v pg_restore &> /dev/null; then
        # Drop e ricrea database
        psql -h ${DB_HOST:-localhost} \
             -U ${DB_USER:-cercollettiva_user} \
             -d postgres \
             -c "DROP DATABASE IF EXISTS ${DB_NAME:-cercollettiva};"
        psql -h ${DB_HOST:-localhost} \
             -U ${DB_USER:-cercollettiva_user} \
             -d postgres \
             -c "CREATE DATABASE ${DB_NAME:-cercollettiva};"
        
        # Restore database
        pg_restore -h ${DB_HOST:-localhost} \
                   -U ${DB_USER:-cercollettiva_user} \
                   -d ${DB_NAME:-cercollettiva} \
                   --no-password \
                   --clean \
                   --if-exists \
                   "$BACKUP_DATE_DIR/database.dump"
        success "Database ripristinato"
    else
        error "pg_restore non trovato"
        exit 1
    fi
else
    warning "File database.dump non trovato nel backup"
fi

# Restore file media
log "Ripristino file media..."
if [ -f "$BACKUP_DATE_DIR/media.tar.gz" ]; then
    if [ -d "media" ]; then
        rm -rf media/
    fi
    tar -xzf "$BACKUP_DATE_DIR/media.tar.gz"
    success "File media ripristinati"
else
    warning "File media.tar.gz non trovato nel backup"
fi

# Restore configurazioni
log "Ripristino configurazioni..."
if [ -f "$BACKUP_DATE_DIR/.env" ]; then
    cp "$BACKUP_DATE_DIR/.env" .env.backup
    success "File .env ripristinato come .env.backup"
fi

if [ -d "$BACKUP_DATE_DIR/config" ]; then
    if [ -d "config" ]; then
        rm -rf config/
    fi
    cp -r "$BACKUP_DATE_DIR/config" .
    success "Configurazioni ripristinate"
fi

if [ -f "$BACKUP_DATE_DIR/docker-compose.yml" ]; then
    cp "$BACKUP_DATE_DIR/docker-compose.yml" docker-compose.yml.backup
    success "File docker-compose.yml ripristinato come docker-compose.yml.backup"
fi

# Restore logs
log "Ripristino logs..."
if [ -f "$BACKUP_DATE_DIR/logs.tar.gz" ]; then
    if [ -d "logs" ]; then
        rm -rf logs/
    fi
    tar -xzf "$BACKUP_DATE_DIR/logs.tar.gz"
    success "Logs ripristinati"
else
    warning "File logs.tar.gz non trovato nel backup"
fi

# Pulizia file temporanei
rm -rf "$TEMP_DIR"

# Start servizi (se Docker)
if command -v docker-compose &> /dev/null && [ -f "docker-compose.yml" ]; then
    log "Start servizi Docker..."
    docker-compose up -d
    success "Servizi avviati"
fi

# Verifica restore
log "Verifica ripristino..."
if command -v python &> /dev/null; then
    python manage.py check
    success "Configurazione Django verificata"
else
    warning "Python non trovato, skip verifica Django"
fi

# Notifica completamento
log "Restore completato con successo!"
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                    Restore Completato!                       ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Dettagli restore:${NC}"
echo "  - Backup: $BACKUP_FILE"
echo "  - Database: Ripristinato"
echo "  - File media: Ripristinati"
echo "  - Configurazioni: Ripristinate"
echo "  - Logs: Ripristinati"
echo ""

# Invia notifica (se configurato)
if [ ! -z "$SLACK_WEBHOOK_URL" ]; then
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"🔄 Restore CerCollettiva completato da: $(basename $BACKUP_FILE)\"}" \
        "$SLACK_WEBHOOK_URL" 2>/dev/null || warning "Errore invio notifica Slack"
fi

if [ ! -z "$TELEGRAM_BOT_TOKEN" ] && [ ! -z "$TELEGRAM_CHAT_ID" ]; then
    curl -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" \
        -d "chat_id=$TELEGRAM_CHAT_ID" \
        -d "text=🔄 Restore CerCollettiva completato da: $(basename $BACKUP_FILE)" 2>/dev/null || warning "Errore invio notifica Telegram"
fi

echo -e "${GREEN}Restore completato con successo! 🎉${NC}"