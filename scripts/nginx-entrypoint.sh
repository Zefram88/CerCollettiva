#!/bin/sh
set -e

echo "[nginx-entrypoint] Avvio del container Nginx..."

NGINX_ENV="${NGINX_ENV:-prod}"
DOMAIN="${DOMAIN}"
LETSENCRYPT_EMAIL="${LETSENCRYPT_EMAIL}"
echo "[nginx-entrypoint] Modalità configurata: ${NGINX_ENV}"
echo "[nginx-entrypoint] Variabili d'ambiente:"
echo "  - NGINX_ENV: ${NGINX_ENV}"
echo "  - DOMAIN: ${DOMAIN}"
echo "  - LETSENCRYPT_EMAIL: ${LETSENCRYPT_EMAIL}"
echo "[nginx-entrypoint] Profili Docker Compose attivi:"
echo "  - Servizi disponibili: $(docker-compose config --services 2>/dev/null || echo 'N/A')"
echo "  - Container in esecuzione: $(docker ps --format 'table {{.Names}}' --filter 'name=cercollettiva' 2>/dev/null || echo 'N/A')"

generate_self_signed() {
  if [ ! -f "/etc/nginx/ssl/cert.pem" ]; then
    echo "[nginx-entrypoint] Nessun certificato self-signed esistente. Creazione..."
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
      -keyout /etc/nginx/ssl/key.pem \
      -out /etc/nginx/ssl/cert.pem \
      -subj "/C=IT/ST=Italy/L=Local/O=CerCollettiva/OU=Staging/CN=localhost"
    echo "[nginx-entrypoint] ✓ Certificati self-signed creati."
  else
    echo "[nginx-entrypoint] ✓ Certificati self-signed già esistenti."
  fi
}

get_letsencrypt_certs() {
  if [ -z "$DOMAIN" ] || [ -z "$LETSENCRYPT_EMAIL" ]; then
    echo "[nginx-entrypoint] ERRORE: Variabili DOMAIN e LETSENCRYPT_EMAIL non configurate per la modalità prod."
    exit 1
  fi

  if [ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
    echo "[nginx-entrypoint] ✓ Certificati Let's Encrypt per $DOMAIN già esistenti."
  else
    echo "[nginx-entrypoint] Generazione on-demand certificati Let's Encrypt per $DOMAIN..."
    # Usa configurazione bootstrap solo per ACME challenge
    ln -sf /etc/nginx/conf.d/cercollettiva-bootstrap.conf /etc/nginx/sites-enabled/app.conf
    nginx -s reload

    # Genera certificato on-demand con webroot
    certbot certonly --webroot -w /var/www/certbot \
      --email "$LETSENCRYPT_EMAIL" \
      -d "$DOMAIN" \
      --agree-tos \
      --non-interactive \
      --force-renewal

    echo "[nginx-entrypoint] ✓ Certificati Let's Encrypt generati on-demand."
  fi
  # Passa alla configurazione produzione
  ln -sf /etc/nginx/conf.d/cercollettiva-prod.conf /etc/nginx/sites-enabled/app.conf
}

setup_cert_renewal() {
  if [ "$NGINX_ENV" = "prod" ]; then
    echo "0 12 * * * certbot renew --quiet" | crontab -
    echo "[nginx-entrypoint] Configurato rinnovo automatico Certbot."
  fi
}

mkdir -p /etc/nginx/sites-enabled /var/www/certbot /etc/nginx/ssl
rm -f /etc/nginx/sites-enabled/*.conf 2>/dev/null || true

# Auto-rilevamento della modalità basato sui servizi disponibili
if [ -n "$NGINX_ENV" ]; then
  # Modalità esplicita se NGINX_ENV è impostata
  case "$NGINX_ENV" in
    dev)
      export NGINX_UPSTREAM_HOST="web-dev"
      ln -sf /etc/nginx/conf.d/cercollettiva-dev.conf /etc/nginx/sites-enabled/app.conf
      echo "[nginx-entrypoint] Modalità sviluppo (HTTP) - esplicita."
      ;;
    staging)
      export NGINX_UPSTREAM_HOST="web"
      generate_self_signed
      ln -sf /etc/nginx/conf.d/cercollettiva-staging.conf /etc/nginx/sites-enabled/app.conf
      echo "[nginx-entrypoint] Modalità staging (HTTPS Self-Signed) - esplicita."
      ;;
    prod)
      export NGINX_UPSTREAM_HOST="web"
      get_letsencrypt_certs
      setup_cert_renewal
      echo "[nginx-entrypoint] Modalità produzione (HTTPS Let's Encrypt) - esplicita."
      ;;
    *)
      echo "[nginx-entrypoint] ERRORE: NGINX_ENV non valido. Usa 'dev', 'staging' o 'prod'."
      exit 1
      ;;
  esac
else
  # Auto-rilevamento basato sui servizi disponibili
  echo "[nginx-entrypoint] Auto-rilevamento modalità..."
  
  # Verifica se web-dev è disponibile (modalità dev)
  if nslookup web-dev >/dev/null 2>&1; then
    export NGINX_UPSTREAM_HOST="web-dev"
    ln -sf /etc/nginx/conf.d/cercollettiva-dev.conf /etc/nginx/sites-enabled/app.conf
    echo "[nginx-entrypoint] Modalità sviluppo (HTTP) - auto-rilevata."
  # Verifica se web è disponibile e se ci sono certificati Let's Encrypt (modalità prod)
  elif [ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ] && [ -n "$DOMAIN" ]; then
    export NGINX_UPSTREAM_HOST="web"
    ln -sf /etc/nginx/conf.d/cercollettiva-prod.conf /etc/nginx/sites-enabled/app.conf
    echo "[nginx-entrypoint] Modalità produzione (HTTPS Let's Encrypt) - auto-rilevata."
  # Default: modalità staging
  else
    export NGINX_UPSTREAM_HOST="web"
    generate_self_signed
    ln -sf /etc/nginx/conf.d/cercollettiva-staging.conf /etc/nginx/sites-enabled/app.conf
    echo "[nginx-entrypoint] Modalità staging (HTTPS Self-Signed) - auto-rilevata."
  fi
fi

# Crea il file nginx.conf con il nome corretto del servizio
echo "[nginx-entrypoint] Creazione configurazione nginx per upstream '$NGINX_UPSTREAM_HOST'"
cat > /etc/nginx/nginx.conf << EOF
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log notice;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging
    log_format main '\$remote_addr - \$remote_user [\$time_local] "\$request" '
                    '\$status \$body_bytes_sent "\$http_referer" '
                    '"\$http_user_agent" "\$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    # Performance
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 50M;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Rate limiting
    limit_req_zone \$binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone \$binary_remote_addr zone=login:10m rate=5r/m;

    # Upstream Django
    upstream django {
        server $NGINX_UPSTREAM_HOST:8000;
    }

    # Include only active site configuration (set by entrypoint)
    include /etc/nginx/sites-enabled/*.conf;
}
EOF

echo "[nginx-entrypoint] Configurazione nginx creata con upstream: $NGINX_UPSTREAM_HOST"

exec nginx -g 'daemon off;'


