#!/bin/sh
set -e

echo "[nginx-entrypoint] Starting..."

NGINX_ENV="${NGINX_ENV:-prod}"
DOMAIN="${DOMAIN}"
LETSENCRYPT_EMAIL="${LETSENCRYPT_EMAIL}"
echo "[nginx-entrypoint] NGINX_ENV=${NGINX_ENV}"

# Crea directory necessarie
mkdir -p /etc/nginx/sites-enabled /var/www/certbot /etc/nginx/ssl
rm -f /etc/nginx/sites-enabled/*.conf 2>/dev/null || true

# PRIMA: Genera certificati se necessario (prima di configurare nginx)
if [ "$NGINX_ENV" != "dev" ]; then
  # Modalità produzione: sempre genera certificati PRIMA
  if [ -n "$DOMAIN" ] && [ -n "$LETSENCRYPT_EMAIL" ]; then
    echo "[nginx-entrypoint] Domini reali configurati - gestione certificati disponibile"
    # TODO: Implementare gestione certificati automatica se necessario
  else
    echo "[nginx-entrypoint] Localhost: creazione certificati self-signed..."
    # Genera certificati self-signed per localhost
    if [ ! -f "/etc/nginx/ssl/cert.pem" ]; then
      openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout /etc/nginx/ssl/key.pem \
        -out /etc/nginx/ssl/cert.pem \
        -subj "/C=IT/ST=Italy/L=Local/O=CerCollettiva/OU=Dev/CN=localhost"
      echo "[nginx-entrypoint] ✓ Certificati self-signed creati"
    else
      echo "[nginx-entrypoint] ✓ Certificati self-signed già esistenti"
    fi
  fi
fi

# DOPO: Selezione configurazione basata su ambiente
if [ "$NGINX_ENV" = "dev" ]; then
  # Modalità sviluppo: HTTP only
  ln -sf /etc/nginx/conf.d/cercollettiva-dev.conf /etc/nginx/sites-enabled/app.conf
  echo "[nginx-entrypoint] Modalità sviluppo (HTTP)"
else
  # Modalità produzione: HTTPS
  ln -sf /etc/nginx/conf.d/cercollettiva-prod.conf /etc/nginx/sites-enabled/app.conf
  echo "[nginx-entrypoint] Modalità produzione (HTTPS)"
fi

# Avvia nginx
exec nginx -g 'daemon off;'


