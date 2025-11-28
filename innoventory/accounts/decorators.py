from functools import wraps
from django.core.exceptions import PermissionDenied

def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != "admin":
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper
