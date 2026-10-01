from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from accounts.utils import get_user_role
from .forms import DriverForm
from .models import Driver

@login_required
def driver_list(request):
    """لیست تمام رانندگان"""
    drivers = Driver.objects.prefetch_related("vehicle_set").all().order_by("-id")

    name = request.GET.get("name")
    national_id = request.GET.get("national_id")
    phone = request.GET.get("phone")
    certificate = request.GET.get("certificate")
    smart_card = request.GET.get("smart_card")

    if name:
        drivers = drivers.filter(name__icontains=name)
    if national_id:
        drivers = drivers.filter(national_id__icontains=national_id)
    if phone:
        drivers = drivers.filter(Q(phone__icontains=phone) | Q(phone2__icontains=phone) | Q(phone3__icontains=phone))
    if certificate:
        drivers = drivers.filter(certificate__icontains=certificate)
    if smart_card:
        drivers = drivers.filter(driver_smart_card__icontains=smart_card)

    return render(request, "drivers/driver_list.html", {"drivers": drivers, "filters": request.GET})

@login_required
def add_driver(request):
    """افزودن راننده جدید"""
    form = DriverForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        driver = form.save(commit=False)
        driver.created_by = request.user
        driver.created_by_role = get_user_role(request.user)
        driver.updated_by = request.user
        driver.updated_by_role = get_user_role(request.user)
        driver.save()
        messages.success(request, "راننده جدید با موفقیت ثبت شد")
        return redirect("drivers:driver_list")

    return render(request, "drivers/add_driver.html", {"form": form})

@login_required
def edit_driver(request, driver_id):
    """ویرایش راننده"""
    driver = get_object_or_404(Driver, pk=driver_id)
    form = DriverForm(request.POST or None, instance=driver)

    if request.method == "POST" and form.is_valid():
        driver = form.save(commit=False)
        if not getattr(driver, "created_by", None):
            driver.created_by = request.user
            driver.created_by_role = get_user_role(request.user)
        driver.updated_by = request.user
        driver.updated_by_role = get_user_role(request.user)
        driver.save()
        messages.success(request, "اطلاعات راننده با موفقیت ذخیره شد")
        # مسیر issuance:add_vehicle_with_driver در urls کامنت شده است؛ به مسیر فعال fleet:add_vehicle ریدایرکت می‌کنیم
        return redirect("fleet:add_vehicle")

    return render(request, "drivers/edit_driver.html", {"form": form, "driver": driver})

@login_required
def search_driver(request):
    """جستجوی راننده"""
    q = request.GET.get("q", "").strip()
    drivers = Driver.objects.filter(
        Q(name__icontains=q) |
        Q(national_id__icontains=q) |
        Q(phone__icontains=q)
    )[:10]
    return JsonResponse({
        "results": list(drivers.values("id", "name", "national_id", "phone"))
    })
