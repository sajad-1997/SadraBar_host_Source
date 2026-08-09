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

    # بررسی مجوزهای ویرایش
    can_edit_sender = bijak.can_edit_sender or bijak.approval_status != 'rejected'
    can_edit_receiver = bijak.can_edit_receiver or bijak.approval_status != 'rejected'
    can_edit_driver = bijak.can_edit_driver or bijak.approval_status != 'rejected'
    can_edit_cargo = bijak.can_edit_cargo or bijak.approval_status != 'rejected'
    can_edit_financial = bijak.can_edit_financial or bijak.approval_status != 'rejected'

    if request.method == 'POST':
        # ویرایش بخش فرستنده
        if can_edit_sender:
            sender_form = CustomerForm(request.POST, prefix='sender', instance=bijak.sender)
            if sender_form.is_valid():
                sender_form.save()
        
        # ویرایش بخش گیرنده
        if can_edit_receiver:
            receiver_form = CustomerForm(request.POST, prefix='receiver', instance=bijak.receiver)
            if receiver_form.is_valid():
                receiver_form.save()
        
        # ویرایش بخش راننده
        if can_edit_driver:
            driver_form = DriverForm(request.POST, prefix='driver', instance=bijak.driver)
            if driver_form.is_valid():
                driver_form.save()
        
        # ویرایش بخش محموله
        if can_edit_cargo:
            cargo_form = CargoForm(request.POST, instance=bijak.cargo)
            if cargo_form.is_valid():
                cargo_form.save()
        
        # ویرایش بخش مالی
        if can_edit_financial:
            bijak_form = ShipmentForm(request.POST, instance=bijak)
            if bijak_form.is_valid():
                bijak_form.save()

        messages.success(request, "بیجک با موفقیت ویرایش شد ✅")
        return redirect('issuance:crud:preview', pk=bijak.pk)
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
        'can_edit_sender': can_edit_sender,
        'can_edit_receiver': can_edit_receiver,
        'can_edit_driver': can_edit_driver,
        'can_edit_cargo': can_edit_cargo,
        'can_edit_financial': can_edit_financial,
    })
