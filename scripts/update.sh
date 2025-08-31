#!/usr/bin/env bash

set -euo pipefail

echo "Aggiornamento CerCollettiva..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="${SCRIPT_DIR}/.."
cd "$ROOT_DIR"

# Attiva ambiente virtuale, se presente
if [ -f "venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source "venv/bin/activate"
fi

# Pull nuovi cambiamenti (assumendo git)
if command -v git >/dev/null 2>&1; then
  git pull --ff-only || true
fi

# Installa nuove dipendenze se requirements.txt presente
if [ -f "requirements.txt" ]; then
  pip install -r requirements.txt
fi

# Applica migrazioni e raccoglie statici
python manage.py migrate
python manage.py collectstatic --noinput

# Riavvia l'applicazione se disponibile uno script di restart
if [ -x "${SCRIPT_DIR}/restart.sh" ]; then
  "${SCRIPT_DIR}/restart.sh"
else
  echo "Nessuno script di restart trovato; riavvia manualmente se necessario."
fi

echo "CerCollettiva aggiornato!"
