#!/bin/bash
echo "Mostra ultimi log di CerCollettiva..."
echo "=== LOG DJANGO ==="
tail -n 50 /home/atomozero/CerCollettiva/logs/django.log
echo "=== LOG GUNICORN ==="
tail -n 50 /home/atomozero/CerCollettiva/logs/gunicorn.log
echo "=== LOG MQTT ==="
tail -n 50 /home/atomozero/CerCollettiva/logs/mqtt.log
