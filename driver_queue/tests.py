from datetime import date, datetime
from unittest import mock
from zoneinfo import ZoneInfo

from django.apps import apps
from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model

from . import conf, services
from .models import Announcement, QueueProfile, QueueTicket
from .utils import haversine_km, is_valid_national_id, normalize_digits
from .models import Announcement, QueueProfile, QueueStaff, QueueTicket

TZ = ZoneInfo("Asia/Tehran")
SATURDAY = date(2026, 8, 8)  # شنبه - روز کاری
SUNDAY = date(2026, 8, 9)  # یکشنبه - روز کاری
FRIDAY = date(2026, 8, 7)  # جمعه - تعطیل
VALID_NID = "0499370899"  # معتبر از نظر چک‌سام کد ملی


def _driver_model():
    return apps.get_model(conf.DRIVER_MODEL)


def dt(day, hour=8, minute=0):
    return datetime(day.year, day.month, day.day, hour, minute, tzinfo=TZ)


def make_driver(nid=VALID_NID, name="علی رضایی", phone="09121112233"):
    return _driver_model().objects.create(
        name=name,
        national_id=nid,
        certificate=f"GB-{nid}",  # در مدل شما اجباری و یکتا است
        phone=phone,
        created_by_role="queue-test",
    )


class UtilsTests(TestCase):
    def test_normalize_digits(self):
        self.assertEqual(normalize_digits("۰۹۱۲٣۴۵"), "0912345")

    def test_national_id_validation(self):
        self.assertTrue(is_valid_national_id("0499370899"))
        self.assertTrue(is_valid_national_id("۱۲۳۴۵۶۷۸۹۱"))
        self.assertFalse(is_valid_national_id("1111111111"))
        self.assertFalse(is_valid_national_id("123"))

    def test_haversine(self):
        self.assertLess(haversine_km(35.0, 51.0, 35.01, 51.01), 2)
        self.assertGreater(haversine_km(35.0, 51.0, 35.2, 51.2), 20)


@override_settings(QUEUE_TIMEZONE="Asia/Tehran")
class JoinQueueTests(TestCase):
    def setUp(self):
        self.driver = make_driver()

    def test_join_inside_window(self):
        ticket = services.join_queue(self.driver, now=dt(SUNDAY, 9, 30))
        self.assertEqual(ticket.number, 1)
        self.assertEqual(ticket.status, QueueTicket.Status.WAITING)

    def test_join_before_window(self):
        with self.assertRaises(services.QueueError):
            services.join_queue(self.driver, now=dt(SUNDAY, 7, 0))

    def test_join_after_window(self):
        with self.assertRaises(services.QueueError):
            services.join_queue(self.driver, now=dt(SUNDAY, 11, 30))

    def test_join_on_friday(self):
        with self.assertRaises(services.QueueError):
            services.join_queue(self.driver, now=dt(FRIDAY, 9, 0))

    def test_join_on_holiday(self):
        with self.settings(QUEUE_HOLIDAYS=[SATURDAY.isoformat()]):
            with self.assertRaises(services.QueueError):
                services.join_queue(self.driver, now=dt(SATURDAY, 9, 0))

    def test_duplicate_join_blocked(self):
        services.join_queue(self.driver, now=dt(SUNDAY, 9, 0))
        with self.assertRaises(services.QueueError):
            services.join_queue(self.driver, now=dt(SUNDAY, 9, 5))


@override_settings(QUEUE_TIMEZONE="Asia/Tehran")
class RenumberTests(TestCase):
    def setUp(self):
        self.d1 = make_driver("0499370899")
        self.d2 = make_driver("1234567891", "رضا محمدی")
        self.d3 = make_driver("0013542427", "حسین کریمی")

    def test_renumber_after_removal(self):
        t1 = services.join_queue(self.d1, now=dt(SUNDAY, 9, 0))
        t2 = services.join_queue(self.d2, now=dt(SUNDAY, 9, 5))
        t3 = services.join_queue(self.d3, now=dt(SUNDAY, 9, 10))
        self.assertEqual([t1.number, t2.number, t3.number], [1, 2, 3])
        t2.status = QueueTicket.Status.LOADED
        t2.save()
        services.renumber(SUNDAY)
        t1.refresh_from_db();
        t3.refresh_from_db()
        self.assertEqual([t1.number, t3.number], [1, 2])
        self.assertEqual(services.ahead_of(t3), 1)


