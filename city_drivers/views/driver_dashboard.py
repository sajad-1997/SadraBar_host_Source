from decimal import Decimal
from datetime import datetime, timedelta, date
from django.apps import apps
from django.db.models import Count, Sum, Q
from django.shortcuts import render, redirect
from django.http import JsonResponse
import jdatetime
from django_jalali.db import models as jmodels

from .. import services
from ..models import ServiceRequest, DriverLocation, DriverAttendance
from ..utils import jalali_today, jalali_str, today_start

SESSION_DRIVER = "city_drivers_driver_id"


def _driver_model():
    """مدل راننده ماژول رانندگان"""
    return apps.get_model('drivers.Driver')


def _driver_from_session(request):
    """دریافت راننده از جلسه"""
    driver_id = request.session.get(SESSION_DRIVER)
    return _driver_model().objects.filter(pk=driver_id).first() if driver_id else None


def driver_login_required(view_func):
    """دکوراتور برای بررسی احراز هویت راننده"""
    def wrapper(request, *args, **kwargs):
        driver = _driver_from_session(request)
        if not driver:
            return redirect('city_drivers:driver_login')
        request.driver = driver
        return view_func(request, *args, **kwargs)
    return wrapper


def driver_login(request):
    """صفحه ورود راننده"""
    if _driver_from_session(request):
        return redirect('city_drivers:driver_dashboard')
    
    error = None
    if request.method == 'POST':
        phone = request.POST.get('phone')
        driver = _driver_model().objects.filter(phone=phone).first()
        if driver:
            request.session[SESSION_DRIVER] = driver.pk
            return redirect('city_drivers:driver_dashboard')
        else:
            error = 'شماره تلفن در سیستم ثبت نشده است'
    
    return render(request, 'city_drivers/driver/login.html', {'error': error})


def driver_logout(request):
    """خروج راننده"""
    request.session.pop(SESSION_DRIVER, None)
    return redirect('city_drivers:driver_login')


@driver_login_required
def driver_dashboard(request):
    """داشبورد اختصاصی راننده شهری"""
    driver = request.driver
    today = date.today()
    start_of_day = today_start()
    
    # محاسبه رتبه راننده بر اساس سرویس‌های انجام شده امروز
    today_services = ServiceRequest.objects.filter(
        created_at__gte=start_of_day,
        status=ServiceRequest.Status.DONE,
        assigned_driver__isnull=False
    ).values('assigned_driver_id', 'assigned_driver__name').annotate(
        total=Count('id')
    ).order_by('-total')
    
    driver_rank = 0
    for idx, item in enumerate(today_services, 1):
        if item['assigned_driver_id'] == driver.id:
            driver_rank = idx
            break
    
    # سرویس‌های راننده بر اساس فیلتر (هفتگی/ماهانه/سالانه)
    period = request.GET.get('period', 'daily')
    
    if period == 'weekly':
        start_date = today - timedelta(days=7)
    elif period == 'monthly':
        start_date = today - timedelta(days=30)
    elif period == 'yearly':
        start_date = today - timedelta(days=365)
    else:  # daily
        start_date = start_of_day
    
    driver_services = ServiceRequest.objects.filter(
        assigned_driver=driver,
        created_at__gte=start_date
    ).select_related('customer', 'service').order_by('-created_at')
    
    # درآمد امروز
    today_income = ServiceRequest.objects.filter(
        assigned_driver=driver,
        created_at__gte=start_of_day,
        status=ServiceRequest.Status.DONE
    ).aggregate(total=Sum('fare_amount'))['total'] or Decimal(0)
    
    # نمودار درآمد روزانه (۷ روز گذشته)
    daily_income_data = []
    for i in range(7):
        day = today - timedelta(days=i)
        day_start = datetime.combine(day, datetime.min.time())
        day_end = datetime.combine(day, datetime.max.time())
        
        income = ServiceRequest.objects.filter(
            assigned_driver=driver,
            created_at__range=(day_start, day_end),
            status=ServiceRequest.Status.DONE
        ).aggregate(total=Sum('fare_amount'))['total'] or Decimal(0)
        
        jd = jdatetime.date.fromgregorian(date=day)
        daily_income_data.append({
            'date': jd.strftime('%Y/%m/%d'),
            'income': int(income)
        })
    
    daily_income_data.reverse()
    
    # سرویس در حال انجام: درخواستی که راننده هم‌اکنون در حال انجام آن است
    current_service = (ServiceRequest.objects
                       .filter(assigned_driver=driver,
                               status=ServiceRequest.Status.IN_PROGRESS)
                       .select_related('customer', 'service', 'rate_card')
                       .order_by('id')
                       .first())

    # سرویس بعدی تخصیص‌یافته: اولین درخواست فعال در انتظار قبول/شروع راننده
    next_service = (ServiceRequest.objects
                    .filter(assigned_driver=driver,
                            status__in=[
                                ServiceRequest.Status.PENDING,
                                ServiceRequest.Status.APPROVED,
                                ServiceRequest.Status.ASSIGNED])
                    .select_related('customer', 'service', 'rate_card')
                    .order_by('id')
                    .first())

    # آیا راننده سرویس بعدی را قبول کرده است؟ (برای نمایش دکمه قبول/شروع)
    next_service_accepted = False
    if next_service:
        next_service_accepted = next_service.status_logs.filter(
            to_status=ServiceRequest.Status.ASSIGNED,
            note__icontains='قبول سرویس').exists()
    
    # آمار سرویس‌ها برای کارت لیست
    service_stats = {
        'daily': driver_services.filter(created_at__gte=start_of_day).count(),
        'weekly': driver_services.filter(created_at__gte=today - timedelta(days=7)).count(),
        'monthly': driver_services.filter(created_at__gte=today - timedelta(days=30)).count(),
        'yearly': driver_services.filter(created_at__gte=today - timedelta(days=365)).count(),
    }
    
    context = {
        'driver': driver,
        'driver_rank': driver_rank,
        'today_jalali': jalali_str(jalali_today()),
        'current_time': datetime.now().strftime('%H:%M:%S'),
        'driver_services': driver_services,
        'period': period,
        'service_stats': service_stats,
        'today_income': today_income,
        'daily_income_data': daily_income_data,
        'current_service': current_service,
        'next_service': next_service,
        'next_service_accepted': next_service_accepted,
    }
    
    return render(request, 'city_drivers/driver/dashboard.html', context)


