from django.contrib import messages
from django.db.models import Count, Q, Sum
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from accounts.models import User, RolePermission
from .decorators import superuser_required
from .security_monitor import SecurityMonitor
from .forms import (
    UserCreateForm, CustomRoleForm, SystemRuleForm, IssuanceQuotaForm,
)
from .models import (
    SystemRule, Role, SystemModule, ModuleAccessRule, UserModuleAccess,
    IssuanceQuota, Wallet, SystemAuditLog,
)
from . import services
from .services import role_label


def _get_all_roles():
    return services.all_roles()


def _build_statistics():
    """آمار سیستم برای داشبورد نظارت"""
    from issuance.models.bijak import Bijak

    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    bijak_qs = Bijak.objects.all()
    total_bijaks = bijak_qs.count()
    today_bijaks = bijak_qs.filter(created_at__gte=today_start).count()
    month_bijaks = bijak_qs.filter(created_at__gte=month_start).count()

    # آمار صدور بر اساس نقش‌ها (بجز سوپر ادمین که نقش مستقل ندارد)
    role_rows = bijak_qs.values('created_by__role').annotate(
        total=Count('id'),
        today=Count('id', filter=Q(created_at__gte=today_start)),
        month=Count('id', filter=Q(created_at__gte=month_start)),
    ).order_by('-total')

    role_stats = []
    for row in role_rows:
        code = row['created_by__role'] or 'unknown'
        role_stats.append({
            'role': code,
            'label': 'نامشخص' if code == 'unknown' else role_label(code),
            'total': row['total'],
            'today': row['today'],
            'month': row['month'],
        })

    # کاربران برتر این ماه به همراه وضعیت سهمیه
    top_users = []
    top_rows = bijak_qs.filter(created_at__gte=month_start).values(
        'created_by', 'created_by__username', 'created_by__first_name',
        'created_by__last_name', 'created_by__role',
    ).annotate(count=Count('id')).order_by('-count')[:15]
    for row in top_rows:
        if not row['created_by']:
            continue
        user = User.objects.filter(id=row['created_by']).first()
        entry = {
            'username': row['created_by__username'],
            'full_name': f"{row['created_by__first_name'] or ''} {row['created_by__last_name'] or ''}".strip(),
            'role_label': role_label(row['created_by__role']),
            'count': row['count'],
            'quotas': services.get_quota_status(user) if user else [],
        }
        top_users.append(entry)

    user_role_counts = User.objects.values('role').annotate(count=Count('id'))

    wallets_agg = Wallet.objects.aggregate(total_balance=Sum('balance'))
    frozen_wallets = Wallet.objects.filter(is_frozen=True).count()

    context = {
        'total_bijaks': total_bijaks,
        'today_bijaks': today_bijaks,
        'month_bijaks': month_bijaks,
        'role_stats': role_stats,
        'top_users': top_users,
        'user_role_counts': [(role_label(r['role']), r['count']) for r in user_role_counts],
        'total_users': User.objects.count(),
        'active_users': User.objects.filter(is_active=True).count(),
        'active_quotas': IssuanceQuota.objects.filter(is_active=True).count(),
        'locked_modules': SystemModule.objects.filter(is_locked=True).count(),
        'locked_role_rules': ModuleAccessRule.objects.filter(is_locked=True).count(),
        'user_locks': UserModuleAccess.objects.filter(mode='deny').count(),
        'wallet_total_balance': wallets_agg['total_balance'] or 0,
        'frozen_wallets': frozen_wallets,
        'recent_logs': SystemAuditLog.objects.all()[:15],
    }
    return context


@superuser_required
def index(request):
    """داشبورد کنترل سیستم: قوانین سراسری + نظارت بر آمار"""
    services.ensure_default_modules()
    rule = SystemRule.load()

    if request.method == 'POST' and request.POST.get('action') == 'save_rules':
        form = SystemRuleForm(request.POST, instance=rule)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.updated_by = request.user
            obj.save()
            services.log_action(
                request.user, 'update_system_rules',
                description='بروزرسانی قوانین سراسری سیستم', request=request)
            messages.success(request, 'قوانین سیستم با موفقیت ذخیره شد.')
            return redirect('system_control:index')
        messages.error(request, 'خطا در ذخیره قوانین. مقادیر را بررسی کنید.')
    else:
        form = SystemRuleForm(instance=rule)

    context = {'rule': rule, 'rule_form': form}
    context.update(_build_statistics())
    return render(request, 'system_control/dashboard.html', context)


