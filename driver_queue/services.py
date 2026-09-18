import logging
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.apps import apps
from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.urls import reverse

from . import conf
from .models import Announcement, QueueLog, QueueProfile, QueueTicket
from .sms import get_sms_gateway
from .utils import haversine_km, normalize_digits, tehran_now

logger = logging.getLogger(__name__)


class QueueError(Exception):
    """خطایی که عیناً باید به کاربر نمایش داده شود."""


# ================================================================ زمان‌بندی

def _parse_hhmm(value: str) -> time:
    hh, mm = value.split(":")
    return time(int(hh), int(mm))


def _combine(day: date, t: time) -> datetime:
    """
    ساخت کرانه زمانی بازه‌ها؛ متناسب با USE_TZ:
    - aware اگر USE_TZ=True
    - naive اگر USE_TZ=False (سازگار با SQLite و پروژه‌های بدون timezone)
    """
    base = datetime.combine(day, t)
    if settings.USE_TZ:
        base = base.replace(tzinfo=ZoneInfo(conf.TIMEZONE))
    return base


def is_working_day(day: date) -> bool:
    return day.weekday() in conf.WORKING_WEEKDAYS and day.isoformat() not in conf.HOLIDAYS


def queue_window(day: date):
    """
    بازه نوبت‌دهی: ۸:۰۰ تا ۱۱:۰۰ و ۱۱:۳۰ تا پایان روز.
    بین ۱۱:۰۰ تا ۱۱:۳۰ بازه اعلان است و نوبت‌دهی متوقف می‌شود.
    """
    start_morning = _combine(day, _parse_hhmm(conf.START_TIME))
    end_morning = _combine(day, _parse_hhmm(conf.ANNOUNCE_TIME))
    start_afternoon = _combine(day, _parse_hhmm(conf.ANNOUNCE_TIME)) + timedelta(minutes=conf.ANNOUNCE_WINDOW_MINUTES)
    end_day = _combine(day + timedelta(days=1), _parse_hhmm("00:00"))
    return (start_morning, end_morning), (start_afternoon, end_day)


def announce_window(day: date):
    """بازه به‌روزرسانی/اعلان: ۱۱:۰۰ تا ۱۱:۳۰."""
    start = _combine(day, _parse_hhmm(conf.ANNOUNCE_TIME))
    return start, start + timedelta(minutes=conf.ANNOUNCE_WINDOW_MINUTES)


def is_queue_open(now=None) -> bool:
    now = now or tehran_now()
    if not is_working_day(now.date()):
        return False
    (start_morning, end_morning), (start_afternoon, end_day) = queue_window(now.date())
    return (start_morning <= now <= end_morning) or (start_afternoon <= now <= end_day)


def is_announce_window(now=None) -> bool:
    now = now or tehran_now()
    if not is_working_day(now.date()):
        return False
    start, end = announce_window(now.date())
    return start <= now <= end


def queue_state(now=None) -> dict:
    now = now or tehran_now()
    return {
        "working_day": is_working_day(now.date()),
        "open": is_queue_open(now),
        "announce_window": is_announce_window(now),
        "waiting_count": waiting_tickets(now.date()).count(),
    }


# ================================================================ صف روزانه

def waiting_tickets(day=None):
    day = day or tehran_now().date()
    return QueueTicket.objects.filter(date=day, status=QueueTicket.Status.WAITING)


def active_ticket_for(driver, day=None):
    day = day or tehran_now().date()
    return waiting_tickets(day).filter(driver=driver).first()


def ahead_of(ticket) -> int:
    """تعداد نفرات جلوتر از این نوبت."""
    return waiting_tickets(ticket.date).filter(number__lt=ticket.number).count()


@transaction.atomic
def join_queue(driver, now=None) -> QueueTicket:
    """ثبت نوبت جدید؛ فقط روزهای کاری ۸ تا ۱۱."""
    now = now or tehran_now()
    day = now.date()
    if not is_working_day(day):
        raise QueueError("امروز روز کاری نیست و نوبت‌دهی انجام نمی‌شود.")
    if not is_queue_open(now):
        start, _end = queue_window(day)
        if now < start:
            raise QueueError(f"نوبت‌دهی از ساعت {conf.START_TIME} آغاز می‌شود.")
        raise QueueError(f"نوبت‌دهی امروز ساعت {conf.END_TIME} به پایان رسید.")
    number = waiting_tickets(day).count() + 1
    try:
        return QueueTicket.objects.create(driver=driver, date=day, number=number)
    except IntegrityError:
        raise QueueError("شما برای امروز نوبت دارید.")


