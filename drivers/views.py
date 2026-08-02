from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import redirect, get_object_or_404, render
from django.utils import timezone
from django.views.decorators.cache import never_cache

from .forms import DriverForm
from .models import Driver


@login_required
@never_cache
def driver_list(request):
    """لیست تمام رانندگان"""
    drivers = Driver.objects.all().order_by("-id")

    # فیلترها
    name = request.GET.get("name")
    national_id = request.GET.get("national_id")
    phone = request.GET.get("phone")
    certificate = request.GET.get("certificate")

    if name:
        drivers = drivers.filter(name__icontains=name)
    if national_id:
        drivers = drivers.filter(national_id__icontains=national_id)
    if phone:
        drivers = drivers.filter(Q(phone__icontains=phone) | Q(phone2__icontains=phone))
    if certificate:
        drivers = drivers.filter(certificate__icontains=certificate)

    context = {
        "drivers": drivers,
        "filters": request.GET
    }
    return render(request, "drivers/driver_list.html", context)


@login_required
@never_cache
def add_driver(request):
    """افزودن راننده جدید"""
    form = DriverForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            name = form.cleaned_data.get('name')
            national_id = form.cleaned_data.get('national_id')

            # بررسی تکراری بودن نام
            if Driver.objects.filter(name=name).exists():
                form.add_error(
                    'name',
                    'راننده‌ای با این نام و نام خانوادگی قبلاً ثبت شده است'
                )

            # بررسی تکراری بودن کد ملی
            if national_id and Driver.objects.filter(national_id=national_id).exists():
                form.add_error(
                    'national_id',
                    'کد ملی وارد شده قبلاً در سیستم ثبت شده است'
                )

            # اگر بعد از بررسی هنوز خطایی وجود ندارد → ذخیره
            if not form.errors:
                form.save()
                messages.success(request, 'راننده جدید با موفقیت ثبت شد')
                return redirect('drivers:driver_list')

    return render(request, 'drivers/add_driver.html', {
        'form': form
    })


@login_required
@never_cache
def edit_driver(request, driver_id):
    """ویرایش اطلاعات راننده"""
    driver = get_object_or_404(Driver, pk=driver_id)
    form = DriverForm(request.POST or None, instance=driver)

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
            messages.success(request, "اطلاعات راننده با موفقیت ذخیره شد.")
            return redirect('drivers:driver_list')
        else:
            # نمایش پیام خطا برای هر فیلد
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields[field].label}: {error}")

    return render(request, 'drivers/edit_driver.html', {'form': form, 'driver': driver})


@login_required
@never_cache
def search_driver(request):
    """جستجوی راننده برای استفاده در فرم‌های دیگر"""
    q = request.GET.get('q', '')
    drivers = Driver.objects.filter(name__icontains=q)[:15]
    return JsonResponse({
        'results': list(drivers.values('id', 'name', 'national_id', 'phone'))
    })