# =========================================================
# ۱- مدیریت کاربران
# =========================================================
@superuser_required
def users(request):
    """ایجاد، حذف و مدیریت کاربران"""
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'create_user':
            form = UserCreateForm(request.POST)
            if form.is_valid():
                user = form.save(commit=False)
                user.set_password(form.cleaned_data['password1'])
                user.save()
                services.log_action(
                    request.user, 'create_user', target=user.username,
                    description=f'ایجاد کاربر با نقش {user.role}', request=request)
                messages.success(request, f'کاربر «{user.username}» با موفقیت ایجاد شد.')
                return redirect('system_control:user_detail', user_id=user.id)
            messages.error(request, 'خطا در ایجاد کاربر. اطلاعات فرم را بررسی کنید.')

        elif action == 'delete_user':
            target = get_object_or_404(User, id=request.POST.get('user_id'))
            if target.is_superuser:
                messages.error(request, 'حذف کاربر سوپر ادمین مجاز نیست.')
            elif target == request.user:
                messages.error(request, 'حذف حساب خودتان مجاز نیست.')
            else:
                username = target.username
                target.delete()
                services.log_action(
                    request.user, 'delete_user', target=username,
                    description='حذف کاربر', request=request)
                messages.success(request, f'کاربر «{username}» حذف شد.')
            return redirect('system_control:users')

        elif action == 'toggle_active':
            target = get_object_or_404(User, id=request.POST.get('user_id'))
            if target.is_superuser or target == request.user:
                messages.error(request, 'غیرفعال‌سازی این حساب مجاز نیست.')
            else:
                target.is_active = not target.is_active
                target.save(update_fields=['is_active'])
                state = 'فعال' if target.is_active else 'قفل (غیرفعال)'
                services.log_action(
                    request.user, 'toggle_user', target=target.username,
                    description=f'تغییر وضعیت به {state}', request=request)
                messages.success(request, f'وضعیت کاربر «{target.username}» به {state} تغییر یافت.')
            return redirect('system_control:users')

    search_query = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')

    users_qs = User.objects.all().order_by('-date_joined')
    if search_query:
        users_qs = users_qs.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(user_code__icontains=search_query))
    if role_filter:
        users_qs = users_qs.filter(role=role_filter)

    form = UserCreateForm()
    return render(request, 'system_control/users.html', {
        'users': users_qs,
        'form': form,
        'search_query': search_query,
        'role_filter': role_filter,
        'all_roles': _get_all_roles(),
    })


