from decimal import Decimal

from django.db.models import Count, DecimalField, ExpressionWrapper, F, Sum
from django.shortcuts import render

from accounts.decorators import get_user_permissions

from ..models import CommissionDebt, DriverAttendance, ServiceRequest
from ..permissions import urban_access_required, urban_permissions_map
from ..utils import jalali_str, jalali_today, parse_jalali_date, today_start

REMAINING_EXPR = ExpressionWrapper(
    F('amount') - F('paid_amount'),
    output_field=DecimalField(max_digits=15, decimal_places=0))


def _attendance_lists(qs):
    """جدا کردن رانندگان حاضر و غایب از کوئری حضور و غیاب"""
    from fleet.models import Vehicle
    
    # دریافت ناوگان رانندگان
    vehicles: dict[int, Vehicle] = {}
    for v in Vehicle.objects.select_related('driver'):
        vehicles.setdefault(v.driver_id, v)
    
    present_nissan, present_peikan = [], []
    absent_nissan, absent_peikan = [], []

    for item in qs:
        vehicle = vehicles.get(item.driver_id)
        vehicle_type = ''
        if vehicle is not None:
            vehicle_type = vehicle.type.lower()
        is_nissan = 'nisan' in vehicle_type or 'nissan' in vehicle_type
        is_peikan = 'pikan' in vehicle_type or 'peikan' in vehicle_type

        if item.status == DriverAttendance.Status.PRESENT:
            if is_nissan:
                present_nissan.append(item)
            elif is_peikan:
                present_peikan.append(item)
        elif item.status == DriverAttendance.Status.ABSENT:
            if is_nissan:
                absent_nissan.append(item)
            elif is_peikan:
                absent_peikan.append(item)

    return {
        'present': {
            'nissan': present_nissan,
            'peikan': present_peikan,
        },
        'absent': {
            'nissan': absent_nissan,
            'peikan': absent_peikan,
        }
    }


@urban_access_required('can_urban_access_dashboard')
def dashboard(request):
    """داشبورد اختصاصی آژانس برای مدیریت فرایند رانندگان شهری"""
    user = request.user
    start = today_start()

    todays = (ServiceRequest.objects
              .filter(created_at__gte=start)
              .select_related('customer', 'assigned_driver', 'service'))
    done_today = todays.filter(status=ServiceRequest.Status.DONE)

    stats = {
        'all': todays.count(),
        'done': done_today.count(),
        'active': todays.filter(status__in=[
            ServiceRequest.Status.ASSIGNED,
            ServiceRequest.Status.IN_PROGRESS]).count(),
        'pending': todays.filter(status=ServiceRequest.Status.PENDING).count(),
        'income': done_today.aggregate(total=Sum('fare_amount'))['total'] or Decimal(0),
        'commission': done_today.aggregate(total=Sum('commission_amount'))['total'] or Decimal(0),
    }

    # حضور و غیاب امروز (تاریخ شمسی)
    attendance = DriverAttendance.objects.filter(
        date=jalali_today()).select_related('driver')
    attendance_lists = _attendance_lists(attendance)

    # ۵ سرویس آخر روز جاری
    last_services = done_today.order_by('-id')[:5]

    # نمودار رتبه‌بندی رانندگان بر اساس سرویس‌های انجام شده امروز
    ranking = (done_today.filter(assigned_driver__isnull=False)
               .values('assigned_driver_id', 'assigned_driver__name')
               .annotate(total=Count('id'))
               .order_by('-total')[:10])
    max_total = ranking[0]['total'] if ranking else 0
    ranking_rows = [{
        'name': row['assigned_driver__name'],
        'total': row['total'],
        'percent': int(round(row['total'] * 100 / max_total)) if max_total else 0,
    } for row in ranking]

    # بدهکاران کمیسیون پرداخت‌نشده به آژانس
    debtors = (CommissionDebt.objects.filter(is_settled=False)
               .select_related('driver', 'service_request')
               .annotate(remaining=REMAINING_EXPR)
               .order_by('-remaining')[:10])
    total_debt = (CommissionDebt.objects.filter(is_settled=False)
                  .annotate(remaining=REMAINING_EXPR)
                  .aggregate(total=Sum('remaining'))['total'] or Decimal(0))

    context = {
        'urban_perms': urban_permissions_map(user),
        'permissions': get_user_permissions(user),
        'today_jalali': jalali_str(jalali_today()),
        'stats': stats,
        'attendance_lists': attendance_lists,
        'last_services': last_services,
        'ranking_rows': ranking_rows,
        'debtors': debtors,
        'total_debt': total_debt,
    }
    return render(request, 'city_drivers/dashboard.html', context)


@urban_access_required('can_urban_view_reports')
def managers_daily_report(request):
    """گزارش کامل روزانه مدیریت (همه سرویس‌های یک روز شمسی)"""
    selected = parse_jalali_date(request.GET.get('date'), jalali_today())
    gdate = selected.togregorian()

    services = (ServiceRequest.objects.filter(created_at__date=gdate)
                .select_related('customer', 'assigned_driver', 'service', 'rate_card'))

    done = services.filter(status=ServiceRequest.Status.DONE)
    totals = {
        'all': services.count(),
        'done': done.count(),
        'active': services.filter(status__in=[
            ServiceRequest.Status.ASSIGNED,
            ServiceRequest.Status.IN_PROGRESS]).count(),
        'pending': services.filter(status__in=[
            ServiceRequest.Status.PENDING,
            ServiceRequest.Status.APPROVED]).count(),
        'canceled': services.filter(status__in=[
            ServiceRequest.Status.CANCELED,
            ServiceRequest.Status.REJECTED]).count(),
        'income': done.aggregate(total=Sum('fare_amount'))['total'] or Decimal(0),
        'commission': done.aggregate(total=Sum('commission_amount'))['total'] or Decimal(0),
    }

    attendance = DriverAttendance.objects.filter(date=selected).select_related('driver')
    attendance_lists = _attendance_lists(attendance)

    context = {
        'urban_perms': urban_permissions_map(request.user),
        'date_jalali': jalali_str(selected),
        'date_param': jalali_str(selected),
        'services': services,
        'totals': totals,
        'attendance_lists': attendance_lists,
    }
    return render(request, 'city_drivers/managers_daily_report.html', context)
