#!/bin/bash
cd /home/atomozero/CerCollettiva/app
source /home/atomozero/CerCollettiva/venv/bin/activate
export DJANGO_SETTINGS_MODULE=cercollettiva.settings.local
/home/atomozero/CerCollettiva/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 cercollettiva.wsgi:application
