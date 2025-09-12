#!/bin/bash

###########################################
#  CerCollettiva - Uninstallation Script  #
#  Version: 1.0                           #
#  Date: Febbraio 2025                    #
###########################################

# Colori per output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m'

# Configurazione base
APP_NAME="CerCollettiva"
APP_ROOT="/home/pi"
APP_PATH="$APP_ROOT/$APP_NAME"
VENV_PATH="$APP_PATH/venv"
PROJECT_PATH="$APP_PATH/app"

# Funzione di logging
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[AVVISO] $1${NC}"
}

error() {
    echo -e "${RED}[ERRORE] $1${NC}"
    exit 1
}

# Funzione per chiedere conferma
confirm() {
    read -p "$1 (s/n): " choice
    case "$choice" in
        s|S) return 0 ;;
        *) return 1 ;;
    esac
}

# Verifica che lo script non venga eseguito come root
check_user() {
    if [ "$EUID" -eq 0 ]; then
        error "Non eseguire questo script come root. Eseguilo come l'utente che ha installato CerCollettiva."
    fi
}

# Ferma tutti i servizi correlati
stop_services() {
    log "Arresto dei servizi in esecuzione..."
    
    # Ferma Gunicorn
    if sudo systemctl is-active --quiet gunicorn; then
        sudo systemctl stop gunicorn
        sudo systemctl disable gunicorn
    fi
    
    # Ferma i processi supervisor
    if command -v supervisorctl &> /dev/null; then
        sudo supervisorctl stop cercollettiva_mqtt
    fi
    
    # Ferma Nginx
    if sudo systemctl is-active --quiet nginx; then
        sudo systemctl stop nginx
    fi
    
    # Ferma Mosquitto
    if sudo systemctl is-active --quiet mosquitto; then
        sudo systemctl stop mosquitto
    fi
}

# Rimuovi configurazioni da Nginx
remove_nginx_config() {
    log "Rimozione configurazione Nginx..."
    
    if [ -f /etc/nginx/sites-enabled/cercollettiva ]; then
        sudo rm -f /etc/nginx/sites-enabled/cercollettiva
    fi
    
    if [ -f /etc/nginx/sites-available/cercollettiva ]; then
        sudo rm -f /etc/nginx/sites-available/cercollettiva
    fi
    
    # Ripristina default se è stato rimosso
    if [ ! -f /etc/nginx/sites-enabled/default ] && [ -f /etc/nginx/sites-available/default ]; then
        sudo ln -sf /etc/nginx/sites-available/default /etc/nginx/sites-enabled/
    fi
    
    sudo systemctl restart nginx
}

# Rimuovi configurazioni SSL se presenti
remove_ssl_config() {
    log "Verifico se ci sono configurazioni SSL da rimuovere..."
    
    # Leggi .env per ottenere informazioni sul dominio
    if [ -f "$APP_PATH/.env" ]; then
        source "$APP_PATH/.env"
        
        if [ -n "$PUBLIC_DOMAIN" ]; then
            warn "Trovato dominio configurato: $PUBLIC_DOMAIN"
            if confirm "Vuoi rimuovere i certificati SSL per questo dominio?"; then
                sudo certbot delete --cert-name "$PUBLIC_DOMAIN" --non-interactive
            fi
        fi
    fi
}

# Rimuovi configurazioni systemd
remove_systemd_config() {
    log "Rimozione configurazioni systemd..."
    
    if [ -f /etc/systemd/system/gunicorn.service ]; then
        sudo rm -f /etc/systemd/system/gunicorn.service
        sudo systemctl daemon-reload
    fi
}

# Rimuovi configurazioni supervisor
remove_supervisor_config() {
    log "Rimozione configurazioni supervisor..."
    
    if [ -f /etc/supervisor/conf.d/cercollettiva.conf ]; then
        sudo rm -f /etc/supervisor/conf.d/cercollettiva.conf
        sudo supervisorctl reread
        sudo supervisorctl update
    fi
}

# Rimuovi configurazioni MQTT
remove_mqtt_config() {
    log "Rimozione configurazioni MQTT..."
    
    if [ -f /etc/mosquitto/conf.d/default.conf ]; then
        sudo rm -f /etc/mosquitto/conf.d/default.conf
    fi
    
    if [ -f /etc/mosquitto/passwd ]; then
        # Rimuovi solo l'utente cercollettiva, non l'intero file
        if grep -q "cercollettiva:" /etc/mosquitto/passwd; then
            warn "Rimozione utente MQTT 'cercollettiva'"
            sudo mosquitto_passwd -D /etc/mosquitto/passwd cercollettiva
        fi
    fi
    
    sudo systemctl restart mosquitto
}

