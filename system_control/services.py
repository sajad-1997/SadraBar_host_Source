from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from accounts.models import User
from .models import (
    MODULE_DEFAULTS, SystemRule, Role, SystemModule, ModuleAccessRule,
    UserModuleAccess, IssuanceQuota, Wallet, WalletTransaction,
    SystemAuditLog,
)

PERIOD_LABELS = dict(IssuanceQuota.PERIOD_CHOICES)


# =========================================================
# نقش‌ها
# =========================================================
def get_custom_role(code):
    """برگرداندن نقش سفارشی فعال بر اساس کد"""
    if not code:
        return None
    return Role.objects.filter(code=code, is_active=True).first()


def role_label(code):
    """نام نمایشی نقش (استاندارد یا سفارشی)"""
    for choice_code, label in User.ROLE_CHOICES:
        if choice_code == code:
            return label
    custom = get_custom_role(code)
    if custom:
        return custom.name
    return code or '-'


def all_roles():
    """لیست همه نقش‌ها (استاندارد + سفارشی) به شکل [(code, label), ...]"""
    roles = list(User.ROLE_CHOICES)
    known = {code for code, _ in roles}
    for custom in Role.objects.filter(is_active=True).order_by('name'):
        if custom.code not in known:
            roles.append((custom.code, custom.name))
            known.add(custom.code)
    return roles


# =========================================================
# ماژول‌ها و کنترل دسترسی
# =========================================================
def ensure_default_modules():
    """ثبت خودکار ماژول‌های پیش‌فرض (idempotent)"""
    for key, name, prefix in MODULE_DEFAULTS:
        SystemModule.objects.get_or_create(
            key=key, defaults={'name': name, 'url_prefix': prefix})


def get_module_for_path(path):
    """یافتن ماژول مربوط به یک مسیر بر اساس طولانی‌ترین پیشوند مطابقت"""
    modules = list(SystemModule.objects.filter(is_active=True).only('key', 'url_prefix'))
    best = None
    for module in modules:
        if path.startswith(module.url_prefix):
            if best is None or len(module.url_prefix) > len(best.url_prefix):
                best = module
    return best


def get_module_access(user, module):
    """بررسی دسترسی کاربر به ماژول.

    اولویت: دسترسی اختصاصی کاربر > قفل نقش > قفل کامل ماژول.
    خروجی: (مجاز است؟, دلیل)
    """
    if user.is_superuser:
        return True, ''

    # دسترسی اختصاصی کاربر (بالاترین اولویت)
    override = UserModuleAccess.objects.filter(module=module, user=user).first()
    if override:
        if override.mode == 'allow':
            return True, ''
        return False, f'دسترسی شما به ماژول «{module.name}» توسط سوپر ادمین قفل شده است.'

    # قفل کامل ماژول
    if module.is_locked:
        return False, f'ماژول «{module.name}» توسط سوپر ادمین به طور کامل قفل شده است.'

    # قفل برای نقش کاربر (نقش سفارشی از نقش پایه هم ارث می‌برد)
    role_codes = [user.role]
    custom = get_custom_role(user.role)
    if custom and custom.base_role not in role_codes:
        role_codes.append(custom.base_role)

    if ModuleAccessRule.objects.filter(
            module=module, is_locked=True, role__in=role_codes).exists():
        return False, f'ماژول «{module.name}» برای نقش شما قفل شده است.'

    return True, ''


def user_can_access_path(user, path, rule=None):
    """بررسی دسترسی کاربر به مسیر (استفاده در middleware)"""
    if rule is None:
        rule = SystemRule.load()

    if not rule.enforce_module_locks:
        return True, ''

    if rule.lock_all_modules:
        return False, 'کل سیستم توسط سوپر ادمین قفل شده است. لطفاً با مدیر تماس بگیرید.'

    module = get_module_for_path(path)
    if not module:
        return True, ''

    return get_module_access(user, module)


# =========================================================
# سهمیه صدور بارنامه
# =========================================================
def _period_window(period):
    """بازه زمانی هر دوره (نایو، هماهنگ با created_at که USE_TZ=False است)"""
    now = timezone.now()
    if period == 'daily':
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return start, None
    if period == 'weekly':
        # شروع هفته: شنبه (مطابق تقویم کاری سیستم)
        days_since_saturday = (now.weekday() - 5) % 7
        start = (now - timedelta(days=days_since_saturday)).replace(
            hour=0, minute=0, second=0, microsecond=0)
        return start, None
    if period == 'monthly':
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return start, None
    # total - کل عمر سیستم
    return None, None


def count_issued_bijaks(user, period):
    """تعداد بارنامه‌های صادرشده توسط کاربر در دوره مشخص (بر اساس آمار سیستم)"""
    from issuance.models.bijak import Bijak

    start, end = _period_window(period)
    qs = Bijak.objects.filter(created_by=user)
    if start:
        qs = qs.filter(created_at__gte=start)
    if end:
        qs = qs.filter(created_at__lt=end)
    return qs.count()


