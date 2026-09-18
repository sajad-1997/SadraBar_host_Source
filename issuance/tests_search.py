"""تست‌های صفحه جستجوی بارنامه و دکمه چاپ با وزن دوم"""
import re

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from cargo.models import Cargo, City, Province
from customers.models import Customer
from drivers.models import Driver
from fleet.models import Vehicle
from issuance.models import Bijak


class SearchPageWeight2Tests(TestCase):
    """دکمه «چاپ با وزن دوم» در صفحه جستجو و عملکرد چاپ"""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="searcher", password="test12345",
                                            role="admin", is_superuser=True)
        province = Province.objects.create(name="خراسان رضوی")
        city = City.objects.create(province=province, name="مشهد")
        cls.customer = Customer.objects.create(name="مشتری جستجو")
        cls.driver = Driver.objects.create(name="راننده جستجو", national_id="8888888888")
        cls.vehicle = Vehicle.objects.create(driver=cls.driver, license_plate_three_digit="666")
        cls.cargo_w2 = Cargo.objects.create(
            name="محموله وزن دوم", weight=20000, weight_2=15000,
            origin=city, destination=city)
        cls.cargo_no_w2 = Cargo.objects.create(
            name="محموله ساده", weight=10000, weight_2=0,
            origin=city, destination=city)

    def setUp(self):
        self.client.force_login(self.user)

    def _make_bijak(self, cargo):
        bijak = Bijak(
            sender=self.customer, receiver=self.customer,
            driver=self.driver, vehicle=self.vehicle, cargo=cargo,
            value=1, insurance=1, freight=1, total_fare=1,
            issuance_datetime=timezone.now(),
            status="issued", approval_status="approved", type="sent",
        )
        bijak.save()
        return bijak

    @staticmethod
    def _norm(html):
        return re.sub(r"\s+", " ", html)

    def test_weight2_button_shown_desktop_and_mobile(self):
        self._make_bijak(self.cargo_w2)
        response = self.client.get(reverse("issuance:search:search_shipment"))
        html = self._norm(response.content.decode())
        # یک دکمه در جدول دسکتاپ + یک دکمه در کارت موبایل
        self.assertEqual(html.count("چاپ با وزن دوم"), 2)
        self.assertContains(response, reverse("issuance:crud:print_weight2", args=[1]))

    def test_weight2_button_hidden_without_weight2(self):
        self._make_bijak(self.cargo_no_w2)
        response = self.client.get(reverse("issuance:search:search_shipment"))
        html = self._norm(response.content.decode())
        self.assertNotIn("چاپ با وزن دوم", html)

    def test_weight2_button_in_live_search_results(self):
        """نتایج جستجوی زنده (AJAX) هم باید دکمه را داشته باشند"""
        self._make_bijak(self.cargo_w2)
        response = self.client.get(
            reverse("issuance:search:ajax_search_shipment"), {"q": "وزن دوم"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["count"], 1)
        self.assertIn("چاپ با وزن دوم", self._norm(data["html"]))

    def test_live_search_matches_city_and_province(self):
        """جستجو روی نام شهر و استان (پس از تبدیل مبدأ/مقصد به FK)"""
        self._make_bijak(self.cargo_w2)
        for query in ("مشهد", "خراسان"):
            response = self.client.get(
                reverse("issuance:search:ajax_search_shipment"), {"q": query})
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertGreaterEqual(data["count"], 1, f"جستجوی {query} باید نتیجه بدهد")

    def test_print_weight2_renders_weight2_value(self):
        bijak = self._make_bijak(self.cargo_w2)
        response = self.client.get(
            reverse("issuance:crud:print_weight2", args=[bijak.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertIn("۱۵۰۰۰", self._norm(response.content.decode()))

    def test_print_normal_renders_weight_value(self):
        bijak = self._make_bijak(self.cargo_w2)
        response = self.client.get(reverse("issuance:crud:print", args=[bijak.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertIn("۲۰۰۰۰", self._norm(response.content.decode()))
