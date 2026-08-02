"""
Tests for printing app.
Coverage target: >= 70%
"""
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from issuance.models import Bijak, Driver, Customer, Vehicle, Cargo
from .models import WaybillPrintOTP
from .serializers import (
    WaybillPrintOTPSerializer,
    RequestOTPSerializer,
    VerifyOTPSerializer
)

User = get_user_model()


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
        self.cargo = Cargo.objects.create(name='Test Cargo', weight=1000, origin='Tehran', destination='Mashhad')
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
        self.cargo = Cargo.objects.create(name='Test Cargo', weight=1000, origin='Tehran', destination='Mashhad')
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
        self.cargo = Cargo.objects.create(name='Test Cargo', weight=1000, origin='Tehran', destination='Mashhad')
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
        self.assertIn('verify_otp', response.url)

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
        self.assertIn('request_print', response.url)


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
        self.cargo = Cargo.objects.create(name='API Cargo', weight=500, origin='Isfahan', destination='Shiraz')
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
        self.assertEqual(response.status_code, 404)

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
        self.assertEqual(otp_record.print_count, 1)
