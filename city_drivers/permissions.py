from functools import wraps

from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.urls import reverse

from accounts.decorators import get_user_permissions

ROLE_ADMIN = 'admin'
ROLE_MANAGER = 'manager'
ROLE_EMPLOYEE = 'employee'

# کلیدهای مجوز ماژول رانندگان شهری
# (فیلدهای مدل RolePermission در ماژول accounts که توسط مدیریت/ادمین
#  برای نقش‌های «کارمند» و «مدیریت» فعال می‌شوند؛ نقش ادمین همیشه کامل است)
URBAN_PERMISSIONS = [
    ('can_urban_access_dashboard', 'دسترسی به داشبورد رانندگان شهری'),
    ('can_urban_view_customers', 'مشاهده مشتریان شهری'),
    ('can_urban_add_customers', 'ثبت و ویرایش مشتریان شهری'),
    ('can_urban_view_requests', 'مشاهده درخواست‌های سرویس شهری'),
    ('can_urban_add_requests', 'ثبت درخواست سرویس شهری'),
    ('can_urban_edit_requests', 'ویرایش و تغییر وضعیت درخواست سرویس'),
    ('can_urban_assign_requests', 'تخصیص راننده به سرویس'),
    ('can_urban_view_queue', 'مشاهده نوبت و حضور رانندگان'),
    ('can_urban_manage_queue', 'مدیریت نوبت و حضور رانندگان'),
    ('can_urban_view_rates', 'مشاهده نرخ‌نامه و محاسبه کرایه'),
    ('can_urban_manage_rates', 'مدیریت نرخ‌نامه‌ها'),
    ('can_urban_view_locations', 'مشاهده موقعیت رانندگان'),
    ('can_urban_manage_settlements', 'تسویه بدهی کمیسیون رانندگان'),
    ('can_urban_view_reports', 'مشاهده گزارش‌های روزانه مدیریت'),
]


def get_urban_role(user):
    """نقش کاربر در ماژول رانندگان شهری؛ None یعنی بدون دسترسی.

    - ادمین (مدیر کل سیستم): دسترسی کامل
    - مدیریت: دسترسی بر اساس مجوزهایی که ادمین برای نقش مدیریت تعیین کرده
    - کارمند: دسترسی بر اساس مجوزهایی که مدیریت برای نقش کارمند تعیین کرده
    """
    if not user or not getattr(user, 'is_authenticated', False):
        return None
    if user.is_superuser:
        return ROLE_ADMIN
    role = getattr(user, 'role', None)
    if role in (ROLE_ADMIN, ROLE_MANAGER, ROLE_EMPLOYEE):
        return role
    return None


def has_urban_permission(user, perm):
    """بررسی یک مجوز ماژول رانندگان شهری برای کاربر"""
    role = get_urban_role(user)
    if role is None:
        return False
    if role == ROLE_ADMIN:
        return True
    permissions = get_user_permissions(user)
    if not permissions:
        return False
    return bool(getattr(permissions, perm, False))


def urban_permissions_map(user):
    """دیکشنری وضعیت همه مجوزهای ماژول برای استفاده در قالب‌ها (نوار کناری)"""
    return {name: has_urban_permission(user, name) for name, _ in URBAN_PERMISSIONS}


def urban_access_required(perm=None):
    """دکوراتور دسترسی صفحات ماژول رانندگان شهری.

    استفاده:
        @urban_access_required('can_urban_view_requests')
        @urban_access_required()  # فقط دسترسی کلی به ماژول
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            user = getattr(request, 'user', None)
            if not getattr(user, 'is_authenticated', False):
                return redirect(reverse('login'))
            if not has_urban_permission(user, perm):
                raise PermissionDenied('شما به این بخش از ماژول رانندگان شهری دسترسی ندارید.')
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator


def urban_manager_required(view_func):
    """دسترسی مدیریتی؛ فقط ادمین و مدیریت (بدون کارمند)"""

    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        user = getattr(request, 'user', None)
        if not getattr(user, 'is_authenticated', False):
            return redirect(reverse('login'))
        if get_urban_role(user) not in (ROLE_ADMIN, ROLE_MANAGER):
            raise PermissionDenied('این عملیات فقط برای مدیریت مجاز است.')
        return view_func(request, *args, **kwargs)

    return _wrapped