@transaction.atomic
def renumber(day) -> None:
    """شماره‌گذاری مجدد حاضران صف بر اساس زمان پیوستن (بعد از هر حذف)."""
    tickets = list(
        QueueTicket.objects.select_for_update()
        .filter(date=day, status=QueueTicket.Status.WAITING)
        .order_by("joined_at", "id")
    )
    for index, ticket in enumerate(tickets, start=1):
        if ticket.number != index:
            ticket.number = index
            ticket.save(update_fields=["number"])


def is_first_saturday(day: date) -> bool:
    """بررسی اینکه آیا روز وارد شده شنبه اول ماه است."""
    if day.weekday() != 6:  # شنبه در Python = 6
        return False
    # اولین شنبه ماه است اگر روز ماه کمتر از 8 باشد
    return day.day <= 7


def weekly_queue_update(now=None) -> int:
    """
    بروزرسانی هفتگی لیست نوبت‌ها در شنبه اول ماه.
    افراد حاضر در صف از هفته گذشته و افراد جدید در صف در هفته جدید
    پشت سر هم به ترتیب زمان دریافت نوبت در لیست قرار می‌گیرند.
    """
    now = now or tehran_now()
    day = now.date()
    
    if not is_first_saturday(day):
        return 0
    
    # پیدا کردن آخرین شنبه قبل از امروز (برای گرفتن نوبت‌های هفته گذشته)
    last_saturday = day - timedelta(days=7)
    
    # گرفتن نوبت‌های هفته گذشته که هنوز در وضعیت waiting هستند
    last_week_tickets = list(
        QueueTicket.objects
        .filter(date=last_saturday, status=QueueTicket.Status.WAITING)
        .select_related("driver")
        .order_by("joined_at", "id")
    )
    
    if not last_week_tickets:
        return 0
    
    # ایجاد نوبت‌های جدید برای امروز برای رانندگان هفته گذشته
    updated_count = 0
    for old_ticket in last_week_tickets:
        # بررسی اینکه آیا راننده برای امروز نوبت دارد
        existing = QueueTicket.objects.filter(
            driver=old_ticket.driver, 
            date=day
        ).first()
        
        if not existing:
            # ایجاد نوبت جدید با همان زمان پیوستن
            new_ticket = QueueTicket.objects.create(
                driver=old_ticket.driver,
                date=day,
                number=0  # بعداً شماره‌گذاری می‌شود
            )
            # حفظ زمان پیوستن اصلی برای ترتیب‌بندی صحیح
            new_ticket.joined_at = old_ticket.joined_at
            new_ticket.save(update_fields=["joined_at"])
            updated_count += 1
    
    # شماره‌گذاری مجدد همه نوبت‌های امروز (قدیمی + جدید)
    renumber(day)
    
    return updated_count


# ================================================================ اعلان ۱۱:۰۰

def announcement_links(ticket) -> dict:
    base = conf.BASE_URL.rstrip("/")
    return {
        "loaded": base + reverse("driver_queue:announce_respond",
                                 args=[ticket.token, Announcement.Response.LOADED]),
        "waiting": base + reverse("driver_queue:announce_respond",
                                  args=[ticket.token, Announcement.Response.STILL_WAITING]),
    }


def build_announcement_sms(ticket) -> str:
    links = announcement_links(ticket)
    return (
        f"راننده گرامی {ticket.driver.name}؛\n"
        f"لطفا وضعیت نوبت امروز خود را اعلام کنید "
        f"(مهلت: {conf.RESPONSE_GRACE_MINUTES} دقیقه).\n"
        f"اگر بار گرفته‌اید: {links['loaded']}\n"
        f"اگر هنوز در نوبت هستید: {links['waiting']}"
    )


@transaction.atomic
def send_announcements(now=None) -> int:
    """ارسال اعلان برای همه حاضران صف امروز (اید‌امپوتنت؛ ارسال تکراری نمی‌شود)."""
    now = now or tehran_now()
    day = now.date()
    gateway = get_sms_gateway()
    sent = 0
    for ticket in waiting_tickets(day).select_related("driver").order_by("number"):
        if ticket.announcements.filter(day=day).exists():
            continue
        announcement = Announcement.objects.create(ticket=ticket, day=day, sent_at=now)
        try:
            result = gateway.send(ticket.driver.phone, build_announcement_sms(ticket))
        except Exception as exc:  # noqa: BLE001
            logger.exception("خطا در ارسال پیامک به %s", ticket.driver.phone)
            result = f"error: {exc}"
        announcement.sms_result = str(result)
        announcement.save(update_fields=["sms_result"])
        sent += 1
    return sent


