#!/bin/bash
# Script per configurazione automatica Lets Encrypt con Docker

set -e

# Configurazione
DOMAIN=${1:-"example.com"}
EMAIL=${2:-"admin@example.com"}
NGINX_ENV=${3:-"prod"}

echo "🔧 Configurazione Lets Encrypt per dominio: $DOMAIN"
echo "📧 Email: $EMAIL"
echo "🌐 Ambiente: $NGINX_ENV"

# Verifica prerequisiti
if [ -z "$DOMAIN" ] || [ "$DOMAIN" = "example.com" ]; then
    echo "❌ Errore: Specificare un dominio valido"
    echo "Uso: $0 <dominio> <email> [prod|dev]"
    exit 1
fi

# Crea directory per certificati
mkdir -p config/ssl

# Genera certificati self-signed per sviluppo
if [ "$NGINX_ENV" = "dev" ]; then
    echo "🔐 Generazione certificati self-signed per sviluppo..."
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout config/ssl/key.pem \
        -out config/ssl/cert.pem \
        -subj "/C=IT/ST=Italy/L=Rome/O=CerCollettiva/CN=$DOMAIN"
    echo "✅ Certificati self-signed generati"
    exit 0
fi

# Per produzione: usa certbot con Docker
echo "🔐 Configurazione Lets Encrypt per produzione..."

# Crea docker-compose per certbot
cat > docker-compose.certbot.yml << EOF
version: '3.8'

services:
  certbot:
    image: certbot/certbot
    container_name: cercollettiva_certbot
    volumes:
      - ./config/ssl:/etc/letsencrypt
      - ./config/nginx/conf.d:/etc/nginx/conf.d
    command: certonly --webroot --webroot-path=/etc/nginx/conf.d -d $DOMAIN --email $EMAIL --agree-tos --non-interactive
    depends_on:
      - nginx
    networks:
      - cercollettiva_network

networks:
  cercollettiva_network:
    external: true
EOF

# Avvia nginx temporaneo per validazione
echo "🚀 Avvio nginx temporaneo per validazione..."
docker-compose up -d nginx

# Genera certificati
echo "🔐 Generazione certificati Lets Encrypt..."
docker-compose -f docker-compose.certbot.yml run --rm certbot

# Copia certificati
echo "📋 Copia certificati..."
cp config/ssl/live/$DOMAIN/fullchain.pem config/ssl/cert.pem
cp config/ssl/live/$DOMAIN/privkey.pem config/ssl/key.pem

# Configura rinnovo automatico
echo "🔄 Configurazione rinnovo automatico..."
cat > scripts/renew-certificates.sh << 'EOF'
#!/bin/bash
# Script per rinnovo automatico certificati Lets Encrypt

docker-compose -f docker-compose.certbot.yml run --rm certbot renew
docker-compose restart nginx
EOF

chmod +x scripts/renew-certificates.sh

# Aggiungi cron job per rinnovo (opzionale)
echo "⏰ Per rinnovo automatico, aggiungi al crontab:"
echo "0 12 * * * $(pwd)/scripts/renew-certificates.sh"

echo "✅ Configurazione Lets Encrypt completata!"
echo "🌐 Il sito sarà disponibile su: https://$DOMAIN"
