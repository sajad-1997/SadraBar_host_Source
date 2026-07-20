# 4️⃣ customer_views.py

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.cache import never_cache

from issuance.models import Customer
from ..forms import CustomerForm


@login_required
@never_cache
def add_customer(request):
    form = CustomerForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect('issuance:crud:create_new')
    return render(request, 'issuance/add/add_customer.html', {"form": form})


@login_required
@never_cache
def search_customer(request):
    q = request.GET.get("q", "")
    customers = Customer.objects.filter(name__icontains=q)[:15]
    return JsonResponse({"results": list(customers.values())})


@login_required
@never_cache
def duplicate_customer(request):
    if request.method == "POST":
        name = request.POST.get("name")
        national_id = request.POST.get("national_id")
        postal = request.POST.get("postal")
        phone = request.POST.get("phone")
        address = request.POST.get("address")

        # بررسی تکراری بودن national_id
        if national_id:
            existing = Customer.objects.filter(national_id=national_id).first()
            if existing:
                # اجازه ثبت رکورد جدید فقط اگر آدرس متفاوت باشد
                if existing.address == address:
                    return JsonResponse({
                        "success": False,
                        "error": "این مشتری با همان آدرس قبلاً ثبت شده است"
                    })
                else:
                    # در این حالت duplicate با national_id همان، فقط آدرس جدید ثبت می‌شود
                    try:
                         # اضافه کردن خط تیره به انتهای کد ملی
                        new_national_id = f"{existing.national_id}-"
                        
                        new_customer = Customer.objects.create(
                            name=name,
                            national_id=new_national_id,  # national_id تکراری را جدید می‌کنیم
                            postal=postal,
                            phone=phone,
                            address=address
                        )
                        return JsonResponse({"success": True, "new_id": new_customer.id})
                    except Exception as e:
                        return JsonResponse({"success": False, "error": str(e)})

        # اگر national_id خالی است یا قبلاً موجود نبوده
        try:
            new_customer = Customer.objects.create(
                name=name,
                national_id=national_id,
                postal=postal,
                phone=phone,
                address=address
            )
            return JsonResponse({"success": True, "new_id": new_customer.id})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "درخواست نامعتبر"})


@login_required
@never_cache
def edit_customer(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
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
            return redirect('issuance:crud:create_new')
        else:
            # نمایش پیام خطا برای هر فیلد
            for field, errors in form.errors.items():
                for error in errors:
                    label = getattr(form.fields[field], 'label', field)
                    messages.error(request, f"{label}: {error}")

    return render(request, 'issuance/edit/edit_customer.html', {
        'form': form,
        'customer': customer,
    })