@transaction.atomic
def respond_to_announcement(token, action, now=None) -> str:
    """پاسخ راننده به اعلان (از طریق لینک پیامکی یا دکمه‌های صفحه)."""
    now = now or tehran_now()
    if action not in dict(Announcement.Response.choices):
        raise QueueError("گزینه انتخابی معتبر نیست.")
    try:
        ticket = QueueTicket.objects.select_related("driver").get(token=token, date=now.date())
    except QueueTicket.DoesNotExist:
        raise QueueError("نوبتی مطابق این پیوند یافت نشد.")
    if ticket.status != QueueTicket.Status.WAITING:
        raise QueueError("این نوبت قبلا تعیین تکلیف شده است.")
    announcement = (ticket.announcements
                    .filter(day=ticket.date, response__isnull=True)
                    .order_by("-sent_at").first())
    if announcement is None:
        raise QueueError("اعلانی برای پاسخ وجود ندارد یا قبلا پاسخ داده شده است.")

    announcement.response = action
    announcement.responded_at = now
    announcement.save(update_fields=["response", "responded_at"])

    if action == Announcement.Response.LOADED:
        # گزینه اول: راننده بار گرفته -> حذف از صف
        ticket.status = QueueTicket.Status.LOADED
        ticket.removed_at = now
        ticket.save(update_fields=["status", "removed_at"])
        renumber(ticket.date)
        return "بارگیری شما ثبت شد و از صف امروز حذف شدید."

    # گزینه دوم: هنوز در نوبت است -> ماندن در صف + به‌روزرسانی لیست
    renumber(ticket.date)
    return "حضور شما در صف ثبت شد و در نوبت باقی می‌مانید."


@transaction.atomic
def purge_nonresponders(now=None) -> int:
    """
    حذف خودکار کسانی که به اعلان پاسخ نداده‌اند.
    قانون: اگر ظرف ۱۵ دقیقه از شروع به‌روزرسانی پاسخی ثبت نشود، حذف خودکار.
    """
    now = now or tehran_now()
    day = now.date()
    deadline = now - timedelta(minutes=conf.RESPONSE_GRACE_MINUTES)
    announce_start = _combine(day, _parse_hhmm(conf.ANNOUNCE_TIME))
    removed = 0
    for ticket in waiting_tickets(day):
        announcement = ticket.announcements.filter(day=day).order_by("-sent_at").first()
        if announcement is None:
            # اعلانی ارسال نشده؛ مهلت از شروع بازه اعلان محاسبه می‌شود
            if now < announce_start + timedelta(minutes=conf.RESPONSE_GRACE_MINUTES):
                continue
        else:
            if announcement.responded_at is not None or announcement.sent_at > deadline:
                continue
        ticket.status = QueueTicket.Status.REMOVED_NO_RESPONSE
        ticket.removed_at = now
        ticket.save(update_fields=["status", "removed_at"])
        removed += 1
    if removed:
        renumber(day)
    return removed


# ================================================================ موقعیت مکانی

@transaction.atomic
def report_location(ticket, lat, lng, now=None) -> bool:
    """
    بررسی حضور در محدوده دفتر فقط در بازه به‌روزرسانی (۱۱:۰۰ تا ۱۱:۳۰).
    خارج از شعاع پیکربندی‌شده -> حذف خودکار. خروجی: True یعنی حذف شد.
    """
    now = now or tehran_now()
    if ticket.status != QueueTicket.Status.WAITING or not is_announce_window(now):
        return False
    distance = haversine_km(lat, lng, conf.OFFICE_LAT, conf.OFFICE_LNG)
    if distance > conf.GEOFENCE_RADIUS_KM:
        ticket.status = QueueTicket.Status.REMOVED_DISTANCE
        ticket.removed_at = now
        ticket.save(update_fields=["status", "removed_at"])
        renumber(ticket.date)
        return True
    return False


# ================================================================ زمان‌بند بدون Celery

