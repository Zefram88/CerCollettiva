#!/bin/bash
cd /home/atomozero/CerCollettiva/app
source /home/atomozero/CerCollettiva/venv/bin/activate
export DJANGO_SETTINGS_MODULE=cercollettiva.settings.dev
python manage.py runserver 0.0.0.0:8000
