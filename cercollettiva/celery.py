# cercollettiva/celery.py

import os
from celery import Celery

# Imposta il modulo Django predefinito per il comando 'celery'.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cercollettiva.settings.local')

app = Celery('cercollettiva')

# Usa una stringa di configurazione Django per il namespace='CELERY'
app.config_from_object('django.conf:settings', namespace='CELERY')

# Carica automaticamente i task da tutte le app Django registrate.
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