class FakeGateway:
    def __init__(self):
        self.messages = []

    def send(self, phone, text):
        self.messages.append((phone, text))
        return "ok"


@override_settings(QUEUE_TIMEZONE="Asia/Tehran", QUEUE_BASE_URL="http://testserver")
class AnnouncementTests(TestCase):
    def setUp(self):
        self.d1 = make_driver("0499370899")
        self.d2 = make_driver("1234567891", "رضا محمدی", "09122223344")
        patcher = mock.patch("driver_queue.services.get_sms_gateway",
                             return_value=FakeGateway())
        self.gateway = patcher.start().return_value
        self.addCleanup(patcher.stop)
        self.t1 = services.join_queue(self.d1, now=dt(SUNDAY, 8, 30))
        self.t2 = services.join_queue(self.d2, now=dt(SUNDAY, 8, 40))

    def test_send_creates_announcements_once(self):
        self.assertEqual(services.send_announcements(now=dt(SUNDAY, 11, 0)), 2)
        self.assertEqual(len(self.gateway.messages), 2)
        self.assertEqual(services.send_announcements(now=dt(SUNDAY, 11, 2)), 0)

    def test_respond_waiting_keeps_ticket(self):
        services.send_announcements(now=dt(SUNDAY, 11, 0))
        services.respond_to_announcement(self.t1.token,
                                         Announcement.Response.STILL_WAITING,
                                         now=dt(SUNDAY, 11, 5))
        self.t1.refresh_from_db()
        self.assertEqual(self.t1.status, QueueTicket.Status.WAITING)

    def test_respond_loaded_removes_and_renumbers(self):
        services.send_announcements(now=dt(SUNDAY, 11, 0))
        services.respond_to_announcement(self.t1.token,
                                         Announcement.Response.LOADED,
                                         now=dt(SUNDAY, 11, 5))
        self.t1.refresh_from_db();
        self.t2.refresh_from_db()
        self.assertEqual(self.t1.status, QueueTicket.Status.LOADED)
        self.assertEqual(self.t2.number, 1)

    def test_purge_removes_only_nonresponders(self):
        services.send_announcements(now=dt(SUNDAY, 11, 0))
        services.respond_to_announcement(self.t2.token,
                                         Announcement.Response.STILL_WAITING,
                                         now=dt(SUNDAY, 11, 3))
        removed = services.purge_nonresponders(now=dt(SUNDAY, 11, 16))
        self.assertEqual(removed, 1)
        self.t1.refresh_from_db();
        self.t2.refresh_from_db()
        self.assertEqual(self.t1.status, QueueTicket.Status.REMOVED_NO_RESPONSE)
        self.assertEqual(self.t2.status, QueueTicket.Status.WAITING)
        self.assertEqual(self.t2.number, 1)


@override_settings(QUEUE_TIMEZONE="Asia/Tehran")
class DueJobsTests(TestCase):
    """زمان‌بند بدون Celery: run_due_jobs"""

    def setUp(self):
        self.d1 = make_driver("0499370899")
        self.d2 = make_driver("1234567891", "رضا محمدی", "09122223344")
        patcher = mock.patch("driver_queue.services.get_sms_gateway",
                             return_value=FakeGateway())
        patcher.start()
        self.addCleanup(patcher.stop)
        services.join_queue(self.d1, now=dt(SUNDAY, 8, 30))
        services.join_queue(self.d2, now=dt(SUNDAY, 8, 40))

    def test_jobs_run_at_due_time(self):
        # قبل از ساعت ۱۱ هیچ اتفاقی نمی‌افتد
        services.run_due_jobs(now=dt(SUNDAY, 10, 30))
        self.assertEqual(Announcement.objects.count(), 0)
        # سر ساعت ۱۱ اعلان‌ها ارسال می‌شوند ولی هنوز مهلت باقی است
        services.run_due_jobs(now=dt(SUNDAY, 11, 0))
        self.assertEqual(Announcement.objects.count(), 2)
        self.assertEqual(QueueTicket.objects.filter(status=QueueTicket.Status.WAITING).count(), 2)
        # پس از پایان مهلت ۱۵ دقیقه‌ای، عدم‌پاسخ‌دهنده‌ها حذف می‌شوند
        services.run_due_jobs(now=dt(SUNDAY, 11, 16))
        self.assertEqual(QueueTicket.objects.filter(
            status=QueueTicket.Status.REMOVED_NO_RESPONSE).count(), 2)


