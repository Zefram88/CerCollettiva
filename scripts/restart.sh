#!/bin/bash
echo "Riavvio CerCollettiva..."
# Riavvia Gunicorn
sudo supervisorctl restart gunicorn
# Riavvia il client MQTT
sudo supervisorctl restart cercollettiva_mqtt
echo "CerCollettiva riavviato!"