@superuser_required
def user_detail(request, user_id):
    """جزئیات کاربر: نقش، سهمیه‌ها، قفل ماژول‌ها، کیف پول"""
    target = get_object_or_404(User, id=user_id)
    all_roles = _get_all_roles()

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_profile':
            target.first_name = request.POST.get('first_name', '').strip()
            target.last_name = request.POST.get('last_name', '').strip()
            target.email = request.POST.get('email', '').strip()
            target.save(update_fields=['first_name', 'last_name', 'email'])
            services.log_action(
                request.user, 'update_user', target=target.username,
                description='بروزرسانی اطلاعات کاربر', request=request)
            messages.success(request, 'اطلاعات کاربر بروزرسانی شد.')

        elif action == 'change_role':
            new_role = request.POST.get('new_role')
            if new_role in dict(all_roles) and not target.is_superuser:
                old_role = target.role
                target.role = new_role
                target.save(update_fields=['role'])
                services.log_action(
                    request.user, 'change_role', target=target.username,
                    description=f'{old_role} -> {new_role}', request=request)
                messages.success(request, 'نقش کاربر تغییر یافت.')
            else:
                messages.error(request, 'تغییر نقش این کاربر مجاز نیست یا نقش نامعتبر است.')

        elif action == 'set_password':
            p1 = request.POST.get('password1')
            p2 = request.POST.get('password2')
            if p1 and p1 == p2:
                target.set_password(p1)
                target.save(update_fields=['password'])
                services.log_action(
                    request.user, 'reset_password', target=target.username,
                    description='تغییر رمز عبور توسط سوپر ادمین', request=request)
                messages.success(request, 'رمز عبور تغییر یافت.')
            else:
                messages.error(request, 'رمزهای عبور یکسان نیستند یا خالی است.')

        elif action == 'add_quota':
            period = request.POST.get('period')
            try:
                max_count = int(request.POST.get('max_count', -1))
            except (TypeError, ValueError):
                max_count = -1
            if period in dict(IssuanceQuota.PERIOD_CHOICES) and max_count >= 0:
                IssuanceQuota.objects.update_or_create(
                    scope='user', user=target, period=period,
                    defaults={'max_count': max_count, 'is_active': True,
                              'created_by': request.user})
                services.log_action(
                    request.user, 'add_user_quota', target=target.username,
                    description=f'سهمیه {period} = {max_count}', request=request)
                messages.success(request, 'سهمیه اختصاصی کاربر ذخیره شد.')
            else:
                messages.error(request, 'مقادیر سهمیه نامعتبر است.')
            return redirect('system_control:user_detail', user_id=target.id)

        elif action == 'remove_quota':
            quota = IssuanceQuota.objects.filter(
                id=request.POST.get('quota_id'), scope='user', user=target).first()
            if quota:
                quota.delete()
                services.log_action(
                    request.user, 'remove_user_quota', target=target.username,
                    description=f'حذف سهمیه {quota.period}', request=request)
                messages.success(request, 'سهمیه حذف شد.')
            return redirect('system_control:user_detail', user_id=target.id)

        elif action == 'add_module_override':
            module = SystemModule.objects.filter(id=request.POST.get('module_id')).first()
            mode = request.POST.get('mode')
            if module and mode in ('allow', 'deny'):
                UserModuleAccess.objects.update_or_create(
                    module=module, user=target,
                    defaults={'mode': mode, 'created_by': request.user})
                services.log_action(
                    request.user, 'module_override',
                    target=f'{target.username}/{module.key}',
                    description=f'دسترسی اختصاصی: {mode}', request=request)
                messages.success(request, 'دسترسی اختصاصی ذخیره شد.')
            else:
                messages.error(request, 'مقادیر نامعتبر است.')
            return redirect('system_control:user_detail', user_id=target.id)

        elif action == 'remove_module_override':
            override = UserModuleAccess.objects.filter(
                id=request.POST.get('override_id'), user=target).first()
            if override:
                module_key = override.module.key
                override.delete()
                services.log_action(
                    request.user, 'remove_module_override',
                    target=f'{target.username}/{module_key}', request=request)
                messages.success(request, 'دسترسی اختصاصی حذف شد.')
            return redirect('system_control:user_detail', user_id=target.id)

        return redirect('system_control:user_detail', user_id=target.id)

    context = {
        'target': target,
        'all_roles': all_roles,
        'quota_statuses': services.get_quota_status(target),
        'user_quotas': IssuanceQuota.objects.filter(scope='user', user=target),
        'period_choices': IssuanceQuota.PERIOD_CHOICES,
        'user_overrides': UserModuleAccess.objects.filter(user=target).select_related('module'),
        'all_modules': SystemModule.objects.all(),
    }
    return render(request, 'system_control/user_detail.html', context)


# =========================================================
# ۲- مدیریت نقش‌ها و مجوزها
# =========================================================
def _permission_fields():
    """لیست فیلدهای مجوز (can_*) مدل RolePermission"""
    fields = []
    for f in RolePermission._meta.get_fields():
        if f.name.startswith('can_'):
            fields.append((f.name, getattr(f, 'verbose_name', f.name)))
    return fields


