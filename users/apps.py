# users/apps.py
from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "users"
    verbose_name = "Utenti"

    def ready(self):
        """
        Importa e registra i signals quando l'applicazione viene caricata.
        """
        import users.signals  # noqa: F401
