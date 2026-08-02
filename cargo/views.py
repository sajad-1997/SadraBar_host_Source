from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.cache import never_cache

from .forms import CargoForm
from .models import Cargo


@login_required
@never_cache
def cargo_list(request):
    """لیست تمام محموله‌ها"""
    cargos = Cargo.objects.all().order_by("-id")

    # فیلترها
    name = request.GET.get("name")
    origin = request.GET.get("origin")
    destination = request.GET.get("destination")

    if name:
        cargos = cargos.filter(name__icontains=name)
    if origin:
        cargos = cargos.filter(origin__icontains=origin)
    if destination:
        cargos = cargos.filter(destination__icontains=destination)

    context = {
        "cargos": cargos,
        "filters": request.GET
    }
    return render(request, "cargo/cargo_list.html", context)


@login_required
@never_cache
def add_cargo(request):
    """افزودن محموله جدید"""
    form = CargoForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, 'محموله جدید با موفقیت ثبت شد')
            return redirect('cargo:cargo_list')

    return render(request, 'cargo/add_cargo.html', {
        'form': form
    })


@login_required
@never_cache
def edit_cargo(request, cargo_id):
    """ویرایش اطلاعات محموله"""
    cargo = get_object_or_404(Cargo, pk=cargo_id)
    form = CargoForm(request.POST or None, instance=cargo)

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
            messages.success(request, "اطلاعات محموله با موفقیت ذخیره شد.")
            return redirect('cargo:cargo_list')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields[field].label}: {error}")

    return render(request, 'cargo/edit_cargo.html', {'form': form, 'cargo': cargo})


@login_required
@never_cache
def search_cargo(request):
    """جستجوی محموله برای استفاده در فرم‌های دیگر"""
    q = request.GET.get('q', '')
    cargos = Cargo.objects.filter(name__icontains=q)[:15]
    return JsonResponse({
        'results': list(cargos.values('id', 'name', 'origin', 'destination'))
    })
