# 4️⃣ edit_views.py


from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.shortcuts import render
from django.views.decorators.cache import never_cache

from ..forms import *


@login_required(login_url='/accounts/login/')
@never_cache  # جلوگیری از نمایش از کش
def edit_cargo(request):
    return render(request, 'issuance/edit/edit_cargo.html')


@login_required(login_url='/accounts/login/')
@never_cache  # جلوگیری از نمایش از کش
# -----------------------
# ویرایش بارنامه صادر شده
# -----------------------
def edit_bijak(request, pk):
    bijak = get_object_or_404(Bijak, pk=pk)

    if request.method == 'POST':
        bijak_form = ShipmentForm(request.POST, instance=bijak)
        sender_form = CustomerForm(request.POST, prefix='sender', instance=bijak.sender)
        receiver_form = CustomerForm(request.POST, prefix='receiver', instance=bijak.receiver)
        driver_form = DriverForm(request.POST, prefix='driver', instance=bijak.driver)
        vehicle_form = VehicleForm(request.POST, instance=bijak.vehicle)
        cargo_form = CargoForm(request.POST, instance=bijak.cargo)

        if all([
            bijak_form.is_valid(),
            sender_form.is_valid(),
            receiver_form.is_valid(),
            driver_form.is_valid(),
            vehicle_form.is_valid(),
            cargo_form.is_valid()
        ]):
            bijak_form.save()
            sender_form.save()
            receiver_form.save()
            driver_form.save()
            vehicle_form.save()
            cargo_form.save()

            messages.success(request, "بیجک با موفقیت ویرایش شد ✅")
            return redirect('preview', pk=bijak.pk)  # صفحه نمایش نهایی
    else:
        bijak_form = ShipmentForm(instance=bijak)
        sender_form = CustomerForm(prefix='sender', instance=bijak.sender)
        receiver_form = CustomerForm(prefix='receiver', instance=bijak.receiver)
        driver_form = DriverForm(prefix='driver', instance=bijak.driver)
        vehicle_form = VehicleForm(instance=bijak.vehicle)
        cargo_form = CargoForm(instance=bijak.cargo)

    return render(request, 'issuance/edit/edit_bijak.html', {
        'bijak_form': bijak_form,
        'sender_form': sender_form,
        'receiver_form': receiver_form,
        'driver_form': driver_form,
        'vehicle_form': vehicle_form,
        'cargo_form': cargo_form,
        'bijak': bijak,
    })