@superuser_required
def roles(request):
    """مدیریت نقش‌ها و مجوزهای آن‌ها"""
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'create_role':
            form = CustomRoleForm(request.POST)
            if form.is_valid():
                custom = form.save()
                # ایجاد رکورد مجوز با کپی مجوزهای نقش پایه
                base_perms = RolePermission.objects.filter(role=custom.base_role).first()
                fields = {name: getattr(base_perms, name, False)
                          for name, _ in _permission_fields()}
                RolePermission.objects.create(role=custom.code, **fields)
                services.log_action(
                    request.user, 'create_role', target=custom.code,
                    description=f"نقش سفارشی '{custom.name}' با نقش پایه {custom.base_role}",
                    request=request)
                messages.success(request, f"نقش «{custom.name}» ایجاد شد.")
            else:
                for errs in form.errors.values():
                    messages.error(request, ' '.join(errs))
            return redirect('system_control:roles')

        elif action == 'update_permissions':
            role_code = request.POST.get('role')
            if role_code in dict(_get_all_roles()):
                perms, _ = RolePermission.objects.get_or_create(role=role_code)
                changed = []
                for name, _ in _permission_fields():
                    value = request.POST.get(name) == 'on'
                    if getattr(perms, name) != value:
                        changed.append(name)
                    setattr(perms, name, value)
                perms.save()
                services.log_action(
                    request.user, 'update_permissions', target=role_code,
                    description='تغییر مجوزها: ' + (', '.join(changed) or 'بدون تغییر'),
                    request=request)
                messages.success(request, f"مجوزهای نقش «{role_label(role_code)}» بروزرسانی شد.")
            else:
                messages.error(request, 'نقش نامعتبر است.')
            return redirect('system_control:roles')

        elif action == 'delete_role':
            role_code = request.POST.get('role')
            custom = Role.objects.filter(code=role_code).first()
            if not custom:
                messages.error(request, 'نقش‌های استاندارد قابل حذف نیستند.')
            else:
                base = custom.base_role
                # انتقال کاربران به نقش پایه
                affected = User.objects.filter(role=custom.code)
                count = affected.count()
                affected.update(role=base)
                # حذف وابستگی‌ها
                IssuanceQuota.objects.filter(scope='role', role=custom.code).delete()
                ModuleAccessRule.objects.filter(role=custom.code).delete()
                Wallet.objects.filter(role=custom.code).delete()
                RolePermission.objects.filter(role=custom.code).delete()
                custom.delete()
                services.log_action(
                    request.user, 'delete_role', target=custom.code,
                    description=f'حذف نقش سفارشی؛ {count} کاربر به نقش {base} منتقل شدند',
                    request=request)
                messages.success(
                    request,
                    f"نقش «{custom.name}» حذف شد. {count} کاربر به نقش پایه منتقل شدند.")
            return redirect('system_control:roles')

    role_codes = _get_all_roles()
    role_cards = []
    for code, label in role_codes:
        custom = Role.objects.filter(code=code).first()
        perms = RolePermission.objects.filter(role=code).first()
        users_count = User.objects.filter(role=code).count()
        role_cards.append({
            'code': code,
            'label': label,
            'custom': custom,
            'perms': perms,
            'users_count': users_count,
        })

    return render(request, 'system_control/roles.html', {
        'role_cards': role_cards,
        'permission_fields': _permission_fields(),
        'role_form': CustomRoleForm(),
    })


# =========================================================
# ۳- مدیریت ماژول‌ها و قفل دسترسی
# =========================================================
@superuser_required
def modules(request):
    """قفل ماژول‌ها برای همه، نقش‌ها و کاربران"""
    services.ensure_default_modules()

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'save_module':
            module = SystemModule.objects.filter(id=request.POST.get('module_id')).first()
            if module:
                module.is_locked = request.POST.get('is_locked') == 'on'
                module.save(update_fields=['is_locked'])
                # قفل برای نقش‌ها: هر نقش تیک خورده = قفل، تیک نخورده = آزاد
                posted = set(request.POST.getlist('locked_roles'))
                for code, _ in _get_all_roles():
                    if code in posted:
                        ModuleAccessRule.objects.update_or_create(
                            module=module, role=code, defaults={'is_locked': True})
                    else:
                        ModuleAccessRule.objects.filter(
                            module=module, role=code).delete()
                services.log_action(
                    request.user, 'save_module_locks', target=module.key,
                    description=f'قفل کامل: {module.is_locked} - نقش‌های قفل: {", ".join(posted) or "-"}',
                    request=request)
                messages.success(request, f'تنظیمات قفل ماژول «{module.name}» ذخیره شد.')
            else:
                messages.error(request, 'ماژول یافت نشد.')
            return redirect('system_control:modules')

        elif action == 'add_override':
            module = SystemModule.objects.filter(id=request.POST.get('module_id')).first()
            user = User.objects.filter(id=request.POST.get('user_id')).first()
            mode = request.POST.get('mode')
            if module and user and mode in ('allow', 'deny'):
                UserModuleAccess.objects.update_or_create(
                    module=module, user=user,
                    defaults={'mode': mode, 'created_by': request.user})
                services.log_action(
                    request.user, 'module_override',
                    target=f'{user.username}/{module.key}',
                    description=f'دسترسی اختصاصی: {mode}', request=request)
                messages.success(request, 'دسترسی اختصاصی ذخیره شد.')
            else:
                messages.error(request, 'مقادیر نامعتبر است.')
            return redirect('system_control:modules')

        elif action == 'remove_override':
            override = UserModuleAccess.objects.filter(
                id=request.POST.get('override_id')).first()
            if override:
                label = f'{override.user.username}/{override.module.key}'
                override.delete()
                services.log_action(
                    request.user, 'remove_module_override', target=label, request=request)
                messages.success(request, 'دسترسی اختصاصی حذف شد.')
            return redirect('system_control:modules')

    all_roles = _get_all_roles()
    modules_qs = SystemModule.objects.all().prefetch_related('role_rules', 'user_overrides')
    module_rows = []
    for module in modules_qs:
        locked_roles = {r.role for r in module.role_rules.all() if r.is_locked}
        module_rows.append({
            'module': module,
            'locked_roles': locked_roles,
        })

    return render(request, 'system_control/modules.html', {
        'module_rows': module_rows,
        'all_roles': all_roles,
        'overrides': UserModuleAccess.objects.select_related('user', 'module')
                     .order_by('-created_at')[:100],
        'all_users': User.objects.all().order_by('username'),
    })