def count_issued_bijaks_by_role(role, period):
    """تعداد بارنامه‌های صادرشده توسط اعضای یک نقش در دوره مشخص"""
    from issuance.models.bijak import Bijak

    start, end = _period_window(period)
    qs = Bijak.objects.filter(created_by__role=role)
    if start:
        qs = qs.filter(created_at__gte=start)
    if end:
        qs = qs.filter(created_at__lt=end)
    return qs.count()


def get_quota_status(user):
    """وضعیت سهمیه‌های فعال کاربر.

    خروجی: لیستی از دیکشنری‌ها
    {period, label, limit, used, remaining, source, exceeded}
    """
    if not user or not getattr(user, 'is_authenticated', False):
        return []

    rule = SystemRule.load()
    if not rule.enforce_quotas:
        return []

    if user.is_superuser:
        return []

    periods = set(
        IssuanceQuota.objects.filter(is_active=True).values_list('period', flat=True))
    if rule.default_daily_limit is not None:
        periods.add('daily')

    statuses = []
    for period in ('daily', 'weekly', 'monthly', 'total'):
        if period not in periods:
            continue

        user_quota = IssuanceQuota.objects.filter(
            scope='user', user=user, is_active=True, period=period).first()
        role_quota = IssuanceQuota.objects.filter(
            scope='role', role=user.role, is_active=True, period=period).first()

        # اولویت: سهمیه اختصاصی کاربر > سهمیه نقش > سقف پیش‌فرض سیستم (روزانه)
        if user_quota:
            limit, source = user_quota.max_count, f'سهمیه اختصاصی کاربر ({period})'
        elif role_quota:
            limit, source = role_quota.max_count, f'سهمیه نقش {role_label(user.role)} ({period})'
        elif period == 'daily' and rule.default_daily_limit is not None:
            limit, source = rule.default_daily_limit, 'سقف پیش‌فرض سیستم'
        else:
            continue

        used = count_issued_bijaks(user, period)
        statuses.append({
            'period': period,
            'label': PERIOD_LABELS[period],
            'limit': limit,
            'used': used,
            'remaining': max(limit - used, 0),
            'source': source,
            'exceeded': used >= limit,
        })
    return statuses


def check_issuance_allowed(user):
    """آیا کاربر اجازه صدور بارنامه جدید دارد؟

    خروجی: (مجاز؟, پیام خطا, وضعیت سهمیه‌ها)
    سوپر ادمین همیشه مجاز است.
    """
    if not user or not getattr(user, 'is_authenticated', False):
        return False, 'برای صدور بارنامه ابتدا وارد شوید.', []

    if user.is_superuser:
        return True, '', []

    statuses = get_quota_status(user)
    exceeded = [s for s in statuses if s['exceeded']]
    if exceeded:
        parts = [f"{s['label']}: {s['used']} از {s['limit']}" for s in exceeded]
        message = ('سقف صدور بارنامه شما تکمیل شده است. لطفاً با مدیریت تماس بگیرید. ('
                   + '، '.join(parts) + ')')
        return False, message, statuses
    return True, '', statuses


# =========================================================
# گزارش عملیات
# =========================================================
def log_action(actor, action, target='', description='', request=None):
    ip = None
    if request is not None:
        ip = request.META.get('REMOTE_ADDR')
    return SystemAuditLog.objects.create(
        actor=actor if getattr(actor, 'is_authenticated', False) else None,
        action=action, target=target or '',
        description=description or '', ip_address=ip)


# =========================================================
# کیف پول
# =========================================================
def get_or_create_wallet(user=None, role=None):
    if user:
        wallet, _ = Wallet.objects.get_or_create(user=user)
        return wallet
    if role:
        wallet, _ = Wallet.objects.get_or_create(role=role)
        return wallet
    raise ValueError('برای کیف پول باید کاربر یا نقش مشخص شود.')


def perform_wallet_operation(*, wallet, op_type, amount, note='', actor=None, request=None):
    """انجام عملیات شارژ/برداشت/اصلاحیه با ثبت تراکنش و گزارش عملیات."""
    from decimal import Decimal

    amount = Decimal(amount)
    if amount <= 0:
        raise ValueError('مبلغ باید بزرگ‌تر از صفر باشد.')
    if wallet.is_frozen:
        raise ValueError('این کیف پول مسدود (فریز) است و امکان تراکنش ندارد.')

    with transaction.atomic():
        wallet = Wallet.objects.select_for_update().get(pk=wallet.pk)
        balance = wallet.balance

        if op_type == 'deposit':
            balance += amount
        elif op_type == 'withdraw':
            if balance < amount:
                raise ValueError('موجودی کافی نیست.')
            balance -= amount
        elif op_type == 'adjust':
            balance = amount
        else:
            raise ValueError('نوع تراکنش نامعتبر است.')

        wallet.balance = balance
        wallet.save()

        tx = WalletTransaction.objects.create(
            wallet=wallet, tx_type=op_type, amount=amount,
            balance_after=balance, note=note or '',
            created_by=actor if getattr(actor, 'is_authenticated', False) else None)

    log_action(
        actor, 'wallet_transaction', target=wallet.owner_display(),
        description=f'{tx.get_tx_type_display()} {amount} - {note or ""}',
        request=request)
    return tx
