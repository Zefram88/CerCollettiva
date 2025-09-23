# users/signals.py
import logging
import os
import tempfile

from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

# Rileva ambiente di esecuzione (stessa logica di local.py)
def detect_environment():
    """Rileva se siamo in WSL, Docker, o filesystem normale"""
    # Docker: controlla se siamo in container
    if os.path.exists("/.dockerenv") or os.environ.get("DEPLOYMENT_MODE"):
        return "docker"
    
    # WSL: controlla se siamo su WSL
    if os.path.exists("/proc/version"):
        try:
            with open("/proc/version", "r") as f:
                if "microsoft" in f.read().lower():
                    return "wsl"
        except:
            pass
    
    # Filesystem normale
    return "normal"

# Configurazione del logger
logger = logging.getLogger("access_logger")
logger.setLevel(logging.INFO)

# Determina il percorso del file di log in base all'ambiente
env_type = detect_environment()

if env_type == "docker":
    # Docker: usa directory del progetto
    log_file = "access_logs.log"
elif env_type == "wsl":
    # WSL: usa directory temporanea Linux
    log_file = os.path.join(tempfile.gettempdir(), "access_logs.log")
else:
    # Filesystem normale: usa directory corrente
    log_file = "access_logs.log"

# Handler per file
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.INFO)

# Handler per console (utile in development)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Formato del log
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """
    Registra i tentativi di login riusciti
    """
    ip_address = request.META.get("REMOTE_ADDR", "unknown")
    user_agent = request.META.get("HTTP_USER_AGENT", "unknown")

    logger.info(
        f"Login riuscito - Utente: {user.username} - "
        f"IP: {ip_address} - "
        f"User Agent: {user_agent} - "
        f"Timestamp: {timezone.now()}"
    )


@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request, **kwargs):
    """
    Registra i tentativi di login falliti
    """
    # Gestisce il caso in cui request è None (es. nei test)
    if request is None:
        ip_address = "unknown"
        user_agent = "unknown"
    else:
        ip_address = request.META.get("REMOTE_ADDR", "unknown")
        user_agent = request.META.get("HTTP_USER_AGENT", "unknown")

    # Rimuoviamo la password dalle credenziali per sicurezza
    safe_credentials = credentials.copy()
    if "password" in safe_credentials:
        del safe_credentials["password"]

    logger.warning(
        f"Tentativo di login fallito - Credenziali: {safe_credentials} - "
        f"IP: {ip_address} - "
        f"User Agent: {user_agent} - "
        f"Timestamp: {timezone.now()}"
    )


@receiver(post_save, sender=get_user_model())
def log_user_registration(sender, instance, created, **kwargs):
    """
    Registra le nuove registrazioni utente
    """
    if created:
        logger.info(
            f"Nuovo utente registrato - Username: {instance.username} - "
            f"Email: {instance.email} - "
            f"Tipo: {getattr(instance, 'legal_type', 'N/A')} - "
            f"Timestamp: {timezone.now()}"
        )
