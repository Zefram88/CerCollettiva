# cer/signals.py
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import MemberProfile

User = get_user_model()


@receiver(post_save, sender=User)
def create_member_profile(sender, instance, created, **kwargs):
    """
    Crea automaticamente un MemberProfile quando viene creato un nuovo utente
    """
    if created:
        try:
            MemberProfile.objects.create(user=instance)
        except Exception:
            # Se il profilo esiste già, non fare nulla
            pass


# @receiver(post_save, sender=User)
# def save_member_profile(sender, instance, **kwargs):
#     """
#     Salva il MemberProfile quando viene salvato l'utente
#     """
#     if hasattr(instance, 'member_profile'):
#         instance.member_profile.save()
