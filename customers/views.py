from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.cache import never_cache

from accounts.utils import get_user_role

from .forms import CustomerForm
from .models import Customer, CustomerAddress


@login_required
@never_cache
def customer_list(request):
    """لیست تمام مشتریان با آدرس‌های اضافی"""
    customers = Customer.objects.prefetch_related('addresses').all().order_by("-id")

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


def normalize_name(name):
    """نرمال‌سازی نام برای مقایسه - حذف فاصله‌ها و یکسان‌سازی کاراکترها"""
    if not name:
        return ""
    # حذف فاصله‌ها، نیم‌فاصله‌ها و کاراکترهای خاص
    normalized = name.replace(' ', '').replace('\u200c', '').replace('\u200d', '')
    # حذف کاراکترهای غیر الفبایی
    normalized = ''.join(c for c in normalized if c.isalnum())
    return normalized.lower()


@login_required
@never_cache
def add_customer(request):
    """افزودن مشتری جدید یا افزودن آدرس به مشتری موجود"""
    form = CustomerForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            name = form.cleaned_data.get('name')
            national_id = form.cleaned_data.get('national_id')
            postal = form.cleaned_data.get('postal')
            phone = form.cleaned_data.get('phone')
            address = form.cleaned_data.get('address')

            # دریافت اطلاعات اضافی از فیلدهای extra
            extra_postal = request.POST.get('extra_postal', '').strip()
            extra_phone = request.POST.get('extra_phone', '').strip()
            extra_address = request.POST.get('extra_address', '').strip()

            # بررسی تکراری بودن کد ملی - اگر وجود دارد، خطا بده
            if national_id:
                existing_by_national = Customer.objects.filter(national_id=national_id).first()
                if existing_by_national:
                    messages.error(request, f'مشتری با کد ملی {national_id} قبلاً ثبت شده است. لطفاً کد ملی دیگری وارد کنید.')
                    return render(request, 'customers/add_customer.html', {'form': form})

            # بررسی وجود مشتری بر اساس نام (فقط برای اطلاع، نه جلوگیری)
            normalized_name = normalize_name(name)
            existing_customer = None
            if name:
                potential_customers = Customer.objects.filter(name__icontains=name)
                for customer in potential_customers:
                    if normalize_name(customer.name) == normalized_name:
                        existing_customer = customer
                        break

            if existing_customer:
                # مشتری با همین نام وجود دارد - اطلاعات اضافی را به عنوان آدرس جداگانه ذخیره کن
                # اطلاعات اصلی فرم را هم به عنوان آدرس جداگانه ذخیره کن
                CustomerAddress.objects.create(
                    customer=existing_customer,
                    postal=postal,
                    phone=phone,
                    address=address,
                    created_by=request.user
                )

                # اگر اطلاعات اضافی هم پر شده باشد، آن را هم به عنوان آدرس جداگانه ذخیره کن
                if extra_postal or extra_phone or extra_address:
                    CustomerAddress.objects.create(
                        customer=existing_customer,
                        postal=extra_postal,
                        phone=extra_phone,
                        address=extra_address,
                        created_by=request.user
                    )

                messages.success(request, f'آدرس جدید برای مشتری با نام {existing_customer.name} ذخیره شد')
            else:
                # مشتری جدید است - در جدول Customer ذخیره کن
                customer = form.save(commit=False)
                customer.created_by = request.user
                customer.created_by_role = get_user_role(request.user)
                customer.updated_by = request.user
                customer.updated_by_role = get_user_role(request.user)
                customer.save()

                # اگر اطلاعات اضافی وجود داشت، آن را به عنوان آدرس جداگانه ذخیره کن
                if extra_postal or extra_phone or extra_address:
                    CustomerAddress.objects.create(
                        customer=customer,
                        postal=extra_postal,
                        phone=extra_phone,
                        address=extra_address,
                        created_by=request.user
                    )

                messages.success(request, 'مشتری جدید با موفقیت ثبت شد')

            return redirect('customers:customer_list')
        else:
            # نمایش خطاهای فرم
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields[field].label}: {error}")

    return render(request, 'customers/add_customer.html', {
        'form': form
    })


