from django.apps import AppConfig


class CerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cer'
    verbose_name = 'Comunità Energetica Rinnovabile'
    
    def ready(self):
        """Configurazione app quando è pronta"""
        import cer.signals  # Importa i signal handlers
