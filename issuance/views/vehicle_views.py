# 3️⃣ vehicle_views.py

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.cache import never_cache

from ..forms import VehicleForm
from ..models import Vehicle


@login_required
@never_cache
def add_vehicle(request):
    form = VehicleForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('issuance:crud:create_new')
    return render(request, 'issuance/add/add_vehicle.html', {'form': form})


@login_required
def search_vehicle(request):
    q = request.GET.get('q', '')
    vehicles = Vehicle.objects.filter(plate__icontains=q)[:5]
    return JsonResponse({
        'results': list(vehicles.values())
    })


@login_required
def get_vehicle_by_driver(request):
    driver_id = request.GET.get("driver_id")

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
    }

    return JsonResponse({"success": True, "vehicle": data})


@login_required(login_url='/accounts/login/')
@never_cache  # جلوگیری از نمایش از کش
def edit_vehicle(request):
    return render(request, 'issuance/edit/edit_vehicle.html')
