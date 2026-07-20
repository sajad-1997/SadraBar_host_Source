import json
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Count
from django.db.models.functions import TruncHour
from django.shortcuts import render
from django.utils import timezone
from persiantools.jdatetime import JalaliDate

from issuance.models import Bijak

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
    bijaks = Bijak.objects.all().select_related(
        'sender',
        'receiver',
        'driver',
        'vehicle',
        'created_by'
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

    # -----------------------
    # 🔹 اعمال فیلتر ترکیبی
    # -----------------------
    if sender:
        bijaks = bijaks.filter(sender__name__icontains=sender)

    if receiver:
        bijaks = bijaks.filter(receiver__name__icontains=receiver)

    if driver:
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

    chart_data_all = json.dumps(get_chart_data(filtered_queryset))
    
# obj = filtered_queryset.order_by('created_at').first()
# print("Server now:", timezone.now())
#     if obj:
#     print("First today record ID:", obj.id)
          
    # -----------------------
    # 🔹 context
    # -----------------------
    context = {
        'bijaks': filtered_queryset,
        'all_users': all_users,

        # آمارها
        'daily_24_count': daily_24_count,
        'today_count': today_count,
        'daily_work_count': daily_work_count,
        'daily_after_hours_count': daily_after_hours_count,
        'monthly_count': monthly_count,
        'yearly_count': yearly_count,
        'vant_count': vant_count,
        'bari_count': bari_count,

        'chart_data_all': chart_data_all,

        # نگه داشتن مقادیر فیلتر
        'filters': {
            'sender': sender,
            'receiver': receiver,
            'driver': driver,
            'vehicle': vehicle,
            'approval_status': approval_status,
            'type': type_filter,
            'created_by': created_by,
        },
        'TYPE_CHOICES': TYPE_CHOICES,
    }

    

    return render(request, 'report/report_dashboard.html', context)
