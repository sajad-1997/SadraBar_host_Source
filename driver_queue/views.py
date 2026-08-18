import json

from django.apps import apps
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from . import conf, services
from .forms import IdentifyForm, RegisterForm
from .models import QueueProfile
from .utils import tehran_now

SESSION_DRIVER = "driver_queue_driver_id"
SESSION_PREREG = "driver_queue_preregister"


def _driver_model():
    """مدل راننده ماژول رانندگان (بدون import مستقیم برای جلوگیری از وابستگی)."""
    return apps.get_model(conf.DRIVER_MODEL)


def _driver_from_session(request):
    driver_id = request.session.get(SESSION_DRIVER)
    return _driver_model().objects.filter(pk=driver_id).first() if driver_id else None


def _same_name(entered_name: str, stored_name: str) -> bool:
    """مقایسه نام واردشده با فیلد name مدل راننده."""
    entered = " ".join(entered_name.split())
    stored = " ".join((stored_name or "").split())
    return entered == stored


# ---------------------------------------------------------------- صفحات اصلی

def landing(request):
    return render(request, "driver_queue/landing.html",
                  {"driver": _driver_from_session(request)})


def identify(request):
    """دریافت نام و نام خانوادگی و شماره تماس و تطابق با سوابق."""
    if _driver_from_session(request):
        return redirect("driver_queue:queue")
    form = IdentifyForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        phone = form.cleaned_data["phone"]
        driver = _driver_model().objects.filter(phone=phone).first()
        if driver is None:
            # داده وجود ندارد -> انتقال به ثبت‌نام با داده‌های پیش‌تکمیل‌شده
            request.session[SESSION_PREREG] = form.cleaned_data
            return redirect("driver_queue:register")
        if not _same_name(form.cleaned_data["name"], driver.name):
            form.add_error(None, "اطلاعات وارد شده با سوابق ثبت‌شده مطابقت ندارد.")
        else:
            request.session[SESSION_DRIVER] = driver.pk
            return redirect("driver_queue:queue")
    return render(request, "driver_queue/identify.html", {"form": form})


def register(request):
    if _driver_from_session(request):
        return redirect("driver_queue:queue")
    prereg = request.session.get(SESSION_PREREG, {})
    initial = {k: prereg.get(k, "") for k in ("name", "phone")}
    form = RegisterForm(request.POST or None, initial=initial or None)
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        driver_model = _driver_model()
        if driver_model.objects.filter(phone=data["phone"]).exists():
            form.add_error("phone", "این شماره تماس قبلا ثبت شده است.")
        elif driver_model.objects.filter(certificate=data["certificate"]).exists():
            form.add_error("certificate", "این شماره گواهینامه قبلا ثبت شده است.")
        else:
            driver = driver_model.objects.create(
                name=data["name"],
                phone=data["phone"],
                certificate=data["certificate"],
                created_by_role="queue",  # نشانه ثبت‌نام از صفحه نوبت‌دهی
            )
            QueueProfile.objects.create(driver=driver, office_approved=False)
            request.session[SESSION_DRIVER] = driver.pk
            request.session.pop(SESSION_PREREG, None)
            return redirect("driver_queue:register_done")
    return render(request, "driver_queue/register.html", {"form": form})


def register_done(request):
    """نمایش پیام «ارائه اطلاعات تکمیلی به دفتر» و دکمه تایید."""
    driver = _driver_from_session(request)
    if not driver:
        return redirect("driver_queue:identify")
    return render(request, "driver_queue/register_done.html", {"driver": driver})


# ---------------------------------------------------------------- صفحه صف

