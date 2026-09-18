from django import template

register = template.Library()


@register.filter
def has_permission(user, permission_field):
    """بررسی اینکه آیا کاربر مجوز خاصی دارد یا خیر در قالب‌ها"""
    if not user or not user.is_authenticated:
        return False
    
    # مدیر کل سیستم به همه چیز دسترسی دارد
    user_role = getattr(user, 'role', None)
    if user.is_superuser or user_role == 'admin':
        return True
    
    try:
        from accounts.models import RolePermission
        if not user_role:
            return False
        permissions = RolePermission.objects.filter(role=user_role).first()
        if not permissions:
            return False
        return getattr(permissions, permission_field, False)
    except:
        return False


@register.filter
def is_admin(user):
    """بررسی نقش مدیر کل سیستم"""
    if not user or not user.is_authenticated:
        return False
    return getattr(user, 'role', None) == 'admin'


@register.filter
def is_manager(user):
    """بررسی نقش مدیریت"""
    if not user or not user.is_authenticated:
        return False
    return getattr(user, 'role', None) == 'manager'


@register.filter
def is_employee(user):
    """بررسی نقش کارمند"""
    if not user or not user.is_authenticated:
        return False
    return getattr(user, 'role', None) == 'employee'


@register.filter
def is_driver(user):
    """بررسی نقش راننده"""
    if not user or not user.is_authenticated:
        return False
    return getattr(user, 'role', None) == 'driver'


@register.filter
def is_customer(user):
    """بررسی نقش مشتری"""
    if not user or not user.is_authenticated:
        return False
    return getattr(user, 'role', None) == 'customer'
