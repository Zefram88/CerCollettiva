#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="${SCRIPT_DIR}/.."
LOG_DIR="${ROOT_DIR}/logs"

LINES=${1:-50}

echo "Mostra ultimi log di CerCollettiva..."
echo "=== LOG APPLICAZIONE (cercollettiva.log) ==="
tail -n "$LINES" "$LOG_DIR/cercollettiva.log" || echo "(manca $LOG_DIR/cercollettiva.log)"
echo "=== LOG MQTT (mqtt.log) ==="
tail -n "$LINES" "$LOG_DIR/mqtt.log" || echo "(manca $LOG_DIR/mqtt.log)"
