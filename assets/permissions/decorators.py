"""
Permission decorators and mixins for admin-only operations.
"""
from functools import wraps
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden


class AdminRequiredMixin:
    """Mixin for class-based views requiring admin access."""
    
    def dispatch(self, request, *args, **kwargs):
        """Check if user is admin before allowing access."""
        if not request.user.is_staff:
            raise PermissionDenied("Admin access required")
        return super().dispatch(request, *args, **kwargs)


def admin_required(view_func):
    """Decorator for function-based views requiring admin access."""
    
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            return HttpResponseForbidden("Admin access required")
        return view_func(request, *args, **kwargs)
    
    return wrapper
