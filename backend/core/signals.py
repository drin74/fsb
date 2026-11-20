from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver

from .models import AuditLog
from .services import log_action


@receiver(user_logged_in)
def on_login(sender, request, user, **kwargs):
    log_action(request, AuditLog.Action.LOGIN, user, model_name="User")


@receiver(user_logged_out)
def on_logout(sender, request, user, **kwargs):
    if user:
        log_action(request, AuditLog.Action.LOGOUT, user, model_name="User")
