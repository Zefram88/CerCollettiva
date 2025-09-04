# users/signals.py
import logging
from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.conf import settings

# Configurazione del logger
logger = logging.getLogger('access_logger')
logger.setLevel(logging.INFO)

# Handler per file
file_handler = logging.FileHandler('access_logs.log')
file_handler.setLevel(logging.INFO)

# Handler per console (utile in development)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Formato del log
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """
    Registra i tentativi di login riusciti
    """
    ip_address = request.META.get('REMOTE_ADDR', 'unknown')
    user_agent = request.META.get('HTTP_USER_AGENT', 'unknown')
    
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
        ip_address = 'unknown'
        user_agent = 'unknown'
    else:
        ip_address = request.META.get('REMOTE_ADDR', 'unknown')
        user_agent = request.META.get('HTTP_USER_AGENT', 'unknown')
    
    # Rimuoviamo la password dalle credenziali per sicurezza
    safe_credentials = credentials.copy()
    if 'password' in safe_credentials:
        del safe_credentials['password']
    
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