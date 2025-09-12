# monitoring/apps.py
from django.apps import AppConfig


class MonitoringConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'monitoring'
    verbose_name = 'Monitoring'
    
    def ready(self):
        """Inizializzazione app monitoring"""
        pass