def queue(request):
    driver = _driver_from_session(request)
    if not driver:
        return redirect("driver_queue:identify")
    now = tehran_now()
    # اجرای اعلان ۱۱:۰۰ و حذف ۱۱:۱۵ بدون Celery (اید‌امپوتنت)
    services.run_due_jobs(now)
    state = services.queue_state(now)
    ticket = services.active_ticket_for(driver, now.date())
    profile, _ = QueueProfile.objects.get_or_create(driver=driver)
    pending_announcement = bool(ticket) and ticket.announcements.filter(response__isnull=True).exists()
    
    # پیام‌های اعلان
    notification_messages = []
    if not profile.office_approved:
        notification_messages.append({
            'type': 'warning',
            'message': 'جهت دریافت بار باید اطلاعات تکمیلی خود را به دفتر باربری ارائه دهید.'
        })
    if state['announce_window'] and ticket:
        notification_messages.append({
            'type': 'info',
            'message': f'در بازه به‌روزرسانی صف، موقعیت مکانی شما برای حضور در محدوده {conf.GEOFENCE_RADIUS_KM} کیلومتری دفتر بررسی می‌شود.'
        })
    if pending_announcement:
        notification_messages.append({
            'type': 'urgent',
            'message': 'اعلان وضعیت: لطفا وضعیت خود را اعلام کنید (مهلت: ۱۵ دقیقه).'
        })
    
    context = {
        "driver": driver,
        "now": now,
        "state": state,
        "ticket": ticket,
        "ahead": services.ahead_of(ticket) if ticket else None,
        "pending_announcement": pending_announcement,
        "announce_links": (services.announcement_links(ticket)
                           if ticket and pending_announcement else None),
        "waiting_list": services.waiting_tickets(now.date()).select_related("driver"),
        "radius_km": conf.GEOFENCE_RADIUS_KM,
        "office_approved": profile.office_approved,
        "notification_messages": notification_messages,
    }
    return render(request, "driver_queue/queue.html", context)


@require_POST
def join(request):
    driver = _driver_from_session(request)
    if not driver:
        return redirect("driver_queue:identify")
    try:
        services.join_queue(driver)
        messages.success(request, "نوبت شما با موفقیت ثبت شد.")
    except services.QueueError as exc:
        messages.error(request, str(exc))
    return redirect("driver_queue:queue")


# ---------------------------------------------------------------- اعلان و موقعیت

def announce_respond(request, token, action):
    """پاسخ از طریق لینک پیامکی (GET تا بدون لاگین کار کند)."""
    try:
        message = services.respond_to_announcement(token, action)
        ok = True
    except services.QueueError as exc:
        message = str(exc)
        ok = False
    return render(request, "driver_queue/announce_result.html", {"ok": ok, "message": message})


@require_POST
def report_location(request):
    """دریافت موقعیت GPS مرورگر در بازه به‌روزرسانی."""
    driver = _driver_from_session(request)
    if not driver:
        return JsonResponse({"ok": False, "error": "unauthorized"}, status=401)
    now = tehran_now()
    services.run_due_jobs(now)
    try:
        payload = json.loads(request.body)
        lat, lng = float(payload["lat"]), float(payload["lng"])
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        return JsonResponse({"ok": False, "error": "bad-payload"}, status=400)
    ticket = services.active_ticket_for(driver)
    if not ticket:
        return JsonResponse({"ok": False, "error": "no-ticket"}, status=404)
    removed = services.report_location(ticket, lat, lng, now)
    return JsonResponse({"ok": True, "removed": removed})


def queue_status_api(request):
    """JSON برای تازه‌سازی خودکار صفحه صف."""
    driver = _driver_from_session(request)
    if not driver:
        return JsonResponse({"authenticated": False})
    now = tehran_now()
    services.run_due_jobs(now)
    data = services.queue_state(now)
    ticket = services.active_ticket_for(driver, now.date())
    data["ticket"] = None
    if ticket:
        data["ticket"] = {
            "number": ticket.number,
            "ahead": services.ahead_of(ticket),
            "pending_announcement": ticket.announcements.filter(response__isnull=True).exists(),
        }
    return JsonResponse(data)
