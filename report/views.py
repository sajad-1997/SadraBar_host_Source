import json
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Count, Q
from django.db.models.functions import TruncHour, TruncDay, TruncMonth
from django.shortcuts import render
from django.utils import timezone
from persiantools.jdatetime import JalaliDate

from issuance.models import Bijak
from cargo.models import Cargo
from customers.models import Customer
from drivers.models import Driver
from fleet.models import Vehicle

User = get_user_model()


def is_admin_or_manager(user):
    return user.is_superuser or user.role in ['admin', 'manager']


@user_passes_test(is_admin_or_manager)
def report_dashboard(request):
    now = timezone.now()
    start_today = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # -----------------------
    # 🔹 Query پایه
    # -----------------------
    all_users = User.objects.all().order_by('username')
    TYPE_CHOICES = Bijak.TYPE_CHOICES
    VEHICLE_PREFIX = {
        'وانت': 'vant',
        'خاور': 'Bari',
    }
    
    # دریافت لیست منحصر به فرد برای فیلترها
    all_senders = Customer.objects.all().order_by('name')
    all_receivers = Customer.objects.all().order_by('name')
    all_drivers = Driver.objects.all().order_by('name')
    all_cargos = Cargo.objects.all().order_by('name')
    all_vehicles = Vehicle.objects.all().order_by('type')
    
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
        bijaks = bijaks.filter(sender_id=sender)

    if receiver:
        bijaks = bijaks.filter(receiver_id=receiver)

    if driver:
        bijaks = bijaks.filter(driver_id=driver)

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
        bijaks = bijaks.filter(cargo_id=cargo)

    if origin:
        bijaks = bijaks.filter(cargo__origin__icontains=origin)

    if destination:
        bijaks = bijaks.filter(cargo__destination__icontains=destination)

    # فیلتر بازه زمانی
    if date_from:
        try:
            from datetime import datetime
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            bijaks = bijaks.filter(issuance_datetime__gte=date_from_obj)
        except:
            pass

    if date_to:
        try:
            from datetime import datetime
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            # اضافه کردن زمان پایان روز
            date_to_obj = date_to_obj.replace(hour=23, minute=59, second=59)
            bijaks = bijaks.filter(issuance_datetime__lte=date_to_obj)
        except:
            pass

    # حالا این queryset فیلتر شده مبنای همه آمارهاست
    filtered_queryset = bijaks

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

    # ماه شمسی جاری
    today_j = JalaliDate.today()
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

    # آمارگیری بر اساس نوع ناوگان (برای نمودار)
    vehicle_stats = filtered_queryset.values('vehicle__type').annotate(
        count=Count('id')
    ).order_by('vehicle__type')
    
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
    
    # آمارگیری بر اساس مبدا
    origin_stats = filtered_queryset.values('cargo__origin').annotate(
        count=Count('id')
    ).order_by('cargo__origin')
    
    # آمارگیری بر اساس مقصد
    destination_stats = filtered_queryset.values('cargo__destination').annotate(
        count=Count('id')
    ).order_by('cargo__destination')
    
    # آمارگیری بر اساس وضعیت تایید
    approval_stats = filtered_queryset.values('approval_status').annotate(
        count=Count('id')
    ).order_by('approval_status')
    
    # آمارگیری بر اساس وضعیت نهایی
    type_stats = filtered_queryset.values('type').annotate(
        count=Count('id')
    ).order_by('type')

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
            {'hour': d['hour'].strftime('%Y-%m-%d %H:%M'), 'total': d['total']}
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
            {'day': d['day'].strftime('%Y-%m-%d'), 'total': d['total']}
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
            {'month': d['month'].strftime('%Y-%m'), 'total': d['total']}
            for d in data if d['month'] is not None
        ]

    chart_data_all = json.dumps(get_chart_data(filtered_queryset))
    chart_data_daily = json.dumps(get_daily_chart_data(filtered_queryset))
    chart_data_monthly = json.dumps(get_monthly_chart_data(filtered_queryset))
    
    # -----------------------
    # 🔹 context
    # -----------------------
    context = {
        'bijaks': filtered_queryset,
        'all_users': all_users,
        'all_senders': all_senders,
        'all_receivers': all_receivers,
        'all_drivers': all_drivers,
        'all_cargos': all_cargos,
        'all_vehicles': all_vehicles,

        # آمارها
        'daily_24_count': daily_24_count,
        'today_count': today_count,
        'daily_work_count': daily_work_count,
        'daily_after_hours_count': daily_after_hours_count,
        'monthly_count': monthly_count,
        'yearly_count': yearly_count,
        'vant_count': vant_count,
        'bari_count': bari_count,

        # آمارهای تفکیکی
        'vehicle_stats': list(vehicle_stats),
        'user_stats': list(user_stats),
        'sender_stats': list(sender_stats),
        'receiver_stats': list(receiver_stats),
        'driver_stats': list(driver_stats),
        'cargo_stats': list(cargo_stats),
        'origin_stats': list(origin_stats),
        'destination_stats': list(destination_stats),
        'approval_stats': list(approval_stats),
        'type_stats': list(type_stats),

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
