from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from .models import RolePermission

# لیست نقش‌های استاندارد سیستم
ROLE_ADMIN = 'admin'
ROLE_MANAGER = 'manager'
ROLE_EMPLOYEE = 'employee'
ROLE_DRIVER = 'driver'
ROLE_CUSTOMER = 'customer'

STANDARD_ROLES = [ROLE_ADMIN, ROLE_MANAGER, ROLE_EMPLOYEE, ROLE_DRIVER, ROLE_CUSTOMER]


def get_user_permissions(user):
    """دریافت مجوزهای کاربر بر اساس نقش مؤثر.

    نقش‌های سفارشی (تعریف‌شده در ماژول کنترل سیستم) از نقش پایه خود
    مجوز ارث می‌برند.
    """
    if not user.is_authenticated:
        return None
    
    try:
        user_role = resolve_effective_role(getattr(user, 'role', None))
        if not user_role:
            return None
        return RolePermission.objects.filter(role=user_role).first()
    except:
        return None


def has_permission(user, permission_field):
    """بررسی اینکه آیا کاربر مجوز خاصی دارد یا خیر"""
    if not user.is_authenticated:
        return False
    
    # مدیر کل سیستم به همه چیز دسترسی دارد
    user_role = getattr(user, 'role', None)
    if user.is_superuser or user_role == ROLE_ADMIN:
        return True
    
    # نقش «مدیریت» برای مجوزهای چاپ بارنامه همیشه مجاز است
    # (این دو مجوز طبق طراحی فقط برای نقش کارمند قابل تنظیم‌اند)
    if resolve_effective_role(user_role) == ROLE_MANAGER and permission_field in (
            'can_print_without_approval', 'can_use_digital_stamp'):
        return True
    
    permissions = get_user_permissions(user)
    if not permissions:
        return False
    
    return getattr(permissions, permission_field, False)


def resolve_effective_role(role_code):
    """برگرداندن نقش مؤثر کاربر.

    برای نقش‌های سفارشی (تعریف‌شده در ماژول کنترل سیستم)، نقش پایه
    برگردانده می‌شود تا نقش سفارشی از سطح دسترسی نقش پایه ارث ببرد.
    """
    if role_code in STANDARD_ROLES:
        return role_code
    try:
        from system_control.models import Role
        custom = Role.objects.filter(code=role_code, is_active=True).first()
        if custom:
            return custom.base_role
    except Exception:
        pass
    return role_code


def can_use_digital_stamp(user):
    """بررسی مجوز استفاده از مهر و امضای دیجیتال در چاپ بارنامه‌ها.

    قوانین:
    - مدیر کل (admin) و ابرکاربر: همیشه مجاز
    - مدیریت (manager): همیشه مجاز
    - کارمند (employee): فقط در صورت فعال بودن مجوز «can_use_digital_stamp»
      در نقش کارمند توسط مدیریت/ادمین
    - سایر نقش‌ها (راننده، مشتری، مهمان): غیرمجاز

    نقش‌های سفارشی از نقش پایه خود ارث می‌برند.
    """
    if not getattr(user, 'is_authenticated', False):
        return False

    if user.is_superuser:
        return True

    effective_role = resolve_effective_role(getattr(user, 'role', None))

    if effective_role in (ROLE_ADMIN, ROLE_MANAGER):
        return True

    if effective_role == ROLE_EMPLOYEE:
        return has_permission(user, 'can_use_digital_stamp')

    return False


def is_manager_or_admin(user):
    """بررسی اینکه آیا کاربر «مدیریت» یا «مدیر کل» است.

    ابرکاربر (superuser) و نقش‌های سفارشی مبتنی بر نقش مدیریت/مدیر کل
    نیز شامل می‌شوند.
    """
    if not getattr(user, 'is_authenticated', False):
        return False
    if user.is_superuser:
        return True
    effective_role = resolve_effective_role(getattr(user, 'role', None))
    return effective_role in (ROLE_ADMIN, ROLE_MANAGER)


def can_print_without_approval(user):
    """بررسی مجوز چاپ بارنامه بدون نیاز به تأیید مدیریت.

    قوانین:
    - مدیر کل (admin) و ابرکاربر: همیشه مجاز
    - مدیریت (manager): همیشه مجاز
    - کارمند (employee): فقط در صورت فعال بودن مجوز «can_print_without_approval»
      در نقش کارمند توسط مدیریت/ادمین
    - سایر نقش‌ها (راننده، مشتری، مهمان): غیرمجاز

    نقش‌های سفارشی از نقش پایه خود ارث می‌برند.
    """
    if not getattr(user, 'is_authenticated', False):
        return False

    if user.is_superuser:
        return True

    effective_role = resolve_effective_role(getattr(user, 'role', None))

    if effective_role in (ROLE_ADMIN, ROLE_MANAGER):
        return True

    if effective_role == ROLE_EMPLOYEE:
        return has_permission(user, 'can_print_without_approval')

    return False


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
            # نقش سفارشی از نقش پایه خود ارث می‌برد
            user_role = resolve_effective_role(getattr(user, 'role', None))
            if user_role not in allowed_roles:
                # نقش مجاز نیست
                messages.error(request, "شما به این بخش دسترسی ندارید.")
                return redirect(reverse(redirect_url))  # صفحه 403 یا صفحه اصلی
                # یا می‌تونی بنویسی:
                # return HttpResponseForbidden("دسترسی غیرمجاز")

            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator


def permission_required(permission_field, redirect_url='forbidden'):
    """
    Decorator برای محدود کردن دسترسی بر اساس مجوزهای خاص
    
    استفاده:
    @permission_required('can_manage_shipments')
    @permission_required('can_view_reports')
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user = request.user

            # 🔹 اگر کاربر وارد نشده بود:
            if not user.is_authenticated:
                messages.warning(request, "برای مشاهده این صفحه ابتدا وارد شوید.")
                return redirect(reverse('login'))

            # 🔹 بررسی مجوز
            if not has_permission(user, permission_field):
                messages.error(request, "شما به این بخش دسترسی ندارید.")
                return redirect(reverse(redirect_url))

            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator
