from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User, RolePermission


# ---------- پنل مدیریت کاربران ----------
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # ستون‌هایی که در لیست نمایش داده می‌شوند
    list_display = ('username', 'email', 'role', 'is_staff', 'is_active')
    # ستون‌های قابل فیلتر
    list_filter = ('role', 'is_staff', 'is_active')
    # ستون‌های قابل ویرایش مستقیم
    list_editable = ('role', 'is_active')

    # بخش‌های فرم ویرایش
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('اطلاعات شخصی', {'fields': ('first_name', 'last_name', 'email')}),
        ('نقش و دسترسی', {'fields': ('role', 'is_staff', 'is_superuser', 'is_active')}),
    )


# ---------- پنل عملیاتی RolePermission ----------
@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ('role', 'can_access_dashboard', 'can_manage_shipments', 'can_view_reports', 'can_manage_users', 'can_manage_customers', 'can_manage_drivers')
    list_editable = ('can_access_dashboard', 'can_manage_shipments', 'can_view_reports', 'can_manage_users', 'can_manage_customers', 'can_manage_drivers')

