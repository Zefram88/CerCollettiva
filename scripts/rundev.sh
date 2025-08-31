#!/usr/bin/env bash

# Robust dev server launcher for Unix-like systems
# - Works relative to repo
# - Activates local venv if present
# - Allows --bind and --port args

set -euo pipefail

# Move to repo root (parent of this script dir)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}/.."

# Activate virtualenv if available
if [ -f "venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source "venv/bin/activate"
fi

# Default settings module (overridable from environment)
export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-cercollettiva.settings.local}"
echo "DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE"

# Defaults
BIND="0.0.0.0"
PORT="8000"

# Parse simple flags: --bind <addr>, --port <num>
while [ $# -gt 0 ]; do
  case "$1" in
    --bind)
      BIND="$2"; shift 2 ;;
    --port)
      PORT="$2"; shift 2 ;;
    *)
      echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
done

ENDPOINT="${BIND}:${PORT}"
echo "Starting Django dev server at ${ENDPOINT}"
exec python manage.py runserver "${ENDPOINT}"
