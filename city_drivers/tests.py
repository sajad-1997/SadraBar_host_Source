from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import RolePermission, User
from customers.models import Customer
from drivers.models import Driver

from .models import (
    CommissionDebt,
    DriverAttendance,
    DriverLocation,
    RateCard,
    ServiceRequest,
    UrbanService,
)
from . import services
from .permissions import has_urban_permission


def make_driver(name='علی رضایی', phone='09120000001'):
    return Driver.objects.create(
        name=name, national_id=f'{abs(hash(name)) % 10**10:010d}',
        certificate=f'CERT-{abs(hash(name)) % 10**6:06d}', phone=phone)


class FareCalculationTests(TestCase):
    def setUp(self):
        self.rate = RateCard.objects.create(
            title='تست', base_fare=20000, per_km_fare=8000,
            minimum_fare=30000, commission_percent=Decimal('10.00'))

    def test_fare_calculation(self):
        # (20000 پایه + 8000 * 10) = 100000
        self.assertEqual(self.rate.calculate_fare(10), Decimal('100000'))

    def test_minimum_fare_applies(self):
        # 20000 + 8000 * 1 = 28000 < حداقل 30000
        self.assertEqual(self.rate.calculate_fare(1), Decimal('30000'))

    def test_commission(self):
        self.assertEqual(self.rate.commission_for(Decimal('100000')), Decimal('10000'))


class PermissionTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username='admin1', password='x', role='admin')
        self.manager = User.objects.create_user(username='mgr1', password='x', role='manager')
        self.employee = User.objects.create_user(username='emp1', password='x', role='employee')
        self.employee_perm = RolePermission.objects.create(role='employee')

    def test_admin_full_access(self):
        self.assertTrue(has_urban_permission(self.admin, 'can_urban_view_requests'))
        self.assertTrue(has_urban_permission(self.admin, 'anything_missing'))

    def test_manager_permission_based(self):
        self.assertFalse(has_urban_permission(self.manager, 'can_urban_view_requests'))
        perm = RolePermission.objects.create(role='manager', can_urban_view_requests=True)
        self.manager.refresh_from_db()
        self.assertTrue(has_urban_permission(self.manager, 'can_urban_view_requests'))
        self.assertFalse(has_urban_permission(self.manager, 'can_urban_view_locations'))
        perm.delete()

    def test_employee_permission_based(self):
        self.assertFalse(has_urban_permission(self.employee, 'can_urban_view_requests'))
        self.employee_perm.can_urban_view_requests = True
        self.employee_perm.save()
        self.assertTrue(has_urban_permission(self.employee, 'can_urban_view_requests'))


class ServiceFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='u1', password='x', role='manager')
        self.customer = Customer.objects.create(name='مشتری تست', address='تهران')
        self.driver = make_driver()
        self.service = UrbanService.objects.create(title='مسافری شهری')
        self.rate = RateCard.objects.create(
            title='تست', base_fare=20000, per_km_fare=8000,
            minimum_fare=30000, commission_percent=Decimal('10.00'))
        self.sr = ServiceRequest.objects.create(
            tracking_code=services.generate_tracking_code(),
            customer=self.customer, service=self.service, rate_card=self.rate,
            origin_address='مبدأ', destination_address='مقصد',
            distance_km=Decimal('10.00'), created_by=self.user)

    def test_assign_updates_location(self):
        services.assign_request(self.sr, self.driver, user=self.user)
        self.sr.refresh_from_db()
        # تخصیص فقط راننده را تعیین می‌کند؛ وضعیت با قبول راننده به
        # «تخصیص یافته» تغییر می‌کند
        self.assertEqual(self.sr.status, ServiceRequest.Status.PENDING)
        self.assertEqual(self.sr.assigned_driver, self.driver)
        loc = DriverLocation.objects.get(driver=self.driver)
        self.assertEqual(loc.status, DriverLocation.Status.BUSY)
        self.assertEqual(loc.current_request, self.sr)

    def test_driver_accept_sets_assigned(self):
        services.assign_request(self.sr, self.driver, user=self.user)
        # قبول سرویس توسط راننده: وضعیت به «تخصیص یافته» تغییر می‌کند
        services.change_status(self.sr, ServiceRequest.Status.ASSIGNED,
                               note='قبول سرویس توسط راننده')
        self.sr.refresh_from_db()
        self.assertEqual(self.sr.status, ServiceRequest.Status.ASSIGNED)
        self.assertTrue(self.sr.status_logs.filter(
            note__icontains='قبول سرویس').exists())

    def test_done_creates_commission_debt_and_frees_driver(self):
        services.assign_request(self.sr, self.driver, user=self.user)
        services.change_status(self.sr, ServiceRequest.Status.IN_PROGRESS, user=self.user)
        services.change_status(self.sr, ServiceRequest.Status.DONE, user=self.user)
        self.sr.refresh_from_db()

        # کرایه = 20000 + 8000*10 = 100000، کمیسیون 10% = 10000
        self.assertEqual(self.sr.fare_amount, Decimal('100000'))
        self.assertEqual(self.sr.commission_amount, Decimal('10000'))

        debt = CommissionDebt.objects.get(driver=self.driver, service_request=self.sr)
        self.assertEqual(debt.amount, Decimal('10000'))
        self.assertFalse(debt.is_settled)

        loc = DriverLocation.objects.get(driver=self.driver)
        self.assertEqual(loc.status, DriverLocation.Status.IDLE)
        self.assertIsNone(loc.current_request)

    def test_settle_debt_marks_commission_paid(self):
        services.assign_request(self.sr, self.driver, user=self.user)
        services.change_status(self.sr, ServiceRequest.Status.DONE, user=self.user)
        debt = CommissionDebt.objects.get(driver=self.driver, service_request=self.sr)
        services.settle_debt(debt, debt.amount, user=self.user)
        debt.refresh_from_db()
        self.sr.refresh_from_db()
        self.assertTrue(debt.is_settled)
        self.assertTrue(self.sr.commission_paid)

    def test_attendance_update_or_create(self):
        from .utils import jalali_today
        services.set_attendance(self.driver, jalali_today(), DriverAttendance.Status.PRESENT)
        services.set_attendance(self.driver, jalali_today(), DriverAttendance.Status.ABSENT)
        self.assertEqual(
            DriverAttendance.objects.filter(driver=self.driver).count(), 1)
        self.assertEqual(
            DriverAttendance.objects.get(driver=self.driver).status,
            DriverAttendance.Status.ABSENT)


class ViewAccessTests(TestCase):
    """بررسی کنترل دسترسی صفحات ماژول"""

    def setUp(self):
        self.manager = User.objects.create_user(username='mgr2', password='x', role='manager')
        RolePermission.objects.create(role='manager', can_urban_access_dashboard=True)

    def test_dashboard_requires_permission(self):
        # کارمندی که هیچ مجوز شهری ندارد (پیش‌فرض False)، به داشبورد دسترسی ندارد
        User.objects.create_user(username='emp9', password='x', role='employee')
        self.client.login(username='emp9', password='x')
        response = self.client.get(reverse('city_drivers:dashboard'))
        self.assertEqual(response.status_code, 403)

    def test_dashboard_with_permission(self):
        self.client.login(username='mgr2', password='x')
        response = self.client.get(reverse('city_drivers:dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_other_sections_need_their_own_permission(self):
        self.client.login(username='mgr2', password='x')
        # داشبورد مجاز است اما مشتریان نه
        response = self.client.get(reverse('city_drivers:urban_customer_list'))
        self.assertEqual(response.status_code, 403)

        perm = RolePermission.objects.get(role='manager')
        perm.can_urban_view_customers = True
        perm.can_urban_view_requests = True
        perm.save()
        response = self.client.get(reverse('city_drivers:urban_customer_list'))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('city_drivers:urban_request_list'))
        self.assertEqual(response.status_code, 200)

    def test_dashboard_ok_with_permission(self):
        perm = RolePermission.objects.get(role='manager')
        perm.can_urban_view_rates = True
        perm.save()
        self.client.login(username='mgr2', password='x')
        response = self.client.get(reverse('city_drivers:urban_rate_list'))
        self.assertEqual(response.status_code, 200)

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(reverse('city_drivers:dashboard'))
        self.assertEqual(response.status_code, 302)
