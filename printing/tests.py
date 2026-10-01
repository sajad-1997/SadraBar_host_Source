"""
Tests for printing app.
Coverage target: >= 70%
"""
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal

from issuance.models import Bijak
from drivers.models import Driver
from customers.models import Customer
from fleet.models import Vehicle
from cargo.models import Cargo, City, Province
from .models import WaybillPrintOTP
from .serializers import (
    WaybillPrintOTPSerializer,
    RequestOTPSerializer,
    VerifyOTPSerializer
)
from accounts.decorators import (
    can_print_without_approval,
    can_use_digital_stamp,
    is_manager_or_admin,
)
from accounts.models import RolePermission

User = get_user_model()



def _make_cities():
    """ساخت شهرهای آزمایشی برای مبدأ/مقصد محموله (Cargo به City متصل است)."""
    province = Province.objects.create(name='تهران', slug='tehran-province')
    tehran = City.objects.create(province=province, name='تهران', slug='tehran')
    mashhad = City.objects.create(province=province, name='مشهد', slug='mashhad')
    return tehran, mashhad


class PrintingModelTests(TestCase):
    """Tests for WaybillPrintOTP model."""

    def setUp(self) -> None:
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.customer = Customer.objects.create(
            name='Test Customer',
            national_id='1234567890'
        )
        self.driver = Driver.objects.create(
            name='Test Driver',
            national_id='0987654321',
            phone='09123456789'
        )
        self.vehicle = Vehicle.objects.create(
            driver=self.driver,
            license_plate_two_digit='12',
            license_plate_alphabet='A',
            license_plate_three_digit='345',
            license_plate_series='67',
            type='vant pikan mamoli'
        )
        tehran, mashhad = _make_cities()
        self.cargo = Cargo.objects.create(name='Test Cargo', weight=1000, origin=tehran, destination=mashhad)
        self.bijak = Bijak.objects.create(
            tracking_code='123456789',
            value=Decimal('1000000'),
            insurance=Decimal('500000'),
            freight=Decimal('200000'),
            total_fare=Decimal('200000'),
            sender=self.customer,
            receiver=self.customer,
            driver=self.driver,
            vehicle=self.vehicle,
            cargo=self.cargo,
            created_by=self.user
        )

    def test_waybill_print_otp_creation(self) -> None:
        """Test WaybillPrintOTP object creation."""
        otp_record = WaybillPrintOTP.objects.create(bijak=self.bijak)
        self.assertEqual(otp_record.print_count, 0)
        self.assertFalse(otp_record.is_verified)
        self.assertIsNone(otp_record.otp_code)

    def test_waybill_print_otp_str(self) -> None:
        """Test WaybillPrintOTP string representation."""
        otp_record = WaybillPrintOTP.objects.create(
            bijak=self.bijak,
            print_count=2
        )
        expected = f"{self.bijak.tracking_code} - چاپ 2 بار"
        self.assertIn('چاپ', str(otp_record))

    def test_is_otp_expired_no_created_at(self) -> None:
        """Test OTP expiration when no created_at."""
        otp_record = WaybillPrintOTP.objects.create(bijak=self.bijak)
        self.assertTrue(otp_record.is_otp_expired())

    def test_is_otp_expired_not_expired(self) -> None:
        """Test OTP not expired within 2 minutes."""
        otp_record = WaybillPrintOTP.objects.create(
            bijak=self.bijak,
            otp_created_at=timezone.now()
        )
        self.assertFalse(otp_record.is_otp_expired())

    def test_is_otp_expired_expired(self) -> None:
        """Test OTP expired after 2 minutes."""
        from datetime import timedelta
        past_time = timezone.now() - timedelta(seconds=121)
        otp_record = WaybillPrintOTP.objects.create(
            bijak=self.bijak
        )
        # Update using direct SQL to avoid mock issues
        WaybillPrintOTP.objects.filter(pk=otp_record.pk).update(
            otp_created_at=past_time
        )
        otp_record.refresh_from_db()
        self.assertTrue(otp_record.is_otp_expired())


