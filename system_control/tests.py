from unittest.mock import patch

from django.test import TestCase

from accounts.models import User
from .models import (
    SystemRule, Role, SystemModule, ModuleAccessRule, UserModuleAccess,
    IssuanceQuota, Wallet,
)
from . import services


class ModuleAccessTests(TestCase):
    def setUp(self):
        services.ensure_default_modules()
        self.rule = SystemRule.load()
        self.superuser = User.objects.create_user(
            username='boss', password='x', is_superuser=True)
        self.employee = User.objects.create_user(
            username='emp1', password='x', role='employee')

    def test_modules_seeded(self):
        self.assertGreaterEqual(SystemModule.objects.count(), 13)

    def test_superuser_always_allowed(self):
        module = SystemModule.objects.get(key='issuance')
        module.is_locked = True
        module.save()
        allowed, _ = services.get_module_access(self.superuser, module)
        self.assertTrue(allowed)

    def test_full_module_lock_blocks_user(self):
        module = SystemModule.objects.get(key='issuance')
        module.is_locked = True
        module.save()
        allowed, reason = services.get_module_access(self.employee, module)
        self.assertFalse(allowed)
        self.assertIn('قفل', reason)

    def test_role_lock_blocks_user(self):
        module = SystemModule.objects.get(key='report')
        ModuleAccessRule.objects.create(module=module, role='employee', is_locked=True)
        allowed, reason = services.get_module_access(self.employee, module)
        self.assertFalse(allowed)

    def test_user_allow_override_wins(self):
        module = SystemModule.objects.get(key='report')
        ModuleAccessRule.objects.create(module=module, role='employee', is_locked=True)
        UserModuleAccess.objects.create(
            module=module, user=self.employee, mode='allow')
        allowed, _ = services.get_module_access(self.employee, module)
        self.assertTrue(allowed)

    def test_user_deny_override(self):
        module = SystemModule.objects.get(key='report')
        UserModuleAccess.objects.create(
            module=module, user=self.employee, mode='deny')
        allowed, _ = services.get_module_access(self.employee, module)
        self.assertFalse(allowed)

    def test_lock_all_modules_rule(self):
        self.rule.lock_all_modules = True
        self.rule.save()
        allowed, reason = services.user_can_access_path(self.employee, '/issuance/create_new/')
        self.assertFalse(allowed)

    def test_path_resolution(self):
        module = services.get_module_for_path('/customers/some/page/')
        self.assertEqual(module.key, 'customers')

    def test_unknown_path_allowed(self):
        allowed, _ = services.user_can_access_path(self.employee, '/accounts/profile/')
        self.assertTrue(allowed)


class QuotaTests(TestCase):
    def setUp(self):
        self.rule = SystemRule.load()
        self.superuser = User.objects.create_user(
            username='boss', password='x', is_superuser=True)
        self.employee = User.objects.create_user(
            username='emp1', password='x', role='employee')

    def test_superuser_exempt(self):
        ok, msg, _ = services.check_issuance_allowed(self.superuser)
        self.assertTrue(ok)

    def test_no_quota_means_unlimited(self):
        ok, msg, statuses = services.check_issuance_allowed(self.employee)
        self.assertTrue(ok)
        self.assertEqual(statuses, [])

    def _patched_count(self, count):
        """ماک کردن شمارش بارنامه‌ها"""
        return patch.object(
            services, 'count_issued_bijaks', return_value=count)

    def test_default_daily_limit_enforced(self):
        self.rule.default_daily_limit = 3
        self.rule.save()
        with self._patched_count(3):
            ok, msg, statuses = services.check_issuance_allowed(self.employee)
            self.assertFalse(ok)
            self.assertIn('تکمیل شده', msg)
        with self._patched_count(2):
            ok, _, statuses = services.check_issuance_allowed(self.employee)
            self.assertTrue(ok)
            self.assertEqual(statuses[0]['remaining'], 1)

    def test_role_quota(self):
        IssuanceQuota.objects.create(
            scope='role', role='employee', period='monthly', max_count=10)
        with self._patched_count(10):
            ok, msg, statuses = services.check_issuance_allowed(self.employee)
            self.assertFalse(ok)
        with self._patched_count(4):
            ok, _, statuses = services.check_issuance_allowed(self.employee)
            self.assertTrue(ok)
            monthly = [s for s in statuses if s['period'] == 'monthly'][0]
            self.assertEqual(monthly['remaining'], 6)

    def test_user_quota_precedence(self):
        IssuanceQuota.objects.create(
            scope='role', role='employee', period='monthly', max_count=10)
        IssuanceQuota.objects.create(
            scope='user', user=self.employee, period='monthly', max_count=2)
        with self._patched_count(1):
            ok, _, statuses = services.check_issuance_allowed(self.employee)
            self.assertTrue(ok)
            monthly = [s for s in statuses if s['period'] == 'monthly'][0]
            self.assertEqual(monthly['limit'], 2)
            self.assertIn('اختصاصی', monthly['source'])

    def test_zero_quota_blocks_all(self):
        IssuanceQuota.objects.create(
            scope='user', user=self.employee, period='total', max_count=0)
        with self._patched_count(0):
            ok, msg, _ = services.check_issuance_allowed(self.employee)
            self.assertFalse(ok)

    def test_disable_enforcement(self):
        self.rule.enforce_quotas = False
        self.rule.save()
        IssuanceQuota.objects.create(
            scope='role', role='employee', period='daily', max_count=0)
        with self._patched_count(5):
            ok, _, statuses = services.check_issuance_allowed(self.employee)
            self.assertTrue(ok)
            self.assertEqual(statuses, [])