@login_required
@never_cache
def edit_customer(request, customer_id):
    """ویرایش اطلاعات مشتری شامل اطلاعات اصلی و آدرس‌های اضافی"""
    customer = get_object_or_404(
        Customer.objects.prefetch_related('addresses'), pk=customer_id
    )
    form = CustomerForm(request.POST or None, instance=customer)
    addresses = list(customer.addresses.all())

    if request.method == 'POST':
        # حذف یک آدرس اضافی (از طریق فیلد مخفی delete_address_id که با جاوااسکریپت ست می‌شود)
        delete_address_id = request.POST.get('delete_address_id')
        if delete_address_id:
            address = get_object_or_404(CustomerAddress, pk=delete_address_id, customer=customer)
            address.delete()
            messages.success(request, "آدرس انتخاب‌شده با موفقیت حذف شد.")
            return redirect('customers:edit_customer', customer_id=customer.pk)

        if form.is_valid():
            instance = form.save(commit=False)
            now = timezone.now()

            # مدیریت تاریخ ایجاد و بروزرسانی
            if not getattr(instance, 'created_at', None):
                instance.created_at = now
            instance.updated_at = now

            if not getattr(instance, 'created_by', None):
                instance.created_by = request.user
                instance.created_by_role = get_user_role(request.user)
            instance.updated_by = request.user
            instance.updated_by_role = get_user_role(request.user)

            instance.save()

            # ---------- ویرایش آدرس‌های اضافی موجود ----------
            has_error = False
            for address in addresses:
                # فقط اگر فیلدهای مربوط به این آدرس در POST ارسال شده باشد
                addr_key = f'addr_address_{address.pk}'
                if addr_key not in request.POST:
                    continue

                addr_postal = request.POST.get(f'addr_postal_{address.pk}', '').strip()
                addr_phone = request.POST.get(f'addr_phone_{address.pk}', '').strip()
                addr_address = request.POST.get(addr_key, '').strip()

                if not addr_address:
                    messages.error(
                        request,
                        f"آدرس اضافی شماره {address.pk} نمی‌تواند خالی باشد. اگر می‌خواهید آن را حذف کنید از دکمه حذف استفاده کنید."
                    )
                    has_error = True
                    continue

                address.postal = addr_postal or None
                address.phone = addr_phone or None
                address.address = addr_address
                address.save()

            # ---------- افزودن آدرس اضافی جدید ----------
            extra_postal = request.POST.get('extra_postal', '').strip()
            extra_phone = request.POST.get('extra_phone', '').strip()
            extra_address = request.POST.get('extra_address', '').strip()

            if extra_postal or extra_phone or extra_address:
                if not extra_address:
                    messages.error(request, "برای افزودن آدرس جدید، پر کردن فیلد آدرس الزامی است.")
                    has_error = True
                else:
                    CustomerAddress.objects.create(
                        customer=customer,
                        postal=extra_postal or None,
                        phone=extra_phone or None,
                        address=extra_address,
                        created_by=request.user
                    )

            if has_error:
                # برخی تغییرات ذخیره شده اما خطا هم وجود دارد؛ صفحه ویرایش با پیام‌ها نمایش داده می‌شود
                messages.warning(request, "اطلاعات اصلی مشتری ذخیره شد، اما برخی از آدرس‌های اضافی به دلیل خطا ذخیره نشدند.")
                return redirect('customers:edit_customer', customer_id=customer.pk)

            messages.success(request, "اطلاعات مشتری (شامل آدرس‌های اضافی) با موفقیت ذخیره شد.")
            return redirect('customers:customer_list')
        else:
            # نمایش پیام خطا برای هر فیلد
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields[field].label}: {error}")

    return render(request, 'customers/edit_customer.html', {
        'form': form,
        'customer': customer,
        'addresses': addresses,
    })


@login_required
@never_cache
def search_customer(request):
    """جستجوی مشتری برای استفاده در فرم‌های دیگر (به همراه تمام آدرس‌های مشتری)"""
    q = request.GET.get('q', '')
    customers = (
        Customer.objects.filter(name__icontains=q)
        .prefetch_related('addresses')[:15]
    )

    results = []
    for customer in customers:
        addresses = []

        # آدرس اصلی مشتری
        if customer.address:
            addresses.append({
                'address': customer.address,
                'phone': customer.phone or '',
                'postal': customer.postal or '',
            })

        # آدرس‌های اضافی مشتری
        for addr in customer.addresses.all():
            addresses.append({
                'address': addr.address,
                'phone': addr.phone or '',
                'postal': addr.postal or '',
            })

        results.append({
            'id': customer.id,
            'name': customer.name,
            'national_id': customer.national_id,
            'phone': customer.phone,
            'address': customer.address,
            'addresses': addresses,
        })

    return JsonResponse({'results': results})
