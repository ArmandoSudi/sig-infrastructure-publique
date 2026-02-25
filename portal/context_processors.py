from .utils import get_user_role


def navigation_context(request):
    return {
        "current_role": get_user_role(getattr(request, "user", None)),
    }
