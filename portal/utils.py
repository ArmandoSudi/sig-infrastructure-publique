from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect

from .models import AuditLog, UserProfile


def get_user_role(user):
    if not user or not user.is_authenticated:
        return UserProfile.Role.PUBLIC_READER
    if user.is_superuser:
        return UserProfile.Role.NATIONAL_ADMIN
    profile = getattr(user, "profile", None)
    if profile:
        return profile.role
    return UserProfile.Role.PUBLIC_READER


def role_required(*allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect("portal:login")
            role = get_user_role(request.user)
            if role not in allowed_roles and not request.user.is_superuser:
                messages.error(request, "Acces refuse pour ce role.")
                return redirect("portal:home")
            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator


def log_action(request, action, target_type, target_id="", metadata=None):
    AuditLog.objects.create(
        actor=request.user if request.user.is_authenticated else None,
        action=action,
        target_type=target_type,
        target_id=str(target_id or ""),
        metadata=metadata or {},
        ip_address=get_client_ip(request),
    )


def get_client_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")