@override_settings(QUEUE_TIMEZONE="Asia/Tehran",
                   OFFICE_LAT=35.0, OFFICE_LNG=51.0,
                   QUEUE_GEOFENCE_RADIUS_KM=5.0)
class LocationTests(TestCase):
    def setUp(self):
        self.ticket = services.join_queue(make_driver(), now=dt(SUNDAY, 9, 0))

    def test_far_location_removes_during_window(self):
        self.assertTrue(services.report_location(self.ticket, 35.2, 51.2,
                                                 now=dt(SUNDAY, 11, 5)))
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, QueueTicket.Status.REMOVED_DISTANCE)

    def test_near_location_keeps(self):
        self.assertFalse(services.report_location(self.ticket, 35.01, 51.01,
                                                  now=dt(SUNDAY, 11, 5)))
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, QueueTicket.Status.WAITING)

    def test_ignored_outside_announce_window(self):
        self.assertFalse(services.report_location(self.ticket, 35.2, 51.2,
                                                  now=dt(SUNDAY, 10, 0)))


@override_settings(QUEUE_TIMEZONE="Asia/Tehran")
class FlowTests(TestCase):
    IDENTIFY_DATA = {"first_name": "علی", "last_name": "رضایی",
                     "national_id": VALID_NID}

    def test_unknown_driver_redirected_to_register(self):
        resp = self.client.post(reverse("driver_queue:identify"), self.IDENTIFY_DATA)
        self.assertRedirects(resp, reverse("driver_queue:register"))

    def test_register_flow(self):
        self.client.post(reverse("driver_queue:identify"), self.IDENTIFY_DATA)
        resp = self.client.post(reverse("driver_queue:register"), {
            **self.IDENTIFY_DATA,
            "phone": "09121112233",
            "certificate": "GB-123456",
        })
        self.assertRedirects(resp, reverse("driver_queue:register_done"))
        driver = _driver_model().objects.get(national_id=VALID_NID)
        self.assertEqual(driver.name, "علی رضایی")
        self.assertEqual(driver.created_by_role, "queue")
        profile = QueueProfile.objects.get(driver=driver)
        self.assertFalse(profile.office_approved)
        done = self.client.get(reverse("driver_queue:register_done"))
        self.assertContains(done, "اطلاعات تکمیلی")

    def test_known_driver_goes_to_queue(self):
        make_driver()
        resp = self.client.post(reverse("driver_queue:identify"), self.IDENTIFY_DATA)
        self.assertRedirects(resp, reverse("driver_queue:queue"))

    def test_known_driver_wrong_name(self):
        make_driver()
        resp = self.client.post(reverse("driver_queue:identify"), {
            **self.IDENTIFY_DATA, "first_name": "اکبر"})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "مطابقت ندارد")

    def test_queue_page_requires_session(self):
        self.assertRedirects(self.client.get(reverse("driver_queue:queue")),
                             reverse("driver_queue:identify"))

    def test_sms_link_waiting_response(self):
        driver = make_driver()
        with mock.patch("driver_queue.services.tehran_now",
                        return_value=dt(SUNDAY, 11, 0)):
            ticket = services.join_queue(driver)
            services.send_announcements()
            url = reverse("driver_queue:announce_respond",
                          args=[ticket.token, "waiting"])
            resp = self.client.get(url)
        self.assertContains(resp, "حضور شما در صف ثبت شد")