class CustomRoleTests(TestCase):
    def test_resolve_effective_role(self):
        from accounts.decorators import resolve_effective_role
        self.assertEqual(resolve_effective_role('employee'), 'employee')
        Role.objects.create(code='supervisor', name='سرپرست', base_role='manager')
        self.assertEqual(resolve_effective_role('supervisor'), 'manager')

    def test_all_roles_includes_custom(self):
        Role.objects.create(code='supervisor', name='سرپرست', base_role='manager')
        codes = [code for code, _ in services.all_roles()]
        self.assertIn('supervisor', codes)

    def test_role_label(self):
        Role.objects.create(code='supervisor', name='سرپرست', base_role='manager')
        self.assertEqual(services.role_label('supervisor'), 'سرپرست')
        self.assertEqual(services.role_label('manager'), 'مدیریت')


class WalletTests(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_user(
            username='boss', password='x', is_superuser=True)
        self.employee = User.objects.create_user(
            username='emp1', password='x', role='employee')

    def test_deposit_withdraw(self):
        wallet = services.get_or_create_wallet(user=self.employee)
        tx = services.perform_wallet_operation(
            wallet=wallet, op_type='deposit', amount=100000,
            note='شارژ اولیه', actor=self.superuser)
        self.assertEqual(tx.balance_after, 100000)
        wallet.refresh_from_db()
        self.assertEqual(wallet.balance, 100000)

        services.perform_wallet_operation(
            wallet=wallet, op_type='withdraw', amount=40000,
            actor=self.superuser)
        wallet.refresh_from_db()
        self.assertEqual(wallet.balance, 60000)
        self.assertEqual(wallet.transactions.count(), 2)

    def test_insufficient_funds(self):
        wallet = services.get_or_create_wallet(user=self.employee)
        with self.assertRaises(ValueError):
            services.perform_wallet_operation(
                wallet=wallet, op_type='withdraw', amount=100,
                actor=self.superuser)

    def test_frozen_wallet(self):
        wallet = services.get_or_create_wallet(user=self.employee)
        wallet.is_frozen = True
        wallet.save()
        with self.assertRaises(ValueError):
            services.perform_wallet_operation(
                wallet=wallet, op_type='deposit', amount=100,
                actor=self.superuser)

    def test_adjust_sets_balance(self):
        wallet = services.get_or_create_wallet(user=self.employee)
        services.perform_wallet_operation(
            wallet=wallet, op_type='adjust', amount=500, actor=self.superuser)
        wallet.refresh_from_db()
        self.assertEqual(wallet.balance, 500)

    def test_role_wallet(self):
        wallet = services.get_or_create_wallet(role='employee')
        services.perform_wallet_operation(
            wallet=wallet, op_type='deposit', amount=1000, actor=self.superuser)
        wallet.refresh_from_db()
        self.assertEqual(wallet.balance, 1000)


class ViewTests(TestCase):
    """دسترسی به پنل فقط برای سوپر ادمین و رندر صحیح صفحات"""

    PAGES = [
        '/system-control/',
        '/system-control/users/',
        '/system-control/roles/',
        '/system-control/modules/',
        '/system-control/quotas/',
        '/system-control/wallets/',
    ]

    def setUp(self):
        services.ensure_default_modules()
        self.superuser = User.objects.create_user(
            username='boss', password='secret123', is_superuser=True)
        self.employee = User.objects.create_user(
            username='emp1', password='secret123', role='employee')

    def test_anonymous_redirected_to_login(self):
        response = self.client.get('/system-control/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_non_superuser_forbidden(self):
        self.client.login(username='emp1', password='secret123')
        response = self.client.get('/system-control/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('forbidden', response.url)

    def test_pages_render_for_superuser(self):
        self.client.login(username='boss', password='secret123')
        for page in self.PAGES:
            with self.subTest(page=page):
                response = self.client.get(page)
                self.assertEqual(response.status_code, 200)

    def test_user_detail_renders(self):
        self.client.login(username='boss', password='secret123')
        response = self.client.get(
            f'/system-control/users/{self.employee.id}/')
        self.assertEqual(response.status_code, 200)

    def test_create_user_via_panel(self):
        self.client.login(username='boss', password='secret123')
        response = self.client.post('/system-control/users/', {
            'action': 'create_user',
            'username': 'newemp',
            'first_name': 'نیو',
            'role': 'employee',
            'password1': 'Strong#Pass99',
            'password2': 'Strong#Pass99',
        })
        created = User.objects.filter(username='newemp').first()
        self.assertIsNotNone(created)
        self.assertEqual(created.role, 'employee')
        self.assertTrue(created.check_password('Strong#Pass99'))
        self.assertRedirects(
            response, f'/system-control/users/{created.id}/',
            fetch_redirect_response=False)

    def test_middleware_blocks_locked_module(self):
        module = SystemModule.objects.get(key='report')
        module.is_locked = True
        module.save()
        self.client.login(username='emp1', password='secret123')
        response = self.client.get('/report/')
        self.assertEqual(response.status_code, 403)

    def test_middleware_allows_unlocked_module(self):
        self.client.login(username='emp1', password='secret123')
        # مسیری که به هیچ ماژولی وصل نیست باید آزاد باشد
        response = self.client.get('/nonexistent-path/')
        self.assertNotEqual(response.status_code, 403)