# Rimuovi database PostgreSQL
remove_database() {
    log "Rimozione database PostgreSQL..."
    
    if sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw cercollettiva; then
        if confirm "Sei sicuro di voler eliminare il database 'cercollettiva'? Tutti i dati verranno persi permanentemente!"; then
            sudo -u postgres psql -c "DROP DATABASE cercollettiva;"
            log "Database 'cercollettiva' eliminato con successo."
        else
            warn "Eliminazione del database annullata. Il database 'cercollettiva' è ancora presente."
        fi
    else
        log "Database 'cercollettiva' non trovato."
    fi
    
    if sudo -u postgres psql -c "SELECT 1 FROM pg_roles WHERE rolname='cercollettiva'" | grep -q 1; then
        if confirm "Vuoi eliminare anche l'utente PostgreSQL 'cercollettiva'?"; then
            sudo -u postgres psql -c "DROP USER cercollettiva;"
            log "Utente PostgreSQL 'cercollettiva' eliminato con successo."
        else
            warn "Utente PostgreSQL 'cercollettiva' non eliminato."
        fi
    else
        log "Utente PostgreSQL 'cercollettiva' non trovato."
    fi
}

# Rimuovi i file dell'applicazione
remove_application_files() {
    log "Rimozione file dell'applicazione..."
    
    if [ -d "$APP_PATH" ]; then
        if confirm "Sei sicuro di voler eliminare tutti i file dell'applicazione in '$APP_PATH'?"; then
            rm -rf "$APP_PATH"
            log "Directory dell'applicazione rimossa con successo."
        else
            warn "Eliminazione dei file annullata. I file sono ancora presenti in '$APP_PATH'."
        fi
    else
        log "Directory dell'applicazione non trovata. Nessun file da rimuovere."
    fi
}

# Ripristina configurazioni firewall
restore_firewall() {
    log "Ripristino configurazione firewall..."
    
    if command -v ufw &> /dev/null; then
        if confirm "Vuoi rimuovere le regole del firewall specifiche per CerCollettiva?"; then
            # Rimuovi le regole specifiche
            sudo ufw delete allow 80/tcp
            sudo ufw delete allow 443/tcp
            
            log "Regole del firewall rimosse. Mantieni il firewall attivo con le regole di base?"
            if ! confirm "Mantieni firewall attivo?"; then
                sudo ufw disable
                log "Firewall disattivato."
            fi
        fi
    fi
}

# Chiedi se rimuovere le dipendenze
remove_dependencies() {
    log "Verifico dipendenze installate..."
    
    if confirm "Vuoi rimuovere le dipendenze di sistema installate? Questo potrebbe influire su altre applicazioni se le utilizzano."; then
        sudo apt remove -y postgresql postgresql-contrib nginx supervisor mosquitto mosquitto-clients
        
        if confirm "Vuoi rimuovere anche i file di configurazione delle dipendenze?"; then
            sudo apt purge -y postgresql postgresql-contrib nginx supervisor mosquitto mosquitto-clients
        fi
        
        if [ -d /var/lib/postgresql ]; then
            warn "I dati di PostgreSQL sono ancora presenti in /var/lib/postgresql"
            if confirm "Vuoi rimuovere completamente tutti i dati PostgreSQL? ATTENZIONE: questa operazione è irreversibile!"; then
                sudo rm -rf /var/lib/postgresql
            fi
        fi
        
        sudo apt autoremove -y
        log "Dipendenze rimosse."
    else
        log "Le dipendenze di sistema sono state mantenute."
    fi
}

# Funzione principale
main() {
    echo -e "${RED}=== Disinstallazione CerCollettiva ===${NC}"
    
    check_user
    
    if ! confirm "Questa procedura rimuoverà completamente CerCollettiva e tutti i suoi dati. Sei sicuro di voler continuare?"; then
        log "Disinstallazione annullata."
        exit 0
    fi
    
    stop_services
    remove_nginx_config
    remove_ssl_config
    remove_systemd_config
    remove_supervisor_config
    remove_mqtt_config
    remove_database
    remove_application_files
    restore_firewall
    remove_dependencies
    
    echo -e "\n${GREEN}=== Disinstallazione completata! ===${NC}"
    echo -e "CerCollettiva è stato rimosso dal sistema. Alcuni file di configurazione e log potrebbero essere ancora presenti."
    
    if confirm "Vuoi eseguire un riavvio del sistema per assicurarti che tutti i servizi siano correttamente fermati?"; then
        log "Riavvio del sistema..."
        sudo reboot
    fi
}

# Avvio
main