@override_settings(QUEUE_TIMEZONE="Asia/Tehran")
class PanelPermissionTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.url = reverse("driver_queue:panel_dashboard")
        self.staff_user = User.objects.create_user(username="staff1", password="x")
        self.manager_user = User.objects.create_user(username="mgr1", password="x")
        self.admin_user = User.objects.create_superuser(username="admin1", password="x")

    def test_anonymous_redirected_to_login(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 302)
        self.assertIn("login", resp.url)

    def test_normal_user_forbidden(self):
        plain = get_user_model().objects.create_user(username="plain", password="x")
        self.client.force_login(plain)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_unapproved_staff_forbidden(self):
        QueueStaff.objects.create(user=self.staff_user, role=QueueStaff.Role.STAFF, approved=False)
        self.client.force_login(self.staff_user)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_approved_staff_ok(self):
        QueueStaff.objects.create(user=self.staff_user, role=QueueStaff.Role.STAFF, approved=True)
        self.client.force_login(self.staff_user)
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_manager_ok_without_approval(self):
        QueueStaff.objects.create(user=self.manager_user, role=QueueStaff.Role.MANAGER, approved=False)
        self.client.force_login(self.manager_user)
        self.assertEqual(self.client.get(self.url).status_code, 200)
        self.assertEqual(self.client.get(reverse("driver_queue:panel_users")).status_code, 200)

    def test_superuser_ok(self):
        self.client.force_login(self.admin_user)
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_staff_cannot_open_users_page(self):
        QueueStaff.objects.create(user=self.staff_user, role=QueueStaff.Role.STAFF, approved=True)
        self.client.force_login(self.staff_user)
        self.assertEqual(self.client.get(reverse("driver_queue:panel_users")).status_code, 403)


@override_settings(QUEUE_TIMEZONE="Asia/Tehran")
class PanelOperationsTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.staff_user = User.objects.create_user(username="staff1", password="x")
        QueueStaff.objects.create(user=self.staff_user, role=QueueStaff.Role.STAFF, approved=True)
        self.manager_user = User.objects.create_user(username="mgr1", password="x")
        QueueStaff.objects.create(user=self.manager_user, role=QueueStaff.Role.MANAGER)
        self.driver = make_driver()
        self.client.force_login(self.staff_user)

    def test_staff_add_ticket_outside_window(self):
        # ثبت نوبت دستی محدود به بازه ۸ تا ۱۱ نیست
        resp = self.client.post(reverse("driver_queue:panel_ticket_add"),
                                {"driver_pk": self.driver.pk, "date": SUNDAY.isoformat()})
        self.assertEqual(resp.status_code, 302)
        ticket = QueueTicket.objects.get(driver=self.driver, date=SUNDAY)
        self.assertEqual(ticket.status, QueueTicket.Status.WAITING)

    def test_staff_remove_ticket(self):
        ticket = services.staff_add_ticket(self.driver, SUNDAY, actor=self.staff_user)
        self.client.post(reverse("driver_queue:panel_ticket_remove", args=[ticket.pk]))
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, QueueTicket.Status.REMOVED_BY_STAFF)

    def test_staff_mark_loaded(self):
        ticket = services.staff_add_ticket(self.driver, SUNDAY, actor=self.staff_user)
        self.client.post(reverse("driver_queue:panel_ticket_loaded", args=[ticket.pk]))
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, QueueTicket.Status.LOADED)

    def test_approve_driver(self):
        self.client.post(reverse("driver_queue:panel_driver_approve", args=[self.driver.pk]),
                         {"approve": "1"})
        self.assertTrue(QueueProfile.objects.get(driver=self.driver).office_approved)

    def test_manager_approves_staff(self):
        new_user = get_user_model().objects.create_user(username="emp2", password="x")
        qs = QueueStaff.objects.create(user=new_user, role=QueueStaff.Role.STAFF, approved=False)
        self.client.force_login(self.manager_user)
        self.client.post(reverse("driver_queue:panel_user_toggle", args=[qs.pk]))
        qs.refresh_from_db()
        self.assertTrue(qs.approved)
        self.assertEqual(qs.approved_by, self.manager_user)

    def test_driver_detail_page(self):
        resp = self.client.get(reverse("driver_queue:panel_driver_detail", args=[self.driver.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, self.driver.name)
        self.assertContains(resp, self.driver.national_id)
