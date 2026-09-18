from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from accounts.models import User


# =========================================================
# ماژول‌های پیش‌فرض سیستم (کلید، نام فارسی، پیشوند آدرس)
# =========================================================
MODULE_DEFAULTS = [
    ('dashboard', 'داشبورد عملیاتی', '/dashboard/'),
    ('issuance', 'صدور بارنامه', '/issuance/'),
    ('captions', 'توضیحات بارنامه', '/captions/'),
    ('cargo', 'کالا / بار', '/cargo/'),
    ('customers', 'مشتریان', '/customers/'),
    ('drivers', 'رانندگان', '/drivers/'),
    ('fleet', 'ناوگان و وسایل نقلیه', '/fleet/'),
    ('duplicate_audit', 'کنترل بارنامه‌های تکراری', '/duplicate/'),
    ('report', 'گزارش‌ها', '/report/'),
    ('otp_verification', 'تایید دو مرحله‌ای (OTP)', '/otp/'),
    ('printing', 'چاپ بارنامه', '/printing/'),
    ('driver_queue', 'نوبت‌دهی رانندگان', '/driver-queue/'),
    ('user_management', 'مدیریت کاربران', '/user-management/'),
]


class SystemRule(models.Model):
    """قوانین سراسری سیستم (سینگلتون - فقط رکورد pk=1)"""

    enforce_module_locks = models.BooleanField(
        default=True, verbose_name='اعمال قفل ماژول‌ها')
    lock_all_modules = models.BooleanField(
        default=False,
        verbose_name='قفل کامل سیستم (فقط سوپر ادمین دسترسی دارد)')
    enforce_quotas = models.BooleanField(
        default=True, verbose_name='اعمال سهمیه صدور بارنامه')
    default_daily_limit = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name='سقف پیش‌فرض روزانه صدور بارنامه (برای همه نقش‌ها)')
    wallet_enabled = models.BooleanField(
        default=True, verbose_name='فعال بودن کیف پول')
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='system_rules_updated',
        verbose_name='آخرین تغییر توسط')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین تغییر')

    class Meta:
        verbose_name = 'قانون سیستم'
        verbose_name_plural = 'قوانین سیستم'

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return 'قوانین سراسری سیستم'


class Role(models.Model):
    """نقش سفارشی قابل ایجاد توسط سوپر ادمین.

    هر نقش سفارشی به یک «نقش پایه» متصل است و سطح دسترسی پایه آن را
    به ارث می‌برد؛ سپس سوپر ادمین می‌تواند مجوزها/قفل‌ها/سهمیه‌های
    اختصاصی برای آن تعریف کند.
    """

    code = models.CharField(max_length=20, unique=True, verbose_name='کد نقش')
    name = models.CharField(max_length=60, verbose_name='نام نقش')
    base_role = models.CharField(
        max_length=20, choices=User.ROLE_CHOICES, verbose_name='نقش پایه')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')

    class Meta:
        verbose_name = 'نقش سفارشی'
        verbose_name_plural = 'نقش‌های سفارشی'

    def __str__(self):
        return f'{self.name} ({self.code})'


class SystemModule(models.Model):
    """ثبت ماژول‌های سیستم برای کنترل دسترسی"""

    key = models.CharField(max_length=50, unique=True, verbose_name='کلید ماژول')
    name = models.CharField(max_length=100, verbose_name='نام ماژول')
    url_prefix = models.CharField(max_length=100, verbose_name='پیشوند آدرس')
    is_locked = models.BooleanField(
        default=False,
        verbose_name='قفل کامل (غیرقابل دسترسی برای همه بجز سوپر ادمین)')
    is_active = models.BooleanField(default=True, verbose_name='فعال')

    class Meta:
        verbose_name = 'ماژول سیستم'
        verbose_name_plural = 'ماژول‌های سیستم'
        ordering = ('id',)

    def __str__(self):
        return self.name


class ModuleAccessRule(models.Model):
    """قفل کردن یک ماژول برای یک نقش مشخص"""

    module = models.ForeignKey(
        SystemModule, on_delete=models.CASCADE,
        related_name='role_rules', verbose_name='ماژول')
    role = models.CharField(max_length=20, verbose_name='نقش')
    is_locked = models.BooleanField(default=True, verbose_name='قفل')

    class Meta:
        verbose_name = 'قفل ماژول برای نقش'
        verbose_name_plural = 'قفل ماژول‌ها برای نقش‌ها'
        unique_together = ('module', 'role')

    def __str__(self):
        return f'{self.module.name} - {self.role} - {"قفل" if self.is_locked else "باز"}'


class UserModuleAccess(models.Model):
    """دسترسی اختصاصی یک کاربر به یک ماژول (بالا دست از قفل نقش)"""

    MODE_CHOICES = [
        ('allow', 'اجازه دسترسی'),
        ('deny', 'عدم دسترسی (قفل)'),
    ]
    module = models.ForeignKey(
        SystemModule, on_delete=models.CASCADE,
        related_name='user_overrides', verbose_name='ماژول')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='module_overrides', verbose_name='کاربر')
    mode = models.CharField(max_length=10, choices=MODE_CHOICES, verbose_name='وضعیت')
    note = models.CharField(max_length=200, blank=True, null=True, verbose_name='توضیح')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='module_overrides_created')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'دسترسی اختصاصی کاربر به ماژول'
        verbose_name_plural = 'دسترسی‌های اختصاصی کاربران به ماژول‌ها'
        unique_together = ('module', 'user')

    def __str__(self):
        return f'{self.user.username} - {self.module.name} - {self.get_mode_display()}'


