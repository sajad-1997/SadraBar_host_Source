from django.contrib import admin

from .models import (
    SystemRule, Role, SystemModule, ModuleAccessRule, UserModuleAccess,
    IssuanceQuota, Wallet, WalletTransaction, SystemAuditLog,
)


class SuperuserOnlyAdmin(admin.ModelAdmin):
    """دسترسی به این مدل‌ها فقط برای سوپر ادمین (از طریق پنل ادمین)"""

    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(SystemRule)
class SystemRuleAdmin(SuperuserOnlyAdmin):
    list_display = ('id', 'enforce_module_locks', 'lock_all_modules',
                    'enforce_quotas', 'default_daily_limit', 'wallet_enabled',
                    'updated_by', 'updated_at')

    def has_add_permission(self, request):
        # فقط یک رکورد مجاز است
        if SystemRule.objects.exists():
            return False
        return request.user.is_superuser


@admin.register(Role)
class RoleAdmin(SuperuserOnlyAdmin):
    list_display = ('code', 'name', 'base_role', 'is_active', 'created_at')
    list_filter = ('is_active', 'base_role')
    search_fields = ('code', 'name')


@admin.register(SystemModule)
class SystemModuleAdmin(SuperuserOnlyAdmin):
    list_display = ('key', 'name', 'url_prefix', 'is_locked', 'is_active')
    list_editable = ('is_locked', 'is_active')
    list_filter = ('is_locked', 'is_active')


@admin.register(ModuleAccessRule)
class ModuleAccessRuleAdmin(SuperuserOnlyAdmin):
    list_display = ('module', 'role', 'is_locked')
    list_filter = ('is_locked', 'module')
    search_fields = ('role', 'module__name')


@admin.register(UserModuleAccess)
class UserModuleAccessAdmin(SuperuserOnlyAdmin):
    list_display = ('user', 'module', 'mode', 'note', 'created_at')
    list_filter = ('mode', 'module')
    search_fields = ('user__username', 'module__name')


@admin.register(IssuanceQuota)
class IssuanceQuotaAdmin(SuperuserOnlyAdmin):
    list_display = ('scope', 'role', 'user', 'period', 'max_count', 'is_active')
    list_filter = ('scope', 'period', 'is_active')


@admin.register(Wallet)
class WalletAdmin(SuperuserOnlyAdmin):
    list_display = ('id', 'user', 'role', 'balance', 'is_frozen', 'updated_at')
    list_filter = ('is_frozen',)
    search_fields = ('user__username', 'role')
    readonly_fields = ('balance',)


@admin.register(WalletTransaction)
class WalletTransactionAdmin(SuperuserOnlyAdmin):
    list_display = ('wallet', 'tx_type', 'amount', 'balance_after',
                    'created_by', 'created_at')
    list_filter = ('tx_type',)
    readonly_fields = ('wallet', 'tx_type', 'amount', 'balance_after',
                       'note', 'created_by', 'created_at')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(SystemAuditLog)
class SystemAuditLogAdmin(SuperuserOnlyAdmin):
    list_display = ('created_at', 'actor', 'action', 'target', 'ip_address')
    search_fields = ('action', 'target', 'actor__username')
    readonly_fields = ('actor', 'action', 'target', 'description',
                       'ip_address', 'created_at')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser


# نکته: RolePermission در accounts/admin.py ثبت شده و دسترسی آن در پنل ادمین
# توسط CustomUserAdmin و RolePermissionAdmin مدیریت می‌شود.