@driver_login_required
def update_service_status(request, service_id):
    """به‌روزرسانی وضعیت سرویس توسط راننده"""
    driver = request.driver
    service = ServiceRequest.objects.filter(
        id=service_id,
        assigned_driver=driver
    ).first()
    
    if not service:
        return redirect('city_drivers:driver_dashboard')
    
    action = request.POST.get('action')
    
    if action == 'accept':
        # قبول سرویس توسط راننده: وضعیت به «تخصیص یافته» تغییر می‌کند
        already_accepted = service.status_logs.filter(
            to_status=ServiceRequest.Status.ASSIGNED,
            note__icontains='قبول سرویس').exists()
        if not already_accepted:
            services.change_status(
                service, ServiceRequest.Status.ASSIGNED,
                note='قبول سرویس توسط راننده')
            # راننده پس از قبول سرویس در وضعیت «در حال انجام سرویس» قرار می‌گیرد
            DriverLocation.refresh_location(
                driver, status=DriverLocation.Status.BUSY,
                current_request=service)
    elif action == 'start':
        # شروع سرویس توسط راننده: وضعیت به «در حال انجام» تغییر می‌کند
        accepted = service.status_logs.filter(
            to_status=ServiceRequest.Status.ASSIGNED,
            note__icontains='قبول سرویس').exists()
        if accepted:
            services.change_status(
                service, ServiceRequest.Status.IN_PROGRESS,
                note='شروع سرویس توسط راننده')
    elif action == 'arrive_origin':
        # ثبت رسیدن به مبدا بارگیری (بدون تغییر وضعیت سرویس)
        if service.status == ServiceRequest.Status.IN_PROGRESS:
            services.log_status(
                service, service.status, service.status,
                note='رسیدن به مبدا بارگیری توسط راننده')
    elif action == 'arrive_destination':
        # ثبت رسیدن به مقصد (بدون تغییر وضعیت سرویس)
        if service.status == ServiceRequest.Status.IN_PROGRESS:
            services.log_status(
                service, service.status, service.status,
                note='رسیدن به مقصد توسط راننده')
    elif action == 'unload':
        # تخلیه و تکمیل سرویس توسط راننده
        # (بروزرسانی کرایه، ثبت بدهی کمیسیون و پاک‌سازی موقعیت راننده)
        services.change_status(
            service, ServiceRequest.Status.DONE,
            note='تخلیه و تکمیل سرویس توسط راننده')
    
    service.save()
    return redirect('city_drivers:driver_dashboard')


@driver_login_required
def api_driver_queue(request):
    """API برای دریافت لیست نوبت رانندگان (AJAX) - بر اساس حضور و غیاب و نوع ناوگان از ماژول fleet"""
    from fleet.models import Vehicle
    
    today_jalali = jalali_today()
    
    # دریافت رانندگان حاضر امروز از سیستم حضور و غیاب شهری
    attendances = DriverAttendance.objects.filter(
        date=today_jalali,
        status=DriverAttendance.Status.PRESENT
    ).select_related('driver').order_by('check_in')
    
    # دریافت ناوگان رانندگان
    vehicles = {
        v.driver_id: v
        for v in Vehicle.objects.select_related('driver')
    }
    
    # جدا کردن بر اساس نوع ناوگان
    nissan_queue = []
    peikan_queue = []
    
    nissan_idx = 1
    peikan_idx = 1
    
    for attendance in attendances:
        vehicle = vehicles.get(attendance.driver_id)
        
        # تعیین نوع ناوگان بر اساس فیلد type از ماژول fleet
        vehicle_type = 'other'
        if vehicle:
            if 'nissan' in vehicle.type:
                vehicle_type = 'nissan'
            elif 'pikan' in vehicle.type:
                vehicle_type = 'peikan'
        
        driver_data = {
            'number': 0,
            'driver_name': attendance.driver.name,
            'driver_phone': attendance.driver.phone,
            'joined_at': attendance.check_in.strftime('%H:%M') if attendance.check_in else attendance.created_at.strftime('%H:%M'),
            'vehicle_type': vehicle_type,
        }
        
        if vehicle_type == 'nissan':
            driver_data['number'] = nissan_idx
            nissan_queue.append(driver_data)
            nissan_idx += 1
        elif vehicle_type == 'peikan':
            driver_data['number'] = peikan_idx
            peikan_queue.append(driver_data)
            peikan_idx += 1
        else:
            # سایر ناوگان‌ها را به نیسان اضافه می‌کنیم (یا می‌توان جداگانه نمایش داد)
            driver_data['number'] = nissan_idx
            nissan_queue.append(driver_data)
            nissan_idx += 1
    
    return JsonResponse({
        'nissan_queue': nissan_queue,
        'peikan_queue': peikan_queue,
        'nissan_count': len(nissan_queue),
        'peikan_count': len(peikan_queue),
        'total_count': len(attendances),
        'date': jalali_str(today_jalali)
    })

