# dashboard/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Count, Sum
from django.db.models.functions import TruncDay
from django.utils import timezone
from datetime import timedelta
import json
from persiantools.jdatetime import JalaliDate

from accounts.decorators import role_required
from accounts.models import RolePermission
from issuance.models.bijak import Bijak


def is_manager(user):
    return user.is_superuser or user.role == 'manager'


@role_required(['admin'])
def admin_dashboard(request):
    return render(request, 'dashboard/admin_dashboard.html', {'user': request.user})


@user_passes_test(is_manager)
def manager_dashboard(request):
    permissions = None
    if request.user.role == 'manager':
        permissions = RolePermission.objects.filter(role='manager').first()

    # ========================
    # 🔹 آمار هفتگی (شنبه تا شنبه)
    # ========================
    now = timezone.now()
    today = now.date()
    
    # پیدا کردن شنبه هفته جاری (در تقویم میلادی، شنبه = 5)
    # Saturday = 5, Sunday = 6, Monday = 0, ...
    # ما نیاز داریم از شنبه شروع کنیم
    current_weekday = today.weekday()  # Monday=0, Sunday=6
    # محاسبه فاصله تا شنبه قبل (Saturday=5)
    days_since_saturday = (current_weekday - 5) % 7
    week_start = today - timedelta(days=days_since_saturday)
    week_end = week_start + timedelta(days=7)
    
    # فیلتر بارنامه‌های هفته جاری
    weekly_bijaks = Bijak.objects.filter(
        issuance_datetime__date__gte=week_start,
        issuance_datetime__date__lt=week_end
    )
    
    # تعداد بارنامه‌ها در هر روز هفته
    daily_stats = (
        weekly_bijaks
        .annotate(day=TruncDay('issuance_datetime'))
        .values('day')
        .annotate(count=Count('id'), total_insurance=Sum('insurance'), total_freight=Sum('total_fare'))
        .order_by('day')
    )
    
    # آماده‌سازی داده‌ها برای نمودارها
    chart_labels = []
    chart_counts = []
    chart_insurance = []
    chart_commission = []
    
    for stat in daily_stats:
        day_date = stat['day'].date()
        jalali_day = JalaliDate.fromgregorian(date=day_date)
        day_name = {
            0: 'دوشنبه', 1: 'سه‌شنبه', 2: 'چهارشنبه', 
            3: 'پنج‌شنبه', 4: 'جمعه', 5: 'شنبه', 6: 'یکشنبه'
        }[day_date.weekday()]
        
        chart_labels.append(f"{day_name} ({jalali_day.day}/{jalali_day.month})")
        chart_counts.append(stat['count'] or 0)
        chart_insurance.append(int(stat['total_insurance'] or 0))
        # فرض: کمیسیون دفتر باربری ۵٪ از کرایه کل
        commission = int((stat['total_freight'] or 0) * 0.05)
        chart_commission.append(commission)
    
    # مجموع هفته
    total_weekly_count = sum(chart_counts)
    total_weekly_insurance = sum(chart_insurance)
    total_weekly_commission = sum(chart_commission)
    
    context = {
        'user': request.user,
        'permissions': permissions,
        'chart_labels': json.dumps(chart_labels),
        'chart_counts': json.dumps(chart_counts),
        'chart_insurance': json.dumps(chart_insurance),
        'chart_commission': json.dumps(chart_commission),
        'total_weekly_count': total_weekly_count,
        'total_weekly_insurance': total_weekly_insurance,
        'total_weekly_commission': total_weekly_commission,
    }

    return render(request, 'dashboard/manager_dashboard.html', context)


@role_required(['staff', 'manager', 'admin'])
def staff_dashboard(request):
    permissions = None
    if request.user.role == 'staff':
        permissions = RolePermission.objects.filter(role='staff').first()

    return render(request, 'dashboard/staff_dashboard.html', {
        'user': request.user,
        'permissions': permissions
    })


@role_required(['staff', 'manager', 'admin'])
def home_dashboard(request):
    permissions = None
    if request.user.role == 'staff':
        permissions = RolePermission.objects.filter(role='staff').first()

    return render(request, 'dashboard/home_dashboard.html', {
        'user': request.user,
        'permissions': permissions
    })
