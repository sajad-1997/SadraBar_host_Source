from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import redirect, get_object_or_404, render
from django.utils import timezone
from django.views.decorators.cache import never_cache

from .forms import VehicleForm
from .models import Vehicle


@login_required
@never_cache
def vehicle_list(request):
    """لیست تمام ناوگان‌ها"""
    vehicles = Vehicle.objects.select_related('driver').all().order_by("-id")

    # فیلترها
    driver_name = request.GET.get("driver_name")
    vehicle_type = request.GET.get("vehicle_type")
    plate = request.GET.get("plate")
    smart_card = request.GET.get("smart_card")

    if driver_name:
        vehicles = vehicles.filter(driver__name__icontains=driver_name)
    if vehicle_type:
        vehicles = vehicles.filter(type=vehicle_type)
    if plate:
        vehicles = vehicles.filter(
            Q(license_plate_two_digit__icontains=plate) |
            Q(license_plate_alphabet__icontains=plate) |
            Q(license_plate_three_digit__icontains=plate) |
            Q(license_plate_series__icontains=plate)
        )
    if smart_card:
        vehicles = vehicles.filter(vehicle_smart_card__icontains=smart_card)

    context = {
        "vehicles": vehicles,
        "filters": request.GET
    }
    return render(request, "fleet/vehicle_list.html", context)


@login_required
@never_cache
def add_vehicle(request):
    """افزودن ناوگان جدید"""
    form = VehicleForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            instance = form.save(commit=False)
            
            # بررسی تکراری بودن کارت هوشمند
            smart_card = form.cleaned_data.get('vehicle_smart_card')
            if smart_card and Vehicle.objects.filter(vehicle_smart_card=smart_card).exists():
                form.add_error(
                    'vehicle_smart_card',
                    'این کارت هوشمند ناوگان قبلاً در سیستم ثبت شده است'
                )
            else:
                instance.save()
                messages.success(request, 'ناوگان جدید با موفقیت ثبت شد')
                return redirect('fleet:vehicle_list')

    return render(request, 'fleet/add_vehicle.html', {
        'form': form
    })


@login_required
@never_cache
def edit_vehicle(request, vehicle_id):
    """ویرایش اطلاعات ناوگان"""
    vehicle = get_object_or_404(Vehicle, pk=vehicle_id)
    form = VehicleForm(request.POST or None, instance=vehicle)

    if request.method == 'POST':
        if form.is_valid():
            instance = form.save(commit=False)
            now = timezone.now()

            # مدیریت تاریخ ایجاد و بروزرسانی
            if not getattr(instance, 'created_at', None):
                instance.created_at = now
            instance.updated_at = now

            if not getattr(instance, 'created_by', None):
                instance.created_by = request.user
            instance.updated_by = request.user

            instance.save()
            messages.success(request, "اطلاعات ناوگان با موفقیت ذخیره شد.")
            return redirect('fleet:vehicle_list')
        else:
            # نمایش پیام خطا برای هر فیلد
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields[field].label}: {error}")

    return render(request, 'fleet/edit_vehicle.html', {'form': form, 'vehicle': vehicle})


@login_required
@never_cache
def search_vehicle(request):
    """جستجوی ناوگان برای استفاده در فرم‌های دیگر"""
    q = request.GET.get('q', '')
    vehicles = Vehicle.objects.filter(
        Q(license_plate_two_digit__icontains=q) |
        Q(license_plate_alphabet__icontains=q) |
        Q(license_plate_three_digit__icontains=q) |
        Q(license_plate_series__icontains=q) |
        Q(vehicle_smart_card__icontains=q)
    ).select_related('driver')[:15]
    
    results = []
    for v in vehicles:
        results.append({
            'id': v.id,
            'driver_id': v.driver_id,
            'driver_name': v.driver.name,
            'type': v.get_type_display(),
            'plate': v.license_plate,
            'two_digit': v.license_plate_two_digit,
            'alphabet': v.license_plate_alphabet,
            'three_digit': v.license_plate_three_digit,
            'series': v.license_plate_series,
            'smart_card': v.vehicle_smart_card,
        })
    
    return JsonResponse({'results': results})


@login_required
@never_cache
def get_vehicle_by_driver(request):
    """دریافت اطلاعات ناوگان بر اساس راننده"""
    driver_id = request.GET.get("driver_id")

    if not driver_id:
        return JsonResponse({
            "success": False,
            "error": "شناسه راننده ارسال نشده است"
        })

    vehicle = (
        Vehicle.objects
        .filter(driver_id=driver_id)
        .order_by('-id')
        .first()
    )

    if not vehicle:
        return JsonResponse({
            "success": False,
            "error": "برای این راننده خودروی فعالی ثبت نشده است"
        })

    data = {
        "two_digit": vehicle.license_plate_two_digit,
        "alphabet": vehicle.license_plate_alphabet,
        "three_digit": vehicle.license_plate_three_digit,
        "series": vehicle.license_plate_series,
        "type": vehicle.type,
        "type_display": vehicle.get_type_display(),
    }

    return JsonResponse({"success": True, "vehicle": data})
