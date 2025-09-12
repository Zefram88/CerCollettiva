# core/signals/audit.py
import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from ..models.audit import CERDocumentAudit, EconomicTransactionAudit, UserActionAudit
from ..models.economic import EconomicTransaction

logger = logging.getLogger(__name__)
User = get_user_model()


# Audit per transazioni economiche
@receiver(post_save, sender=EconomicTransaction)
def log_economic_transaction_changes(sender, instance, created, **kwargs):
    """Logga modifiche alle transazioni economiche"""
    if created:
        operation_type = "CREATE"
        old_values = None
        new_values = {
            "id": str(instance.id),
            "transaction_number": instance.transaction_number,
            "transaction_type": instance.transaction_type,
            "amount": float(instance.amount),
            "status": instance.status,
        }
    else:
        operation_type = "UPDATE"
        # Per semplicità, logghiamo solo i campi principali
        old_values = (
            None  # In un'implementazione completa, salveremmo i valori precedenti
        )
        new_values = {
            "id": str(instance.id),
            "transaction_number": instance.transaction_number,
            "status": instance.status,
            "amount": float(instance.amount),
        }

    try:
        EconomicTransactionAudit.log_transaction_operation(
            transaction=instance,
            operation_type=operation_type,
            user=instance.user,
            old_values=old_values,
            new_values=new_values,
            reason=f"Operazione automatica: {operation_type}",
        )
    except Exception as e:
        logger.error(f"Errore nel logging audit transazione {instance.id}: {e}")


@receiver(post_delete, sender=EconomicTransaction)
def log_economic_transaction_deletion(sender, instance, **kwargs):
    """Logga eliminazione transazioni economiche"""
    try:
        EconomicTransactionAudit.log_transaction_operation(
            transaction=None,
            operation_type="DELETE",
            user=None,  # Non abbiamo accesso all'utente in post_delete
            old_values={
                "id": str(instance.id),
                "transaction_number": instance.transaction_number,
                "transaction_type": instance.transaction_type,
                "amount": float(instance.amount),
            },
            new_values=None,
            reason="Eliminazione transazione",
        )
    except Exception as e:
        logger.error(
            f"Errore nel logging audit eliminazione transazione {instance.id}: {e}"
        )


# Audit per azioni utente
@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Logga login utente"""
    try:
        UserActionAudit.objects.create(
            user=user,
            action_type="LOGIN",
            description=f"Login utente {user.email}",
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            session_id=request.session.session_key or "",
        )
    except Exception as e:
        logger.error(f"Errore nel logging login utente {user.id}: {e}")


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """Logga logout utente"""
    try:
        UserActionAudit.objects.create(
            user=user,
            action_type="LOGOUT",
            description=f"Logout utente {user.email}",
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            session_id=request.session.session_key or "",
        )
    except Exception as e:
        logger.error(f"Errore nel logging logout utente {user.id}: {e}")


# Audit per documenti CER (da implementare quando i modelli saranno pronti)
def log_cer_document_operation(
    cer_configuration, document_type, operation_type, user, document_name="", reason=""
):
    """Helper per loggare operazioni su documenti CER"""
    try:
        CERDocumentAudit.objects.create(
            cer_configuration=cer_configuration,
            document_type=document_type,
            operation_type=operation_type,
            user=user,
            document_name=document_name,
            reason=reason,
        )
    except Exception as e:
        logger.error(f"Errore nel logging audit documento CER: {e}")


# Funzione per pulizia automatica audit logs scaduti
def cleanup_expired_audit_logs():
    """Pulisce i log di audit scaduti"""
    try:
        now = timezone.now()

        # Pulisce audit transazioni economiche (2 anni)
        expired_economic = EconomicTransactionAudit.objects.filter(
            retention_date__lt=now
        )
        economic_count = expired_economic.count()
        expired_economic.delete()

        # Pulisce audit documenti CER (3 anni)
        expired_docs = CERDocumentAudit.objects.filter(retention_date__lt=now)
        docs_count = expired_docs.count()
        expired_docs.delete()

        # Pulisce audit azioni utente (1 anno)
        expired_actions = UserActionAudit.objects.filter(retention_date__lt=now)
        actions_count = expired_actions.count()
        expired_actions.delete()

        logger.info(
            f"Pulizia audit logs completata: {economic_count} economic, {docs_count} docs, {actions_count} actions"
        )

    except Exception as e:
        logger.error(f"Errore nella pulizia audit logs: {e}")
