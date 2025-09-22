#!/bin/bash
# Script per testare la modalità staging

echo "🚀 Avvio modalità STAGING..."
echo "📋 Configurazione:"
echo "   - HTTPS con certificati self-signed"
echo "   - CSP con upgrade-insecure-requests"
echo "   - Security headers ottimizzati"
echo "   - Rate limiting abilitato"
echo ""

# Imposta variabili d'ambiente per staging
export NGINX_ENV=staging
export DEPLOYMENT_MODE=staging

# Avvia i servizi
echo "🔧 Avvio servizi staging..."
docker-compose --profile staging up -d

echo ""
echo "✅ Modalità staging avviata!"
echo "🌐 Accesso: https://localhost (accetta certificato self-signed)"
echo "📊 Monitoraggio: http://localhost:3000 (Grafana)"
echo ""
echo "📝 Per fermare: docker-compose --profile staging down"
echo "📝 Per logs: docker-compose --profile staging logs -f"