class IssuanceQuota(models.Model):
    """سهمیه صدور بارنامه برای نقش یا کاربر مشخص"""

    SCOPE_CHOICES = [
        ('role', 'نقش'),
        ('user', 'کاربر'),
    ]
    PERIOD_CHOICES = [
        ('daily', 'روزانه'),
        ('weekly', 'هفتگی'),
        ('monthly', 'ماهانه'),
        ('total', 'کل عمر سیستم'),
    ]
    scope = models.CharField(max_length=10, choices=SCOPE_CHOICES, verbose_name='دامنه')
    role = models.CharField(max_length=20, null=True, blank=True, verbose_name='نقش')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.CASCADE, related_name='issuance_quotas', verbose_name='کاربر')
    period = models.CharField(max_length=10, choices=PERIOD_CHOICES, verbose_name='دوره')
    max_count = models.PositiveIntegerField(
        verbose_name='حداکثر تعداد مجاز (0 = ممنوعیت کامل صدور)')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    note = models.CharField(max_length=200, blank=True, null=True, verbose_name='توضیح')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='quotas_created')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'سهمیه صدور بارنامه'
        verbose_name_plural = 'سهمیه‌های صدور بارنامه'
        ordering = ('scope', 'period', 'id')

    def clean(self):
        if self.scope == 'role' and not self.role:
            raise ValidationError('برای دامنه «نقش» انتخاب نقش الزامی است.')
        if self.scope == 'user' and not self.user:
            raise ValidationError('برای دامنه «کاربر» انتخاب کاربر الزامی است.')
        if self.scope == 'role':
            self.user = None
        if self.scope == 'user':
            self.role = None

    def target_display(self):
        if self.scope == 'user' and self.user:
            return self.user.username
        if self.scope == 'role':
            return self.role
        return '-'

    def __str__(self):
        return f'{self.get_scope_display()} {self.target_display()} - {self.get_period_display()} - {self.max_count}'


class Wallet(models.Model):
    """کیف پول کاربر یا نقش (کیف پول نقش = مشترک بین اعضای نقش)"""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.CASCADE, related_name='wallet', verbose_name='کاربر')
    role = models.CharField(
        max_length=20, null=True, blank=True, unique=True,
        verbose_name='نقش (کیف پول مشترک نقش)')
    balance = models.DecimalField(
        max_digits=15, decimal_places=0, default=0, verbose_name='موجودی (تومان)')
    is_frozen = models.BooleanField(default=False, verbose_name='مسدود (فریز)')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')

    class Meta:
        verbose_name = 'کیف پول'
        verbose_name_plural = 'کیف پول‌ها'

    def clean(self):
        if bool(self.user) == bool(self.role):
            raise ValidationError('کیف پول باید به یک کاربر یا یک نقش متصل باشد (فقط یکی).')

    def owner_display(self):
        if self.user:
            return self.user.username
        if self.role:
            return f'نقش {self.role}'
        return '-'

    def __str__(self):
        return f'{self.owner_display()} - {self.balance}'


class WalletTransaction(models.Model):
    """تراکنش‌های کیف پول"""

    TX_TYPES = [
        ('deposit', 'شارژ'),
        ('withdraw', 'برداشت'),
        ('adjust', 'اصلاحیه'),
    ]
    wallet = models.ForeignKey(
        Wallet, on_delete=models.CASCADE, related_name='transactions', verbose_name='کیف پول')
    tx_type = models.CharField(max_length=10, choices=TX_TYPES, verbose_name='نوع تراکنش')
    amount = models.DecimalField(max_digits=15, decimal_places=0, verbose_name='مبلغ (تومان)')
    balance_after = models.DecimalField(
        max_digits=15, decimal_places=0, verbose_name='موجودی پس از تراکنش')
    note = models.CharField(max_length=200, blank=True, null=True, verbose_name='توضیح')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='wallet_transactions_created', verbose_name='توسط')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'تراکنش کیف پول'
        verbose_name_plural = 'تراکنش‌های کیف پول'
        ordering = ('-created_at', '-id')

    def __str__(self):
        return f'{self.get_tx_type_display()} {self.amount} - {self.wallet.owner_display()}'


class SystemAuditLog(models.Model):
    """گزارش عملیات سوپر ادمین در ماژول کنترل سیستم"""

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='system_audit_logs', verbose_name='عملگر')
    action = models.CharField(max_length=100, verbose_name='عملیات')
    target = models.CharField(max_length=200, blank=True, null=True, verbose_name='هدف')
    description = models.TextField(blank=True, null=True, verbose_name='توضیحات')
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='آی‌پی')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'گزارش عملیات سیستم'
        verbose_name_plural = 'گزارش‌های عملیات سیستم'
        ordering = ('-created_at', '-id')

    def __str__(self):
        return f'{self.action} - {self.actor} - {self.created_at}'
