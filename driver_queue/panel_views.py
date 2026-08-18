from datetime import date as date_type

from django.apps import apps
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from . import conf, services
from .forms import StaffUserAddForm
from .models import QueueLog, QueueProfile, QueueStaff, QueueTicket
from .permissions import manager_required, panel_required
from .utils import tehran_now


def _driver_model():
    return apps.get_model(conf.DRIVER_MODEL)


def _parse_day(value):
    try:
        return date_type.fromisoformat(value)
    except (TypeError, ValueError):
        return tehran_now().date()


def _base_context(request):
    return {
        "is_manager": getattr(request, "queue_role", None) == QueueStaff.Role.MANAGER,
    }


def _panel_redirect(day):
    return f"{reverse('driver_queue:panel_dashboard')}?date={day.isoformat()}"


# ---------------------------------------------------------------- داشبورد

@panel_required()
def dashboard(request):
    now = tehran_now()
    services.run_due_jobs(now)  # اعلان ۱۱:۰۰ / حذف ۱۱:۱۵ بدون Celery
    day = _parse_day(request.GET.get("date"))
    q = request.GET.get("q", "").strip()

    tickets = (QueueTicket.objects.filter(date=day)
               .select_related("driver").order_by("number", "joined_at"))
    approved_ids = set(QueueProfile.objects.filter(
        driver_id__in=tickets.values_list("driver_id", flat=True),
        office_approved=True).values_list("driver_id", flat=True))

    search_results = list(services.search_drivers(q)) if q else []
    search_approved_ids = set(
        QueueProfile.objects.filter(driver__in=search_results, office_approved=True)
        .values_list("driver_id", flat=True)) if search_results else set()

    context = {
        **_base_context(request),
        "active_tab": "dashboard",
        "day": day,
        "today": now.date(),
        "state": services.queue_state(now),
        "tickets": tickets,
        "approved_ids": approved_ids,
        "q": q,
        "search_results": search_results,
        "search_approved_ids": search_approved_ids,
        "waiting_count": tickets.filter(status=QueueTicket.Status.WAITING).count(),
        "logs": QueueLog.objects.select_related("user", "driver")[:15],
    }
    return render(request, "driver_queue/panel/dashboard.html", context)


# ---------------------------------------------------------------- عملیات نوبت

@require_POST
@panel_required()
def ticket_add(request):
    driver = get_object_or_404(_driver_model(), pk=request.POST.get("driver_pk"))
    day = _parse_day(request.POST.get("date"))
    try:
        services.staff_add_ticket(driver, day, actor=request.user)
        messages.success(request, f"نوبت برای «{driver.name}» در تاریخ {day} ثبت شد.")
    except services.QueueError as exc:
        messages.error(request, str(exc))
    return redirect(_panel_redirect(day))


@require_POST
@panel_required()
def ticket_loaded(request, pk):
    ticket = get_object_or_404(QueueTicket, pk=pk)
    day = ticket.date
    try:
        services.staff_mark_loaded(ticket, actor=request.user)
        messages.success(request, "بارگیری ثبت شد و راننده از صف خارج شد.")
    except services.QueueError as exc:
        messages.error(request, str(exc))
    return redirect(_panel_redirect(day))


@require_POST
@panel_required()
def ticket_remove(request, pk):
    ticket = get_object_or_404(QueueTicket, pk=pk)
    day = ticket.date
    services.staff_remove_ticket(ticket, actor=request.user)
    messages.success(request, "نوبت حذف شد و لیست به‌روز گردید.")
    return redirect(_panel_redirect(day))


# ---------------------------------------------------------------- راننده

@panel_required()
def driver_detail(request, pk):
    driver = get_object_or_404(_driver_model(), pk=pk)
    profile, _ = QueueProfile.objects.get_or_create(driver=driver)
    now = tehran_now()
    context = {
        **_base_context(request),
        "active_tab": "dashboard",
        "driver": driver,
        "profile": profile,
        "today": now.date(),
        "today_ticket": QueueTicket.objects.filter(driver=driver, date=now.date()).first(),
        "history": QueueTicket.objects.filter(driver=driver).order_by("-date", "-joined_at")[:10],
    }
    return render(request, "driver_queue/panel/driver_detail.html", context)


@require_POST
@panel_required()
def driver_approve(request, pk):
    driver = get_object_or_404(_driver_model(), pk=pk)
    approved = request.POST.get("approve") == "1"
    services.approve_driver(driver, actor=request.user, approved=approved)
    messages.success(request,
                     "راننده تایید شد." if approved else "تایید راننده لغو شد.")
    return redirect("driver_queue:panel_driver_detail", pk=pk)


# ---------------------------------------------------------------- کاربران مجاز (فقط مدیریت)

@manager_required
def users_list(request):
    context = {
        **_base_context(request),
        "active_tab": "users",
        "staff_list": QueueStaff.objects.select_related("user", "approved_by")
        .order_by("-created_at"),
        "form": StaffUserAddForm(),
    }
    return render(request, "driver_queue/panel/users.html", context)


@require_POST
@manager_required
def user_add(request):
    form = StaffUserAddForm(request.POST)
    if form.is_valid():
        staff = QueueStaff.objects.create(user=form.user,
                                          role=form.cleaned_data["role"])
        QueueLog.objects.create(user=request.user,
                                action=QueueLog.Action.STAFF_ADD,
                                detail=str(form.user))
        messages.success(request,
                         f"کاربر «{form.user}» با نقش «{staff.get_role_display()}» اضافه شد.")
    else:
        errors = "؛ ".join(v[0] for v in form.errors.values())
        messages.error(request, f"خطا در افزودن کاربر: {errors}")
    return redirect("driver_queue:panel_users")


@require_POST
@manager_required
def user_toggle(request, pk):
    staff = get_object_or_404(QueueStaff, pk=pk)
    if staff.role == QueueStaff.Role.MANAGER:
        messages.error(request, "نقش مدیریت نیازی به تایید ندارد.")
        return redirect("driver_queue:panel_users")
    staff.approved = not staff.approved
    staff.approved_by = request.user if staff.approved else None
    staff.approved_at = tehran_now() if staff.approved else None
    staff.save(update_fields=["approved", "approved_by", "approved_at"])
    QueueLog.objects.create(
        user=request.user,
        action=(QueueLog.Action.STAFF_APPROVE if staff.approved
                else QueueLog.Action.STAFF_UNAPPROVE),
        detail=str(staff.user))
    messages.success(request, "وضعیت دسترسی کاربر به‌روز شد.")
    return redirect("driver_queue:panel_users")


@require_POST
@manager_required
def user_remove(request, pk):
    staff = get_object_or_404(QueueStaff, pk=pk)
    if staff.user_id == request.user.id:
        messages.error(request, "نمی‌توانید دسترسی خود را حذف کنید.")
    else:
        detail = str(staff.user)
        staff.delete()
        QueueLog.objects.create(user=request.user,
                                action=QueueLog.Action.STAFF_REMOVE, detail=detail)
        messages.success(request, "کاربر از پنل حذف شد.")
    return redirect("driver_queue:panel_users")
