from django.contrib.auth.models import User
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.db.models.signals import post_save

from .models import AuditLog, UserProfile
from .utils import get_client_ip


@receiver(user_logged_in)
def audit_login(sender, request, user, **kwargs):
    AuditLog.objects.create(
        actor=user,
        action="LOGIN",
        target_type="UserSession",
        target_id=str(user.pk),
        ip_address=get_client_ip(request),
        metadata={"username": user.username},
    )


@receiver(user_logged_out)
def audit_logout(sender, request, user, **kwargs):
    if not user:
        return
    AuditLog.objects.create(
        actor=user,
        action="LOGOUT",
        target_type="UserSession",
        target_id=str(user.pk),
        ip_address=get_client_ip(request),
        metadata={"username": user.username},
    )


@receiver(user_logged_in)
def ensure_profile(sender, request, user, **kwargs):
    UserProfile.objects.get_or_create(user=user)


@receiver(post_save, sender=User)
def create_profile_on_signup(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)
