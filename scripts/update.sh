#!/bin/bash
echo "Aggiornamento CerCollettiva..."
cd /home/atomozero/CerCollettiva/app
# Attiva ambiente virtuale
source /home/atomozero/CerCollettiva/venv/bin/activate
# Pull nuovi cambiamenti (assumendo git)
git pull
# Installa nuove dipendenze
pip install -r requirements.txt
# Applica migrazioni
python manage.py migrate
# Raccolta file statici
python manage.py collectstatic --noinput
# Riavvia l'applicazione
/home/atomozero/CerCollettiva/restart.sh
echo "CerCollettiva aggiornato!"
