#!/usr/bin/env bash

# Sanity check e migrazioni (Unix)
set -euo pipefail

# Porta la working directory alla root del progetto (cartella che contiene manage.py)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}/.."

# Attiva virtualenv se presente
if [ -f "venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source "venv/bin/activate"
fi

# Imposta settings di default se non presenti
export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-cercollettiva.settings.local}"
echo "DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE"

python manage.py check
python manage.py migrate --noinput

echo "Check e migrazioni completati."

