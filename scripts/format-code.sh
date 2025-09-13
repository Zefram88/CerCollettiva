#!/bin/bash

# Script per formattare il codice con Black prima del push
# Uso: ./scripts/format-code.sh

echo "🎨 Formattazione codice con Black..."

# Controlla se Black è installato
if ! command -v black &> /dev/null; then
    echo "❌ Black non trovato. Installazione..."
    pip install black
fi

# Formatta tutti i file Python escludendo le directory specificate
echo "📝 Formattazione file Python..."
black . --exclude "venv|node_modules|tests|cercollettiva/settings"

# Controlla se ci sono modifiche
if git diff --quiet; then
    echo "✅ Tutti i file sono già formattati correttamente!"
else
    echo "📝 File formattati. Modifiche:"
    git diff --name-only
    echo ""
    echo "💡 Ricorda di fare commit delle modifiche:"
    echo "   git add ."
    echo "   git commit -m 'style: Format code with Black'"
    echo "   git push"
fi

echo "🎉 Formattazione completata!"
