from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse

# لیست نقش‌های استاندارد سیستم
ROLE_ADMIN = 'admin'
ROLE_MANAGER = 'manager'
ROLE_STAFF = 'staff'
# ROLE_SUPPORT = 'support'
# ROLE_DRIVER = 'driver'

# STANDARD_ROLES = [ROLE_ADMIN, ROLE_MANAGER, ROLE_SUPPORT, ROLE_DRIVER]
STANDARD_ROLES = [ROLE_ADMIN, ROLE_MANAGER, ROLE_STAFF]


def role_required(allowed_roles=None, redirect_url='forbidden'):
    """
    Decorator برای محدود کردن دسترسی کاربران بر اساس نقش (Role)

    استفاده:
    @role_required([ROLE_ADMIN])
    @role_required([ROLE_MANAGER, ROLE_ADMIN])
    """

    if allowed_roles is None:
        allowed_roles = []

    # اعتبارسنجی اولیه: مطمئن شو allowed_roles فقط شامل نقش‌های استاندارد باشه
    for role in allowed_roles:
        if role not in STANDARD_ROLES:
            raise ValueError(f"نقش '{role}' در نقش‌های استاندارد تعریف نشده است!")

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user = request.user

            # 🔹 اگر کاربر وارد نشده بود:
            if not user.is_authenticated:
                messages.warning(request, "برای مشاهده این صفحه ابتدا وارد شوید.")
                return redirect(reverse('login'))

            # 🔹 بررسی نقش کاربر
            user_role = getattr(user, 'role', None)
            if user_role not in allowed_roles:
                # نقش مجاز نیست
                messages.error(request, "شما به این بخش دسترسی ندارید.")
                return redirect(reverse(redirect_url))  # صفحه 403 یا صفحه اصلی
                # یا می‌تونی بنویسی:
                # return HttpResponseForbidden("دسترسی غیرمجاز")

            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator
