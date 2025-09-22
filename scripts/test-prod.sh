#!/bin/bash
# Script per testare la modalità produzione

echo "🚀 Avvio modalità PRODUZIONE..."
echo "📋 Configurazione:"
echo "   - HTTPS con certificati Let's Encrypt"
echo "   - CSP con massima sicurezza"
echo "   - Security headers completi"
echo "   - Rate limiting e monitoring"
echo ""

# Verifica variabili d'ambiente richieste
if [ -z "$DOMAIN" ]; then
    echo "❌ ERRORE: Variabile DOMAIN non impostata"
    echo "💡 Esempio: export DOMAIN=example.com"
    exit 1
fi

if [ -z "$LETSENCRYPT_EMAIL" ]; then
    echo "❌ ERRORE: Variabile LETSENCRYPT_EMAIL non impostata"
    echo "💡 Esempio: export LETSENCRYPT_EMAIL=admin@example.com"
    exit 1
fi

# Imposta variabili d'ambiente per produzione
export NGINX_ENV=prod
export DEPLOYMENT_MODE=production

echo "🔧 Configurazione:"
echo "   - Dominio: $DOMAIN"
echo "   - Email Let's Encrypt: $LETSENCRYPT_EMAIL"
echo ""

# Avvia i servizi
echo "🔧 Avvio servizi produzione..."
docker-compose --profile prod up -d

echo ""
echo "✅ Modalità produzione avviata!"
echo "🌐 Accesso: https://$DOMAIN"
echo "📊 Monitoraggio: https://$DOMAIN:3000 (Grafana)"
echo ""
echo "📝 Per fermare: docker-compose --profile prod down"
echo "📝 Per logs: docker-compose --profile prod logs -f"
echo "📝 Per rinnovare certificati: docker-compose --profile prod exec nginx certbot renew"
