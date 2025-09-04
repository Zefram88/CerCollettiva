#!/bin/bash

# Script di backup automatico per CerCollettiva
# Questo script crea backup del database, file media e configurazioni

set -e  # Exit on any error

# Configurazione
BACKUP_DIR="/backups/cercollettiva"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}

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
echo "║                    CerCollettiva Backup                      ║"
echo "║              Sistema di backup automatico                    ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Crea directory backup
log "Creazione directory backup..."
mkdir -p "$BACKUP_DIR/$DATE"
success "Directory backup creata: $BACKUP_DIR/$DATE"

# Backup database
log "Backup database PostgreSQL..."
if command -v pg_dump &> /dev/null; then
    pg_dump -h ${DB_HOST:-localhost} \
            -U ${DB_USER:-cercollettiva_user} \
            -d ${DB_NAME:-cercollettiva} \
            --no-password \
            --format=custom \
            --compress=9 \
            --file="$BACKUP_DIR/$DATE/database.dump"
    success "Database backup completato"
else
    error "pg_dump non trovato"
    exit 1
fi

# Backup file media
log "Backup file media..."
if [ -d "media" ]; then
    tar -czf "$BACKUP_DIR/$DATE/media.tar.gz" media/
    success "File media backup completati"
else
    warning "Directory media non trovata"
fi

# Backup configurazioni
log "Backup configurazioni..."
mkdir -p "$BACKUP_DIR/$DATE/config"
cp -r config/ "$BACKUP_DIR/$DATE/config/" 2>/dev/null || warning "Directory config non trovata"
cp .env "$BACKUP_DIR/$DATE/" 2>/dev/null || warning "File .env non trovato"
cp docker-compose.yml "$BACKUP_DIR/$DATE/" 2>/dev/null || warning "File docker-compose.yml non trovato"
success "Configurazioni backup completate"

# Backup logs (ultimi 7 giorni)
log "Backup logs..."
if [ -d "logs" ]; then
    find logs/ -name "*.log" -mtime -7 -exec tar -czf "$BACKUP_DIR/$DATE/logs.tar.gz" {} +
    success "Logs backup completati"
else
    warning "Directory logs non trovata"
fi

# Crea archivio completo
log "Creazione archivio completo..."
cd "$BACKUP_DIR"
tar -czf "cercollettiva_backup_$DATE.tar.gz" "$DATE/"
rm -rf "$DATE/"
success "Archivio completo creato: cercollettiva_backup_$DATE.tar.gz"

# Calcola dimensione backup
BACKUP_SIZE=$(du -h "cercollettiva_backup_$DATE.tar.gz" | cut -f1)
log "Dimensione backup: $BACKUP_SIZE"

# Upload a S3 (se configurato)
if [ ! -z "$BACKUP_S3_BUCKET" ] && [ ! -z "$BACKUP_S3_ACCESS_KEY" ] && [ ! -z "$BACKUP_S3_SECRET_KEY" ]; then
    log "Upload backup a S3..."
    if command -v aws &> /dev/null; then
        export AWS_ACCESS_KEY_ID="$BACKUP_S3_ACCESS_KEY"
        export AWS_SECRET_ACCESS_KEY="$BACKUP_S3_SECRET_KEY"
        aws s3 cp "cercollettiva_backup_$DATE.tar.gz" "s3://$BACKUP_S3_BUCKET/backups/"
        success "Backup caricato su S3"
    else
        warning "AWS CLI non trovato, skip upload S3"
    fi
else
    warning "Configurazione S3 non trovata, skip upload"
fi

# Pulizia backup vecchi
log "Pulizia backup vecchi (più di $RETENTION_DAYS giorni)..."
find "$BACKUP_DIR" -name "cercollettiva_backup_*.tar.gz" -mtime +$RETENTION_DAYS -delete
success "Pulizia backup completata"

# Verifica integrità backup
log "Verifica integrità backup..."
if tar -tzf "cercollettiva_backup_$DATE.tar.gz" > /dev/null 2>&1; then
    success "Backup verificato e integro"
else
    error "Backup corrotto!"
    exit 1
fi

# Notifica completamento
log "Backup completato con successo!"
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                    Backup Completato!                        ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Dettagli backup:${NC}"
echo "  - File: cercollettiva_backup_$DATE.tar.gz"
echo "  - Dimensione: $BACKUP_SIZE"
echo "  - Posizione: $BACKUP_DIR"
echo "  - Retention: $RETENTION_DAYS giorni"
echo ""

# Invia notifica (se configurato)
if [ ! -z "$SLACK_WEBHOOK_URL" ]; then
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"✅ Backup CerCollettiva completato: cercollettiva_backup_$DATE.tar.gz ($BACKUP_SIZE)\"}" \
        "$SLACK_WEBHOOK_URL" 2>/dev/null || warning "Errore invio notifica Slack"
fi

if [ ! -z "$TELEGRAM_BOT_TOKEN" ] && [ ! -z "$TELEGRAM_CHAT_ID" ]; then
    curl -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" \
        -d "chat_id=$TELEGRAM_CHAT_ID" \
        -d "text=✅ Backup CerCollettiva completato: cercollettiva_backup_$DATE.tar.gz ($BACKUP_SIZE)" 2>/dev/null || warning "Errore invio notifica Telegram"
fi

echo -e "${GREEN}Backup completato con successo! 🎉${NC}"
