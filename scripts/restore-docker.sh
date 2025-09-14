#!/bin/bash

# Script di restore per Docker CerCollettiva
# Questo script ripristina backup del database, file media e configurazioni

set -e

# Configurazione
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Database connection
DB_HOST=${DB_HOST:-db}
DB_NAME=${DB_NAME:-cercollettiva}
DB_USER=${DB_USER:-cercollettiva_user}
DB_PASSWORD=${DB_PASSWORD:-cercollettiva_pass}

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Funzioni di logging
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
echo "║                CerCollettiva Docker Restore                  ║"
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
    echo ""
    read -p "Sei sicuro di voler continuare? (yes/no): " CONFIRM
    if [ "$CONFIRM" != "yes" ]; then
        log "Operazione annullata"
        rm -rf "$TEMP_DIR"
        exit 0
    fi
fi

# Attendi che il database sia pronto
log "Attesa database pronto..."
until pg_isready -h "$DB_HOST" -p 5432 -U "$DB_USER"; do
    log "Database non pronto, attendo..."
    sleep 2
done
success "Database pronto"

# Restore database
log "Ripristino database..."
if [ -f "$BACKUP_DATE_DIR/database.dump" ]; then
    # Drop e ricrea database
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d postgres -c "DROP DATABASE IF EXISTS $DB_NAME;"
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d postgres -c "CREATE DATABASE $DB_NAME;"
    
    # Restore database
    PGPASSWORD="$DB_PASSWORD" pg_restore -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" --no-password --clean --if-exists "$BACKUP_DATE_DIR/database.dump"
    success "Database ripristinato"
else
    warning "File database.dump non trovato nel backup"
fi

# Restore file media
log "Ripristino file media..."
if [ -f "$BACKUP_DATE_DIR/media.tar.gz" ]; then
    tar -xzf "$BACKUP_DATE_DIR/media.tar.gz" -C /media
    success "File media ripristinati"
else
    warning "File media.tar.gz non trovato nel backup"
fi

# Restore configurazioni
log "Ripristino configurazioni..."
if [ -f "$BACKUP_DATE_DIR/.env" ]; then
    cp "$BACKUP_DATE_DIR/.env" /.env.backup
    success "File .env ripristinato come .env.backup"
fi

if [ -f "$BACKUP_DATE_DIR/docker-compose.yml" ]; then
    cp "$BACKUP_DATE_DIR/docker-compose.yml" /docker-compose.yml.backup
    success "File docker-compose.yml ripristinato come docker-compose.yml.backup"
fi

if [ -d "$BACKUP_DATE_DIR/config" ]; then
    rm -rf /config.backup
    cp -r "$BACKUP_DATE_DIR/config" /config.backup
    success "Configurazioni ripristinate in /config.backup"
fi

# Cleanup
rm -rf "$TEMP_DIR"
success "Cleanup completato"

# Notifiche (opzionali)
if [ ! -z "$SLACK_WEBHOOK_URL" ]; then
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"🔄 Restore CerCollettiva completato da: $(basename $BACKUP_FILE)\"}" \
        "$SLACK_WEBHOOK_URL" 2>/dev/null || warning "Errore invio notifica Slack"
fi

if [ ! -z "$TELEGRAM_BOT_TOKEN" ] && [ ! -z "$TELEGRAM_CHAT_ID" ]; then
    curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" \
        -d "text=🔄 Restore CerCollettiva completato da: $(basename $BACKUP_FILE)" \
        -d "chat_id=$TELEGRAM_CHAT_ID" 2>/dev/null || warning "Errore invio notifica Telegram"
fi

log "Restore completato con successo!"
echo -e "${GREEN}║                    Restore Completato!                       ║${NC}"
echo -e "${BLUE}Dettagli restore:${NC}"
echo "  - Backup: $BACKUP_FILE"
echo "  - Database: Ripristinato"
echo "  - Media: Ripristinati"
echo "  - Config: Ripristinate"
