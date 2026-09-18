def get_user_role(user):
    """دریافت نقش کاربر انجام‌دهنده فرایند برای ذخیره در فیلدهای created_by_role / updated_by_role

    ابتدا نام نمایشی نقش (get_role_display) و در صورت نبود آن، مقدار raw فیلد role کاربر برمی‌گردد.
    """
    if not user or not getattr(user, 'is_authenticated', False):
        return None
    get_role_display = getattr(user, 'get_role_display', None)
    if callable(get_role_display):
        try:
            return get_role_display()
        except Exception:
            pass
    return getattr(user, 'role', None)