# =========================================================
# ۴- مدیریت سهمیه صدور بارنامه
# =========================================================
@superuser_required
def quotas(request):
    """مدیریت مجوز تعداد صدور بارنامه‌ها"""
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'create_quota':
            form = IssuanceQuotaForm(request.POST)
            if form.is_valid():
                quota = form.save(commit=False)
                quota.created_by = request.user
                try:
                    quota.full_clean()
                    quota.save()
                    services.log_action(
                        request.user, 'create_quota', target=quota.target_display(),
                        description=f'سهمیه {quota.period} = {quota.max_count}',
                        request=request)
                    messages.success(request, 'سهمیه جدید ایجاد شد.')
                except Exception as exc:
                    messages.error(request, str(exc))
            else:
                for errs in form.errors.values():
                    messages.error(request, ' '.join(errs))
            return redirect('system_control:quotas')

        elif action == 'toggle_quota':
            quota = IssuanceQuota.objects.filter(id=request.POST.get('quota_id')).first()
            if quota:
                quota.is_active = not quota.is_active
                quota.save(update_fields=['is_active'])
                state = 'فعال' if quota.is_active else 'غیرفعال'
                services.log_action(
                    request.user, 'toggle_quota', target=quota.target_display(),
                    description=f'سهمیه {quota.period} -> {state}', request=request)
                messages.success(request, f'سهمیه {state} شد.')
            return redirect('system_control:quotas')

        elif action == 'delete_quota':
            quota = IssuanceQuota.objects.filter(id=request.POST.get('quota_id')).first()
            if quota:
                target = quota.target_display()
                quota.delete()
                services.log_action(
                    request.user, 'delete_quota', target=target, request=request)
                messages.success(request, 'سهمیه حذف شد.')
            return redirect('system_control:quotas')

    quota_rows = []
    for quota in IssuanceQuota.objects.all().select_related('user'):
        if quota.scope == 'user' and quota.user:
            used = services.count_issued_bijaks(quota.user, quota.period)
            target_label = quota.user.username
        elif quota.scope == 'role':
            used = services.count_issued_bijaks_by_role(quota.role, quota.period)
            target_label = role_label(quota.role)
        else:
            used, target_label = 0, '-'
        quota_rows.append({
            'quota': quota,
            'target_label': target_label,
            'used': used,
            'remaining': max(quota.max_count - used, 0),
        })

    return render(request, 'system_control/quotas.html', {
        'quota_rows': quota_rows,
        'form': IssuanceQuotaForm(),
    })


# =========================================================
# ۵- مدیریت کیف پول کاربران و نقش‌ها
# =========================================================
def _handle_wallet_operation(request, wallet):
    """اجرای عملیات کیف پول با مدیریت خطا"""
    op_type = request.POST.get('op_type')
    note = request.POST.get('note', '')
    try:
        amount = request.POST.get('amount', '0').replace(',', '')
        services.perform_wallet_operation(
            wallet=wallet, op_type=op_type, amount=amount,
            note=note, actor=request.user, request=request)
        messages.success(request, 'تراکنش کیف پول با موفقیت ثبت شد.')
    except (ValueError, Exception) as exc:
        messages.error(request, f'خطا در تراکنش: {exc}')