def run_due_jobs(now=None) -> None:
    """
    اجرای کارهای زمان‌بندی‌شده بدون نیاز به Celery/Redis.
    این تابع در ویوهای صفحه صف و پنل فراخوانی می‌شود و چون هر دو تابعِ داخل آن
    idempotent هستند، فراخوانی مکرر بی‌خطر است:
      - اگر از ساعت ۱۱:۰۰ گذشته و اعلان امروز ارسال نشده -> ارسال می‌شود.
      - اگر از پایان مهلت ۱۵ دقیقه‌ای گذشته -> عدم‌پاسخ‌دهنده‌ها حذف می‌شوند.
      - اگر شنبه اول ماه باشد -> بروزرسانی هفتگی لیست نوبت‌ها انجام می‌شود.
    برای اجرا رأس ساعت (حتی بدون بازدیدکننده) از cron استفاده کنید.
    """
    now = now or tehran_now()
    day = now.date()
    if not is_working_day(day):
        return
    
    # بروزرسانی هفتگی در شنبه اول ماه
    weekly_queue_update(now)
    
    announce_start, _end = announce_window(day)
    if now >= announce_start:
        send_announcements(now)
    if now >= announce_start + timedelta(minutes=conf.RESPONSE_GRACE_MINUTES):
        purge_nonresponders(now)


# ================================================================ عملیات پنل

def _log(actor, action, driver=None, ticket=None, detail=""):
    """ثبت گزارش عملیات کاربران پنل."""
    QueueLog.objects.create(user=actor, action=action,
                            driver=driver, ticket=ticket, detail=detail)


def search_drivers(query, limit=20):
    """جستجوی راننده بر اساس نام / کد ملی / تلفن / شماره گواهینامه."""
    driver_model = apps.get_model(conf.DRIVER_MODEL)
    q = normalize_digits(query).strip()
    if not q:
        return driver_model.objects.none()
    lookup = (Q(name__icontains=q) | Q(national_id__icontains=q)
              | Q(phone__icontains=q) | Q(certificate__icontains=q))
    return driver_model.objects.filter(lookup).order_by("name")[:limit]


@transaction.atomic
def staff_add_ticket(driver, day=None, actor=None) -> QueueTicket:
    """ثبت نوبت دستی توسط کاربر پنل؛ محدود به بازه ۸ تا ۱۱ نیست."""
    day = day or tehran_now().date()
    existing = QueueTicket.objects.filter(driver=driver, date=day).first()
    if existing:
        if existing.status == QueueTicket.Status.WAITING:
            raise QueueError("این راننده برای تاریخ انتخابی نوبت فعال دارد.")
        existing.delete()  # نوبتِ از قبل تعیین‌تکلیف‌شده با نوبت جدید جایگزین می‌شود
    number = waiting_tickets(day).count() + 1
    ticket = QueueTicket.objects.create(driver=driver, date=day, number=number)
    _log(actor, QueueLog.Action.ADD_TICKET, driver=driver, ticket=ticket,
         detail=f"ثبت نوبت دستی برای {day}")
    return ticket


@transaction.atomic
def staff_remove_ticket(ticket, actor=None) -> None:
    """حذف نوبت توسط کاربر پنل؛ اگر در صف باشد علامت‌گذاری و شماره‌ها به‌روز می‌شود."""
    day = ticket.date
    driver = ticket.driver
    if ticket.status == QueueTicket.Status.WAITING:
        ticket.status = QueueTicket.Status.REMOVED_BY_STAFF
        ticket.removed_at = tehran_now()
        ticket.save(update_fields=["status", "removed_at"])
        renumber(day)
        _log(actor, QueueLog.Action.REMOVE_TICKET, driver=driver, ticket=ticket)
    else:
        ticket.delete()  # سابقه غیرفعال بود؛ کامل حذف می‌شود
        _log(actor, QueueLog.Action.REMOVE_TICKET, driver=driver,
             detail="حذف سابقه نوبت")


@transaction.atomic
def staff_mark_loaded(ticket, actor=None) -> None:
    """ثبت «بار گرفته» توسط کاربر پنل."""
    if ticket.status != QueueTicket.Status.WAITING:
        raise QueueError("این نوبت در وضعیت «در صف» نیست.")
    ticket.status = QueueTicket.Status.LOADED
    ticket.removed_at = tehran_now()
    ticket.save(update_fields=["status", "removed_at"])
    renumber(ticket.date)
    _log(actor, QueueLog.Action.MARK_LOADED, driver=ticket.driver, ticket=ticket)


def approve_driver(driver, actor=None, approved=True) -> None:
    """تایید/لغو تایید راننده (اطلاعات تکمیلی نزد دفتر)."""
    profile, _ = QueueProfile.objects.get_or_create(driver=driver)
    profile.office_approved = approved
    profile.save(update_fields=["office_approved"])
    action = (QueueLog.Action.APPROVE_DRIVER if approved
              else QueueLog.Action.UNAPPROVE_DRIVER)
    _log(actor, action, driver=driver)
