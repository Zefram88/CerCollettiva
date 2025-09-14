#!/bin/bash

# Script per formattare il codice con Black prima del push
# Uso: ./scripts/format-code.sh

echo "🎨 Formattazione codice con Black..."

# Controlla se Black e isort sono installati
if ! command -v black &> /dev/null; then
    echo "❌ Black non trovato. Installazione..."
    pip install black
fi

if ! command -v isort &> /dev/null; then
    echo "❌ isort non trovato. Installazione..."
    pip install isort
fi

# Ordina gli import con isort
echo "📝 Ordinamento import con isort..."
isort . --profile black

# Formatta tutti i file Python escludendo le directory specificate
echo "📝 Formattazione file Python con Black..."
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
