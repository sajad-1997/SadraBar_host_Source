import json
from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Count, Q
from django.db.models.functions import TruncHour, TruncDay, TruncMonth
from django.shortcuts import render
from django.utils import timezone
from persiantools.jdatetime import JalaliDate

from issuance.models import Bijak

User = get_user_model()

# حداکثر تعداد آیتم‌هایی که در کارت نتیجه فیلتر نمایش داده می‌شود
RESULT_ITEMS_LIMIT = 100


def is_admin_or_manager(user):
    from accounts.decorators import ROLE_ADMIN, ROLE_MANAGER
    return user.is_superuser or user.role in [ROLE_ADMIN, ROLE_MANAGER]


# -----------------------
# 🔹 توابع کمکی
# -----------------------
def _to_ascii_digits(value):
    """تبدیل ارقام فارسی به لاتین"""
    return value.translate(str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789'))


def _parse_filter_date(value):
    """
    تبدیل تاریخ فیلتر به تاریخ میلادی برای کوئری.
    از تقویم شمسی (YYYY/MM/DD) و در صورت نیاز میلادی (YYYY-MM-DD) پشتیبانی می‌کند.
    """
    if not value:
        return None
    value = _to_ascii_digits(value.strip())
    for fmt in ('%Y/%m/%d', '%Y-%m-%d'):
        try:
            parsed = datetime.strptime(value, fmt).date()
        except ValueError:
            continue
        if fmt == '%Y/%m/%d':
            try:
                return JalaliDate(parsed.year, parsed.month, parsed.day).to_gregorian()
            except (ValueError, OverflowError):
                return None
        return parsed
    return None


def _vehicle_type_fa(vehicle_type):
    """نام فارسی نوع ناوگان برای نمایش در نمودارها"""
    if not vehicle_type:
        return 'بدون ناوگان'
    lowered = vehicle_type.strip().lower()
    if 'vant' in lowered or 'وانت' in vehicle_type:
        return 'وانت'
    if 'bari' in lowered or 'خاور' in vehicle_type:
        return 'خاور'
    return vehicle_type.strip()


def _jalali_date_str(g_date):
    j = JalaliDate(g_date)
    return f"{j.year}/{j.month:02d}/{j.day:02d}"


def _jalali_datetime_str(dt_value):
    """
    تاریخ و ساعت واقعی صدور (ثبت سیستمی) به تقویم شمسی؛
    نه تاریخی که کاربر هنگام صدور بارنامه به‌صورت دستی وارد کرده است.
    """
    if not dt_value:
        return '—'
    if timezone.is_naive(dt_value):
        local_dt = dt_value
    else:
        local_dt = timezone.localtime(dt_value)
    return f"{_jalali_date_str(local_dt.date())} - {local_dt:%H:%M}"


@user_passes_test(is_admin_or_manager)
def report_dashboard(request):
    now = timezone.now()
    start_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_j = JalaliDate.today()

    # -----------------------
    # 🔹 Query پایه
    # -----------------------
    # تمامی کاربران سیستم برای فیلتر کاربر صادرکننده (بدون هیچ محدودیتی)
    all_users = User.objects.all().order_by('username')
    TYPE_CHOICES = Bijak.TYPE_CHOICES
    VEHICLE_PREFIX = {
        'وانت': 'vant',
        'خاور': 'Bari',
    }

    bijaks = Bijak.objects.all().select_related(
        'sender',
        'receiver',
        'driver',
        'vehicle',
        'created_by',
        'cargo'
    ).order_by('-id')

    # -----------------------
    # 🔹 دریافت فیلترها
    # -----------------------
    sender = request.GET.get('sender', '').strip()
    receiver = request.GET.get('receiver', '').strip()
    driver = request.GET.get('driver', '').strip()
    vehicle = request.GET.get('vehicle', '').strip()
    approval_status = request.GET.get('approval_status', '').strip()
    type_filter = request.GET.get('type', '').strip()
    created_by = request.GET.get('created_by', '').strip()
    cargo = request.GET.get('cargo', '').strip()
    origin = request.GET.get('origin', '').strip()
    destination = request.GET.get('destination', '').strip()
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()

    # -----------------------
    # 🔹 اعمال فیلتر ترکیبی
    # -----------------------
    if sender:
        # جستجو بر اساس نام فرستنده
        bijaks = bijaks.filter(sender__name__icontains=sender)

    if receiver:
        # جستجو بر اساس نام گیرنده
        bijaks = bijaks.filter(receiver__name__icontains=receiver)

    if driver:
        # جستجو بر اساس نام راننده
        bijaks = bijaks.filter(driver__name__icontains=driver)

    if vehicle in VEHICLE_PREFIX:
        prefix = VEHICLE_PREFIX[vehicle]
        bijaks = bijaks.filter(vehicle__type__istartswith=prefix)

    if approval_status:
        bijaks = bijaks.filter(approval_status=approval_status)

    if type_filter:
        bijaks = bijaks.filter(type=type_filter)

    if created_by:
        bijaks = bijaks.filter(created_by_id=created_by)

    if cargo:
        # جستجو بر اساس نام محموله
        bijaks = bijaks.filter(cargo__name__icontains=cargo)

    if origin:
        # جستجو بر اساس نام شهر یا استان مبدا (به جای کد شهر)
        bijaks = bijaks.filter(
            Q(cargo__origin__name__icontains=origin) |
            Q(cargo__origin__province__name__icontains=origin)
        )

    if destination:
        # جستجو بر اساس نام شهر یا استان مقصد (به جای کد شهر)
        bijaks = bijaks.filter(
            Q(cargo__destination__name__icontains=destination) |
            Q(cargo__destination__province__name__icontains=destination)
        )

    # فیلتر بازه زمانی (با تقویم شمسی)
    g_date_from = _parse_filter_date(date_from)
    if g_date_from:
        bijaks = bijaks.filter(issuance_datetime__date__gte=g_date_from)

    g_date_to = _parse_filter_date(date_to)
    if g_date_to:
        bijaks = bijaks.filter(issuance_datetime__date__lte=g_date_to)

    # حالا این queryset فیلتر شده مبنای همه آمارهاست
    filtered_queryset = bijaks

    # آیا فیلتری توسط کاربر اعمال شده است؟
    has_filters = bool(
        sender or receiver or driver or vehicle or approval_status or
        type_filter or created_by or cargo or origin or destination or
        date_from or date_to
    )

    # -----------------------
    # 🔹 ساعت کاری
    # -----------------------
    work_start = start_today.replace(hour=8)
    work_end = start_today.replace(hour=17)

    # -----------------------
    # 🔹 آمارگیری
    # -----------------------

    # ۲۴ ساعت اخیر
    last_24_hours = timezone.now() - timedelta(hours=24)
    daily_24_count = filtered_queryset.filter(created_at__gte=last_24_hours).count()

    # امروز
    today_count = filtered_queryset.filter(created_at__gte=start_today).count()

    # داخل ساعت کاری امروز
    daily_work_count = filtered_queryset.filter(
        created_at__gte=work_start,
        created_at__lte=work_end
    ).count()

    # خارج ساعت کاری امروز
    daily_after_hours_count = today_count - daily_work_count

    # هفته شمسی جاری (از شنبه این هفته تا جمعه) — weekday جلالی: شنبه = 0
    week_start_j = today_j - timedelta(days=today_j.weekday())
    week_start_date = week_start_j.to_gregorian()
    week_end_date = (week_start_j + timedelta(days=6)).to_gregorian()
    weekly_count = filtered_queryset.filter(
        created_at__date__gte=week_start_date,
        created_at__date__lte=week_end_date,
    ).count()

    # تاریخ شمسی شروع و پایان هفته برای نمایش در کارت
    week_start_fa = _jalali_date_str(week_start_date)
    week_end_fa = _jalali_date_str(week_end_date)

    # ماه شمسی جاری
    month_start = today_j.replace(day=1).to_gregorian()
    next_month = today_j.month + 1 if today_j.month < 12 else 1
    next_month_year = today_j.year if today_j.month < 12 else today_j.year + 1
    month_end = JalaliDate(next_month_year, next_month, 1).to_gregorian() - timedelta(days=1)

    monthly_count = filtered_queryset.filter(
        issuance_datetime__date__gte=month_start,
        issuance_datetime__date__lte=month_end
    ).count()

    # سال شمسی جاری
    year_start = JalaliDate(today_j.year, 1, 1).to_gregorian()
    year_end = JalaliDate(today_j.year, 12, 29).to_gregorian()

    yearly_count = filtered_queryset.filter(
        issuance_datetime__date__gte=year_start,
        issuance_datetime__date__lte=year_end
    ).count()

    # بر اساس نوع ناوگان
    vant_count = filtered_queryset.filter(vehicle__type__istartswith='vant').count()
    bari_count = filtered_queryset.filter(vehicle__type__istartswith='Bari').count()

    # آمارگیری بر اساس نوع ناوگان (برای نمودار) با نام فارسی
    _vehicle_counts = {}
    for row in filtered_queryset.values('vehicle__type').annotate(count=Count('id')):
        label = _vehicle_type_fa(row['vehicle__type'])
        _vehicle_counts[label] = _vehicle_counts.get(label, 0) + row['count']
    vehicle_stats = [
        {'label': label, 'count': count}
        for label, count in sorted(_vehicle_counts.items(), key=lambda item: -item[1])
    ]

    # آمارگیری بر اساس کاربر صادر کننده
    user_stats = filtered_queryset.values('created_by__username').annotate(
        count=Count('id')
    ).order_by('created_by__username')

    # آمارگیری بر اساس فرستنده
    sender_stats = filtered_queryset.values('sender__name').annotate(
        count=Count('id')
    ).order_by('sender__name')

    # آمارگیری بر اساس گیرنده
    receiver_stats = filtered_queryset.values('receiver__name').annotate(
        count=Count('id')
    ).order_by('receiver__name')

    # آمارگیری بر اساس راننده
    driver_stats = filtered_queryset.values('driver__name').annotate(
        count=Count('id')
    ).order_by('driver__name')

    # آمارگیری بر اساس محموله
    cargo_stats = filtered_queryset.values('cargo__name').annotate(
        count=Count('id')
    ).order_by('cargo__name')

    # آمارگیری بر اساس مبدا — نمایش نام استان و شهر به جای کد
    origin_rows = filtered_queryset.values(
        'cargo__origin__province__name', 'cargo__origin__name'
    ).annotate(count=Count('id')).order_by('-count')
    origin_stats = [
        {
            'label': f"{row['cargo__origin__province__name'] or 'نامشخص'} - "
                     f"{row['cargo__origin__name'] or 'نامشخص'}",
            'count': row['count'],
        }
        for row in origin_rows
    ]

    # آمارگیری بر اساس مقصد — نمایش نام استان و شهر به جای کد
    destination_rows = filtered_queryset.values(
        'cargo__destination__province__name', 'cargo__destination__name'
    ).annotate(count=Count('id')).order_by('-count')
    destination_stats = [
        {
            'label': f"{row['cargo__destination__province__name'] or 'نامشخص'} - "
                     f"{row['cargo__destination__name'] or 'نامشخص'}",
            'count': row['count'],
        }
        for row in destination_rows
    ]

    # آمارگیری بر اساس وضعیت تایید
    approval_stats = filtered_queryset.values('approval_status').annotate(
        count=Count('id')
    ).order_by('approval_status')

    # آمارگیری بر اساس وضعیت نهایی
    type_stats = filtered_queryset.values('type').annotate(
        count=Count('id')
    ).order_by('type')

    # -----------------------
    # 🔹 کارت نتیجه فیلتر
    # -----------------------
    filtered_count = filtered_queryset.count() if has_filters else 0

    # آیتم‌های نتیجه فیلتر: با وضعیت، صادرکننده (کاربر/نقش) و تاریخ و ساعت
    # واقعی صدور (ثبت سیستمی) به شمسی — نه تاریخی که کاربر دستی وارد کرده است
    result_items = []
    if has_filters:
        for b in filtered_queryset[:RESULT_ITEMS_LIMIT]:
            issuer = b.created_by
            result_items.append({
                'id': b.id,
                'tracking_code': b.tracking_code,
                'approval_status': b.approval_status or 'unknown',
                'approval_display': b.get_approval_status_display() or 'نامشخص',
                'type_display': b.get_type_display() or 'نامشخص',
                'issuer': issuer.username if issuer else 'نامشخص',
                'issuer_role': (
                    dict(User.ROLE_CHOICES).get(issuer.role, issuer.role)
                    if issuer and issuer.role else '—'
                ),
                'issued_at': _jalali_datetime_str(b.created_at),
            })

    # -----------------------
    # 🔹 داده چارت
    # -----------------------
    def get_chart_data(queryset):
        data = (
            queryset.exclude(issuance_datetime__isnull=True)
                .annotate(hour=TruncHour('issuance_datetime'))
                .values('hour')
                .annotate(total=Count('id'))
                .order_by('hour')
        )
        return [
            {'hour': f"{d['hour']:%Y/%m/%d %H}:00", 'total': d['total']}
            for d in data if d['hour'] is not None
        ]

    def get_daily_chart_data(queryset):
        data = (
            queryset.exclude(issuance_datetime__isnull=True)
                .annotate(day=TruncDay('issuance_datetime'))
                .values('day')
                .annotate(total=Count('id'))
                .order_by('day')
        )
        return [
            {'day': f"{d['day']:%Y/%m/%d}", 'total': d['total']}
            for d in data if d['day'] is not None
        ]

    def get_monthly_chart_data(queryset):
        data = (
            queryset.exclude(issuance_datetime__isnull=True)
                .annotate(month=TruncMonth('issuance_datetime'))
                .values('month')
                .annotate(total=Count('id'))
                .order_by('month')
        )
        return [
            {'month': f"{d['month']:%Y/%m}", 'total': d['total']}
            for d in data if d['month'] is not None
        ]

    chart_data_all = json.dumps(get_chart_data(filtered_queryset))
    chart_data_daily = json.dumps(get_daily_chart_data(filtered_queryset))
    chart_data_monthly = json.dumps(get_monthly_chart_data(filtered_queryset))

    # -----------------------
    # 🔹 context
    # -----------------------
    context = {
        # تمامی کاربران سیستم برای فیلتر کاربر صادرکننده
        'all_users': all_users,

        # آمارها
        'daily_24_count': daily_24_count,
        'today_count': today_count,
        'daily_work_count': daily_work_count,
        'daily_after_hours_count': daily_after_hours_count,
        'weekly_count': weekly_count,
        'week_start_fa': week_start_fa,
        'week_end_fa': week_end_fa,
        'monthly_count': monthly_count,
        'yearly_count': yearly_count,
        'vant_count': vant_count,
        'bari_count': bari_count,

        # آمارهای تفکیکی
        'vehicle_stats': vehicle_stats,
        'user_stats': list(user_stats),
        'sender_stats': list(sender_stats),
        'receiver_stats': list(receiver_stats),
        'driver_stats': list(driver_stats),
        'cargo_stats': list(cargo_stats),
        'origin_stats': origin_stats,
        'destination_stats': destination_stats,
        'approval_stats': list(approval_stats),
        'type_stats': list(type_stats),

        # نتیجه فیلتر
        'has_filters': has_filters,
        'filtered_count': filtered_count,
        'result_items': result_items,
        'result_items_limit': RESULT_ITEMS_LIMIT,

        'chart_data_all': chart_data_all,
        'chart_data_daily': chart_data_daily,
        'chart_data_monthly': chart_data_monthly,

        # نگه داشتن مقادیر فیلتر
        'filters': {
            'sender': sender,
            'receiver': receiver,
            'driver': driver,
            'vehicle': vehicle,
            'approval_status': approval_status,
            'type': type_filter,
            'created_by': created_by,
            'cargo': cargo,
            'origin': origin,
            'destination': destination,
            'date_from': date_from,
            'date_to': date_to,
        },
        'TYPE_CHOICES': TYPE_CHOICES,
    }

    return render(request, 'report/report_dashboard.html', context)