@superuser_required
def wallets(request):
    """لیست کیف پول‌ها و انجام عملیات مالی"""
    rule = SystemRule.load()
    if not rule.wallet_enabled:
        messages.warning(request, 'کیف پول از قوانین سیستم غیرفعال است.')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'create_operation':
            user_id = request.POST.get('user_id')
            role_code = request.POST.get('role_code')
            try:
                if user_id:
                    user = get_object_or_404(User, id=user_id)
                    wallet = services.get_or_create_wallet(user=user)
                elif role_code:
                    wallet = services.get_or_create_wallet(role=role_code)
                else:
                    raise ValueError('انتخاب کاربر یا نقش الزامی است.')
                _handle_wallet_operation(request, wallet)
            except (ValueError, Exception) as exc:
                messages.error(request, str(exc))
            return redirect('system_control:wallets')

        elif action == 'toggle_freeze':
            wallet = Wallet.objects.filter(id=request.POST.get('wallet_id')).first()
            if wallet:
                wallet.is_frozen = not wallet.is_frozen
                wallet.save(update_fields=['is_frozen'])
                state = 'مسدود' if wallet.is_frozen else 'آزاد'
                services.log_action(
                    request.user, 'toggle_wallet_freeze', target=wallet.owner_display(),
                    description=f'وضعیت: {state}', request=request)
                messages.success(request, f'کیف پول {state} شد.')
            return redirect('system_control:wallets')

    user_wallets = Wallet.objects.filter(user__isnull=False).select_related('user')
    role_wallets = Wallet.objects.filter(role__isnull=False)
    totals = Wallet.objects.aggregate(total_balance=Sum('balance'))

    return render(request, 'system_control/wallets.html', {
        'user_wallets': user_wallets,
        'role_wallets': role_wallets,
        'total_balance': totals['total_balance'] or 0,
        'all_roles': _get_all_roles(),
        'all_users': User.objects.all().order_by('username'),
        'wallet_enabled': rule.wallet_enabled,
    })


@superuser_required
def wallet_detail(request, user_id):
    """جزئیات کیف پول کاربر"""
    user = get_object_or_404(User, id=user_id)
    wallet = services.get_or_create_wallet(user=user)

    if request.method == 'POST':
        if request.POST.get('action') == 'wallet_operation':
            _handle_wallet_operation(request, wallet)
        elif request.POST.get('action') == 'toggle_freeze':
            wallet.is_frozen = not wallet.is_frozen
            wallet.save(update_fields=['is_frozen'])
            services.log_action(
                request.user, 'toggle_wallet_freeze', target=wallet.owner_display(),
                request=request)
        return redirect('system_control:wallet_detail', user_id=user.id)

    return render(request, 'system_control/wallet_detail.html', {
        'wallet': wallet,
        'owner_user': user,
        'transactions': wallet.transactions.select_related('created_by')[:100],
    })


@superuser_required
def role_wallet_detail(request, role_code):
    """جزئیات کیف پول مشترک نقش"""
    wallet = services.get_or_create_wallet(role=role_code)

    if request.method == 'POST':
        if request.POST.get('action') == 'wallet_operation':
            _handle_wallet_operation(request, wallet)
        elif request.POST.get('action') == 'toggle_freeze':
            wallet.is_frozen = not wallet.is_frozen
            wallet.save(update_fields=['is_frozen'])
            services.log_action(
                request.user, 'toggle_wallet_freeze', target=wallet.owner_display(),
                request=request)
        return redirect('system_control:role_wallet_detail', role_code=role_code)

    return render(request, 'system_control/wallet_detail.html', {
        'wallet': wallet,
        'owner_role': role_label(role_code),
        'transactions': wallet.transactions.select_related('created_by')[:100],
    })


# =========================================================
# ۶- نظارت امنیتی
# =========================================================
@superuser_required
def security_dashboard(request):
    """داشبورد نظارت امنیتی: رویدادهای امنیتی و تهدیدات"""
    hours = int(request.GET.get('hours', 24))
    
    # Get security summary
    summary = SecurityMonitor.get_security_summary(hours)
    
    # Get recent events
    recent_events = SecurityMonitor.get_recent_security_events(hours)
    
    # Get critical and high severity events
    critical_events = recent_events.filter(severity='critical')[:20]
    high_events = recent_events.filter(severity='high')[:20]
    
    # Get login attempts statistics
    from .security_monitor import LoginAttempt
    from django.utils import timezone
    from datetime import timedelta
    
    cutoff = timezone.now() - timedelta(hours=hours)
    login_attempts = LoginAttempt.objects.filter(created_at__gte=cutoff)
    failed_logins = login_attempts.filter(success=False).count()
    successful_logins = login_attempts.filter(success=True).count()
    
    context = {
        'summary': summary,
        'recent_events': recent_events[:50],
        'critical_events': critical_events,
        'high_events': high_events,
        'failed_logins': failed_logins,
        'successful_logins': successful_logins,
        'hours': hours,
    }
    return render(request, 'system_control/security_dashboard.html', context)
