from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied

from .models import QueueStaff


def get_queue_role(user):
    """
    نقش کاربر در ماژول نوبت‌دهی را برمی‌گرداند؛ None یعنی بدون دسترسی.
    - سوپریوزر: همیشه نقش مدیریت
    - نقش مدیریت در سیستم اصلی: نقش مدیریت در نوبت‌دهی
    - نقش کارمند در سیستم اصلی: نقش کارمند در نوبت‌دهی
    - نقش QueueStaff: طبق سیستم نوبت‌دهی
    """
    if not user or not user.is_authenticated:
        return None
    
    # بررسی نقش‌های استاندارد سیستم
    user_role = getattr(user, 'role', None)
    if user.is_superuser or user_role == 'admin':
        return QueueStaff.Role.MANAGER
    if user_role == 'manager':
        return QueueStaff.Role.MANAGER
    if user_role == 'employee':
        return QueueStaff.Role.STAFF
    
    # بررسی سیستم QueueStaff
    staff = getattr(user, "queue_staff", None)
    if staff is None:
        return None
    if staff.role == QueueStaff.Role.MANAGER:
        return QueueStaff.Role.MANAGER
    if staff.role == QueueStaff.Role.STAFF and staff.approved:
        return QueueStaff.Role.STAFF
    return None


def panel_required(roles=(QueueStaff.Role.STAFF, QueueStaff.Role.MANAGER)):
    """دکوراتور دسترسی پنل؛ کاربران بدون نقش به صفحه ورود/خطای 403 می‌روند."""

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            role = get_queue_role(request.user)
            if role is None:
                if not request.user.is_authenticated:
                    return redirect_to_login(request.get_full_path())
                raise PermissionDenied("دسترسی به پنل نوبت‌دهی ندارید.")
            if role not in roles:
                raise PermissionDenied("برای این بخش نیاز به نقش مدیریت است.")
            request.queue_role = role
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


manager_required = panel_required(roles=(QueueStaff.Role.MANAGER,))