class PrintingSerializerTests(TestCase):
    """Tests for printing serializers."""

    def setUp(self) -> None:
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.customer = Customer.objects.create(
            name='Test Customer',
            national_id='1234567890'
        )
        self.driver = Driver.objects.create(
            name='Test Driver',
            national_id='0987654321',
            phone='09123456789'
        )
        self.vehicle = Vehicle.objects.create(
            driver=self.driver,
            license_plate_two_digit='12',
            license_plate_alphabet='A',
            license_plate_three_digit='345',
            license_plate_series='67',
            type='vant pikan mamoli'
        )
        tehran, mashhad = _make_cities()
        self.cargo = Cargo.objects.create(name='Test Cargo', weight=1000, origin=tehran, destination=mashhad)
        self.bijak = Bijak.objects.create(
            tracking_code='123456789',
            value=Decimal('1000000'),
            insurance=Decimal('500000'),
            freight=Decimal('200000'),
            total_fare=Decimal('200000'),
            sender=self.customer,
            receiver=self.customer,
            driver=self.driver,
            vehicle=self.vehicle,
            cargo=self.cargo,
            created_by=self.user
        )
        self.otp_record = WaybillPrintOTP.objects.create(
            bijak=self.bijak,
            print_count=1,
            is_verified=True
        )

    def test_waybill_print_otp_serializer(self) -> None:
        """Test WaybillPrintOTPSerializer serialization."""
        serializer = WaybillPrintOTPSerializer(self.otp_record)
        data = serializer.data
        self.assertEqual(data['waybill_number'], '123456789')
        self.assertEqual(data['print_count'], 1)
        self.assertTrue(data['is_verified'])
        self.assertIn('is_expired', data)

    def test_request_otp_serializer_valid(self) -> None:
        """Test RequestOTPSerializer with valid data."""
        serializer = RequestOTPSerializer(data={'bijak_id': self.bijak.id})
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['bijak_id'], self.bijak.id)

    def test_request_otp_serializer_invalid_bijak(self) -> None:
        """Test RequestOTPSerializer with invalid bijak_id."""
        serializer = RequestOTPSerializer(data={'bijak_id': 99999})
        self.assertFalse(serializer.is_valid())
        self.assertIn('bijak_id', serializer.errors)

    def test_verify_otp_serializer_valid(self) -> None:
        """Test VerifyOTPSerializer with valid data."""
        serializer = VerifyOTPSerializer(
            data={'bijak_id': self.bijak.id, 'otp_code': '123456'}
        )
        self.assertTrue(serializer.is_valid())

    def test_verify_otp_serializer_invalid_length(self) -> None:
        """Test VerifyOTPSerializer with invalid otp_code length."""
        serializer = VerifyOTPSerializer(
            data={'bijak_id': self.bijak.id, 'otp_code': '123'}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('otp_code', serializer.errors)


class PrintingViewTests(TestCase):
    """Tests for printing views."""

    def setUp(self) -> None:
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.customer = Customer.objects.create(
            name='Test Customer',
            national_id='1234567890'
        )
        self.driver = Driver.objects.create(
            name='Test Driver',
            national_id='0987654321',
            phone='09123456789'
        )
        self.vehicle = Vehicle.objects.create(
            driver=self.driver,
            license_plate_two_digit='12',
            license_plate_alphabet='A',
            license_plate_three_digit='345',
            license_plate_series='67',
            type='vant pikan mamoli'
        )
        tehran, mashhad = _make_cities()
        self.cargo = Cargo.objects.create(name='Test Cargo', weight=1000, origin=tehran, destination=mashhad)
        self.bijak = Bijak.objects.create(
            tracking_code='123456789',
            value=Decimal('1000000'),
            insurance=Decimal('500000'),
            freight=Decimal('200000'),
            total_fare=Decimal('200000'),
            sender=self.customer,
            receiver=self.customer,
            driver=self.driver,
            vehicle=self.vehicle,
            cargo=self.cargo,
            created_by=self.user
        )
        self.login_url = reverse('login')

    def test_request_print_permission_login_required(self) -> None:
        """Test that request_print_permission requires login."""
        response = self.client.get(reverse('printing:request_print'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(self.login_url, response.url)

    def test_request_print_permission_get(self) -> None:
        """Test GET request to request_print_permission."""
        self.client.force_login(self.user)
        response = self.client.get(reverse('printing:request_print'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'printing/request_print.html')

    @patch('printing.views.send_otp_via_smsir')
    def test_request_print_permission_post_first_time(
        self,
        mock_send: MagicMock
    ) -> None:
        """Test POST request for first-time print."""
        mock_send.return_value = (True, 'Success')
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('printing:request_print'),
            {'waybill_number': '123456789'}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('printing:verify_otp'))

    def test_request_print_permission_bijak_not_found(self) -> None:
        """Test request with non-existent bijak."""
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('printing:request_print'),
            {'waybill_number': 'INVALID'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'بارنامه یافت نشد')

    def test_request_print_permission_no_access(self) -> None:
        """Test request for bijak created by another user."""
        other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        bijak_other = Bijak.objects.create(
            tracking_code='987654321',
            value=Decimal('1000000'),
            insurance=Decimal('500000'),
            freight=Decimal('200000'),
            total_fare=Decimal('200000'),
            sender=self.customer,
            receiver=self.customer,
            driver=self.driver,
            vehicle=self.vehicle,
            cargo=self.cargo,
            created_by=other_user
        )
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('printing:request_print'),
            {'waybill_number': '987654321'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'شما دسترسی به این بارنامه ندارید')

    def test_verify_otp_login_required(self) -> None:
        """Test that verify_otp requires login."""
        response = self.client.get(reverse('printing:verify_otp'))
        self.assertEqual(response.status_code, 302)

    def test_verify_otp_no_pending_bijak(self) -> None:
        """Test verify_otp without pending bijak in session."""
        self.client.force_login(self.user)
        response = self.client.get(reverse('printing:verify_otp'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('printing:request_print'))


class PrintingAPITests(TestCase):
    """Tests for printing API endpoints."""

    def setUp(self) -> None:
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='apiuser',
            password='testpass123',
            email='api@example.com'
        )
        self.customer = Customer.objects.create(
            name='API Customer',
            national_id='1111111111'
        )
        self.driver = Driver.objects.create(
            name='API Driver',
            national_id='2222222222',
            phone='09111111111'
        )
        self.vehicle = Vehicle.objects.create(
            driver=self.driver,
            license_plate_two_digit='11',
            license_plate_alphabet='B',
            license_plate_three_digit='222',
            license_plate_series='33',
            type='vant pikan mamoli'
        )
        tehran, mashhad = _make_cities()
        self.cargo = Cargo.objects.create(name='API Cargo', weight=500, origin=tehran, destination=mashhad)
        self.bijak = Bijak.objects.create(
            tracking_code='API123456',
            value=Decimal('1000000'),
            insurance=Decimal('500000'),
            freight=Decimal('200000'),
            total_fare=Decimal('200000'),
            sender=self.customer,
            receiver=self.customer,
            driver=self.driver,
            vehicle=self.vehicle,
            cargo=self.cargo,
            created_by=self.user
        )
        self.api_request_url = reverse('printing:api_request_otp')
        self.api_verify_url = reverse('printing:api_verify_otp')

    def test_api_request_otp_unauthenticated(self) -> None:
        """Test API endpoint without authentication."""
        response = self.client.post(
            self.api_request_url,
            {'bijak_id': self.bijak.id},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)

    @patch('printing.views.send_otp_via_smsir')
    def test_api_request_otp_success(self, mock_send: MagicMock) -> None:
        """Test successful API OTP request."""
        mock_send.return_value = (True, 'Success')
        self.client.force_login(self.user)

        response = self.client.post(
            self.api_request_url,
            {'bijak_id': self.bijak.id},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertTrue(data['need_verification'])

    def test_api_request_otp_invalid_bijak(self) -> None:
        """Test API OTP request with invalid bijak_id."""
        self.client.force_login(self.user)
        response = self.client.post(
            self.api_request_url,
            {'bijak_id': 99999},
            content_type='application/json'
        )
        # سریالایزر وجود بارنامه را اعتبارسنجی می‌کند و خطای ۴۰۰ برمی‌گرداند
        self.assertEqual(response.status_code, 400)

    def test_api_request_otp_no_access(self) -> None:
        """Test API OTP request for bijak without access."""
        other_user = User.objects.create_user(
            username='otherapiuser',
            password='testpass123'
        )
        bijak_other = Bijak.objects.create(
            tracking_code='API987654',
            value=Decimal('1000000'),
            insurance=Decimal('500000'),
            freight=Decimal('200000'),
            total_fare=Decimal('200000'),
            sender=self.customer,
            receiver=self.customer,
            driver=self.driver,
            vehicle=self.vehicle,
            cargo=self.cargo,
            created_by=other_user
        )
        self.client.force_login(self.user)
        response = self.client.post(
            self.api_request_url,
            {'bijak_id': bijak_other.id},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)

    def test_api_verify_otp_unauthenticated(self) -> None:
        """Test API verify endpoint without authentication."""
        response = self.client.post(
            self.api_verify_url,
            {'bijak_id': self.bijak.id, 'otp_code': '123456'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)

    def test_api_verify_otp_no_record(self) -> None:
        """Test API verify without OTP record."""
        self.client.force_login(self.user)
        response = self.client.post(
            self.api_verify_url,
            {'bijak_id': self.bijak.id, 'otp_code': '123456'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 404)

    @patch('printing.views.send_otp_via_smsir')
    def test_api_full_flow(self, mock_send: MagicMock) -> None:
        """Test complete API flow: request and verify OTP."""
        mock_send.return_value = (True, 'Success')
        self.client.force_login(self.user)

        # Request OTP
        response = self.client.post(
            self.api_request_url,
            {'bijak_id': self.bijak.id},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])

        # Get the OTP code from database
        otp_record = WaybillPrintOTP.objects.get(bijak=self.bijak)

        # Verify OTP
        response = self.client.post(
            self.api_verify_url,
            {'bijak_id': self.bijak.id, 'otp_code': otp_record.otp_code},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        otp_record.refresh_from_db()
        self.assertEqual(otp_record.print_count, 1)


class PrintPermissionHelperTests(TestCase):
    """تست هلپرهای مجوز چاپ: نقش «مدیریت» و «مدیر کل» همیشه مجاز هستند."""

    def setUp(self) -> None:
        self.manager = User.objects.create_user(
            username='helpermanager', password='testpass123', role='manager')
        self.admin_user = User.objects.create_user(
            username='helperadmin', password='testpass123', role='admin')
        self.employee = User.objects.create_user(
            username='helperemployee', password='testpass123', role='employee')
        self.driver_user = User.objects.create_user(
            username='helperdriver', password='testpass123', role='driver')

    def test_manager_and_admin_always_allowed(self) -> None:
        """مدیریت و مدیر کل بدون نیاز به مجوز، همیشه مجاز به چاپ هستند."""
        self.assertTrue(can_print_without_approval(self.manager))
        self.assertTrue(can_print_without_approval(self.admin_user))
        self.assertTrue(can_use_digital_stamp(self.manager))
        self.assertTrue(can_use_digital_stamp(self.admin_user))
        self.assertTrue(is_manager_or_admin(self.manager))
        self.assertTrue(is_manager_or_admin(self.admin_user))

    def test_employee_requires_role_permission(self) -> None:
        """کارمند فقط با مجوز فعال‌شده توسط مدیریت مجاز است."""
        self.assertFalse(can_print_without_approval(self.employee))
        RolePermission.objects.create(
            role='employee', can_print_without_approval=True)
        self.assertTrue(can_print_without_approval(self.employee))
        # راننده در هیچ شرایطی مجاز نیست
        self.assertFalse(can_print_without_approval(self.driver_user))
        self.assertFalse(can_use_digital_stamp(self.driver_user))

    def test_unauthenticated_user_denied(self) -> None:
        """کاربر واردنشده مجاز نیست."""
        self.assertFalse(can_print_without_approval(None))
        self.assertFalse(is_manager_or_admin(None))

    def test_superuser_always_allowed(self) -> None:
        """ابرکاربر همیشه مجاز است (حتی اگر نقش او کارمند باشد)."""
        superuser = User.objects.create_user(
            username='helpersuper', password='testpass123', role='employee')
        superuser.is_superuser = True
        superuser.save(update_fields=['is_superuser'])
        self.assertTrue(can_print_without_approval(superuser))
        self.assertTrue(is_manager_or_admin(superuser))
        self.assertTrue(can_use_digital_stamp(superuser))

    def test_custom_role_inherits_manager_permission(self) -> None:
        """نقش سفارشی مبتنی بر «مدیریت»، مجوز چاپ مستقیم را ارث می‌برد."""
        from system_control.models import Role
        Role.objects.create(code='sup', name='سرپرست', base_role='manager')
        user = User.objects.create_user(
            username='customsup', password='testpass123', role='sup')
        self.assertTrue(is_manager_or_admin(user))
        self.assertTrue(can_print_without_approval(user))


class ManagerAdminDirectPrintTests(TestCase):
    """نقش «مدیریت» و «مدیر کل» بدون نیاز به کد تأیید (OTP) چاپ می‌گیرند."""

    def setUp(self) -> None:
        self.creator = User.objects.create_user(
            username='bijakcreator', password='testpass123')
        self.manager = User.objects.create_user(
            username='printmanager', password='testpass123', role='manager')
        self.admin_user = User.objects.create_user(
            username='printadmin', password='testpass123', role='admin')
        self.customer = Customer.objects.create(
            name='Test Customer',
            national_id='1234567890'
        )
        self.driver = Driver.objects.create(
            name='Test Driver',
            national_id='0987654321',
            phone='09123456789'
        )
        self.vehicle = Vehicle.objects.create(
            driver=self.driver,
            license_plate_two_digit='12',
            license_plate_alphabet='A',
            license_plate_three_digit='345',
            license_plate_series='67',
            type='vant pikan mamoli'
        )
        tehran, mashhad = _make_cities()
        self.cargo = Cargo.objects.create(
            name='Test Cargo', weight=1000, origin=tehran, destination=mashhad)
        self.bijak = Bijak.objects.create(
            tracking_code='BYPASS001',
            value=Decimal('1000000'),
            insurance=Decimal('500000'),
            freight=Decimal('200000'),
            total_fare=Decimal('200000'),
            sender=self.customer,
            receiver=self.customer,
            driver=self.driver,
            vehicle=self.vehicle,
            cargo=self.cargo,
            created_by=self.creator,
            approval_status='pending',
        )
        self.api_request_url = reverse('printing:api_request_otp')
        self.api_verify_url = reverse('printing:api_verify_otp')

    def test_manager_api_request_print_without_otp(self) -> None:
        """مدیریت بدون OTP و برای بارنامه ساخته‌شده توسط کارمند دیگر چاپ می‌گیرد."""
        self.client.force_login(self.manager)
        response = self.client.post(
            self.api_request_url,
            {'bijak_id': self.bijak.id},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertFalse(data.get('need_verification', False))
        self.assertIn('print_url', data)
        record = WaybillPrintOTP.objects.get(bijak=self.bijak)
        self.assertEqual(record.print_count, 1)
        self.assertTrue(record.is_verified)
        self.assertIsNone(record.otp_code)

    def test_admin_traditional_view_redirects_directly(self) -> None:
        """ادمین در جریان سنتی، مستقیماً به صفحه چاپ هدایت می‌شود."""
        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse('printing:request_print'),
            {'waybill_number': self.bijak.tracking_code}
        )
        self.assertRedirects(
            response,
            reverse('issuance:crud:print', args=[self.bijak.id]),
            target_status_code=200
        )
        record = WaybillPrintOTP.objects.get(bijak=self.bijak)
        self.assertEqual(record.print_count, 1)

    def test_manager_api_verify_grants_directly(self) -> None:
        """مدیریت بدون کد OTP مستقیماً مجوز چاپ می‌گیرد."""
        self.client.force_login(self.manager)
        response = self.client.post(
            self.api_verify_url,
            {'bijak_id': self.bijak.id, 'otp_code': '000000'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('print_url', data)
        record = WaybillPrintOTP.objects.get(bijak=self.bijak)
        self.assertEqual(record.print_count, 1)

    def test_manager_print_page_for_pending_bijak(self) -> None:
        """صفحه چاپ برای بارنامه در انتظار تأیید، برای مدیریت باز می‌شود."""
        self.client.force_login(self.manager)
        response = self.client.get(
            reverse('issuance:manager:bijak_print', args=[self.bijak.id]))
        self.assertEqual(response.status_code, 200)

    def test_admin_print_page_for_pending_bijak(self) -> None:
        """صفحه چاپ برای بارنامه در انتظار تأیید، برای مدیر کل باز می‌شود."""
        self.client.force_login(self.admin_user)
        response = self.client.get(
            reverse('issuance:manager:bijak_print', args=[self.bijak.id]))
        self.assertEqual(response.status_code, 200)

    def test_employee_without_permission_cannot_print_pending_bijak(self) -> None:
        """کارمند بدون مجوز، نمی‌تواند بارنامه در انتظار تأیید را چاپ کند."""
        self.client.force_login(self.creator)
        response = self.client.get(
            reverse('issuance:manager:bijak_print', args=[self.bijak.id]))
        self.assertEqual(response.status_code, 403)

    @patch('printing.views.send_otp_via_smsir')
    def test_employee_still_requires_otp(self, mock_send: MagicMock) -> None:
        """کارمند همچنان به کد تأیید (OTP) نیاز دارد."""
        mock_send.return_value = (True, 'Success')
        self.client.force_login(self.creator)
        response = self.client.post(
            self.api_request_url,
            {'bijak_id': self.bijak.id},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertTrue(data['need_verification'])
        record = WaybillPrintOTP.objects.get(bijak=self.bijak)
        self.assertEqual(record.print_count, 0)
