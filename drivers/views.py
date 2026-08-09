from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Driver

@login_required
def driver_list(request):
    """لیست تمام رانندگان"""
    drivers = Driver.objects.all().order_by("-id")
    return render(request, "drivers/driver_list.html", {"drivers": drivers})

@login_required
def add_driver(request):
    """افزودن راننده جدید"""
    return render(request, "drivers/add_driver.html")

@login_required
def edit_driver(request, driver_id):
    """ویرایش راننده"""
    return render(request, "drivers/edit_driver.html", {"driver_id": driver_id})

@login_required
def search_driver(request):
    """جستجوی راننده"""
    return render(request, "drivers/search_driver.html")
