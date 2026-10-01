from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from drivers.models import Driver

from .. import services
from ..models import DriverAttendance, DriverLocation
from ..permissions import urban_access_required, urban_permissions_map
from ..utils import jalali_str, jalali_today, parse_jalali_date


@urban_access_required('can_urban_view_queue')
def urban_queue(request):
    """مدیریت نوبت رانندگان شهری و حضور/غیاب روزانه"""
    from fleet.models import Vehicle
    
    selected = parse_jalali_date(request.GET.get('date'), jalali_today())

    attendances = {
        a.driver_id: a
        for a in DriverAttendance.objects.filter(date=selected).select_related('driver')
    }
    
    # دریافت ناوگان رانندگان
    vehicles = {
        v.driver_id: v
        for v in Vehicle.objects.select_related('driver')
    }
    
    rows = [
        {'driver': driver, 'attendance': attendances.get(driver.pk), 'vehicle': vehicles.get(driver.pk)}
        for driver in Driver.objects.all().order_by('name')
    ]

    context = {
        'urban_perms': urban_permissions_map(request.user),
        'rows': rows,
        'selected_date': jalali_str(selected),
        'status_choices': DriverAttendance.Status.choices,
        'idle_locations': (DriverLocation.objects
                           .filter(status=DriverLocation.Status.IDLE)
                           .select_related('driver')),
        'busy_locations': (DriverLocation.objects
                           .filter(status=DriverLocation.Status.BUSY)
                           .select_related('driver', 'current_request')),
    }
    return render(request, 'city_drivers/queue/urban_queue.html', context)


@require_POST
@urban_access_required('can_urban_manage_queue')
def urban_queue_set_attendance(request):
    """ثبت وضعیت حضور یک راننده برای تاریخ مشخص"""
    driver = Driver.objects.filter(pk=request.POST.get('driver_id')).first()
    if driver is None:
        messages.error(request, 'راننده یافت نشد.')
        return redirect('city_drivers:urban_queue')

    status = request.POST.get('status')
    if status not in DriverAttendance.Status.values:
        messages.error(request, 'وضعیت حضور نامعتبر است.')
        return redirect('city_drivers:urban_queue')

    date = parse_jalali_date(request.POST.get('date'), jalali_today())
    services.set_attendance(driver, date, status, user=request.user,
                            note=request.POST.get('note') or '')
    messages.success(request, f'وضعیت حضور «{driver.name}» برای {date} ثبت شد.')
    return redirect('city_drivers:urban_queue')
