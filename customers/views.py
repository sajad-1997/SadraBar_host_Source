from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.cache import never_cache

from .forms import CustomerForm
from .models import Customer


@login_required
@never_cache
def customer_list(request):
    """لیست تمام مشتریان"""
    customers = Customer.objects.all().order_by("-id")

    # فیلترها
    name = request.GET.get("name")
    national_id = request.GET.get("national_id")
    phone = request.GET.get("phone")

    if name:
        customers = customers.filter(name__icontains=name)
    if national_id:
        customers = customers.filter(national_id__icontains=national_id)
    if phone:
        customers = customers.filter(phone__icontains=phone)

    context = {
        "customers": customers,
        "filters": request.GET
    }
    return render(request, "customers/customer_list.html", context)


@login_required
@never_cache
def add_customer(request):
    """افزودن مشتری جدید"""
    form = CustomerForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, 'مشتری جدید با موفقیت ثبت شد')
            return redirect('customers:customer_list')

    return render(request, 'customers/add_customer.html', {
        'form': form
    })


@login_required
@never_cache
def edit_customer(request, customer_id):
    """ویرایش اطلاعات مشتری"""
    customer = get_object_or_404(Customer, pk=customer_id)
    form = CustomerForm(request.POST or None, instance=customer)

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
            messages.success(request, "اطلاعات مشتری با موفقیت ذخیره شد.")
            return redirect('customers:customer_list')
        else:
            # نمایش پیام خطا برای هر فیلد
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields[field].label}: {error}")

    return render(request, 'customers/edit_customer.html', {'form': form, 'customer': customer})


@login_required
@never_cache
def search_customer(request):
    """جستجوی مشتری برای استفاده در فرم‌های دیگر"""
    q = request.GET.get('q', '')
    customers = Customer.objects.filter(name__icontains=q)[:15]
    return JsonResponse({
        'results': list(customers.values('id', 'name', 'national_id', 'phone'))
    })
