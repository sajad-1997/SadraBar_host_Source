from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.cache import never_cache

from drivers.models import Driver

from ..models import DriverLocation
from ..permissions import urban_access_required, urban_permissions_map


@urban_access_required('can_urban_view_locations')
@never_cache
def urban_locations_map(request):
    """نمایش موقعیت رانندگان در حال انجام سرویس و بدون سرویس"""
    return render(request, 'city_drivers/locations/urban_locations.html', {
        'urban_perms': urban_permissions_map(request.user),
    })


@urban_access_required('can_urban_view_locations')
@never_cache
def api_locations(request):
    """API موقعیت رانندگان (در حال انجام سرویس / بدون سرویس)"""

    def serialize(loc):
        return {
            'driver_id': loc.driver_id,
            'driver_name': loc.driver.name,
            'phone': loc.driver.phone or '',
            'lat': float(loc.lat) if loc.lat is not None else None,
            'lng': float(loc.lng) if loc.lng is not None else None,
            'status': loc.status,
            'status_display': loc.get_status_display(),
            'maps_url': loc.maps_url,
            'updated_at': loc.updated_at.strftime('%Y/%m/%d %H:%M:%S') if loc.updated_at else '',
            'current_request': loc.current_request.tracking_code if loc.current_request else '',
        }

    busy = [serialize(loc) for loc in DriverLocation.objects
            .filter(status=DriverLocation.Status.BUSY)
            .select_related('driver', 'current_request')]
    idle = [serialize(loc) for loc in DriverLocation.objects
            .filter(status=DriverLocation.Status.IDLE)
            .select_related('driver')]
    return JsonResponse({'busy': busy, 'idle': idle})


@urban_access_required()
@never_cache
def api_update_location(request):
    """ثبت/بروزرسانی موقعیت راننده (برای اتصال اپ راننده یا ثبت دستی)"""
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'متد POST الزامی است.'}, status=405)

    try:
        driver_id = int(request.POST.get('driver_id'))
        lat = float(request.POST.get('lat'))
        lng = float(request.POST.get('lng'))
    except (TypeError, ValueError):
        return JsonResponse({'ok': False, 'error': 'پارامترهای ارسالی نامعتبر است.'}, status=400)

    driver = Driver.objects.filter(pk=driver_id).first()
    if driver is None:
        return JsonResponse({'ok': False, 'error': 'راننده یافت نشد.'}, status=404)

    status = request.POST.get('status')
    loc = DriverLocation.refresh_location(
        driver, lat=lat, lng=lng,
        status=status if status in DriverLocation.Status.values else None)
    return JsonResponse({'ok': True, 'status': loc.status})
