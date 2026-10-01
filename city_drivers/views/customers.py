from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from customers.models import Customer

from ..forms import UrbanCustomerForm
from ..models import UrbanCustomerProfile
from ..permissions import urban_access_required, urban_permissions_map


@urban_access_required('can_urban_view_customers')
def urban_customer_list(request):
    """لیست مشتریان شهری (اطلاعات در دیتابیس ماژول customers)"""
    qs = Customer.objects.all().order_by('-id')

    name = request.GET.get('name', '').strip()
    national_id = request.GET.get('national_id', '').strip()
    phone = request.GET.get('phone', '').strip()
    if name:
        qs = qs.filter(name__icontains=name)
    if national_id:
        qs = qs.filter(national_id__icontains=national_id)
    if phone:
        qs = qs.filter(phone__icontains=phone)

    customers = qs.prefetch_related('addresses')

    context = {
        'urban_perms': urban_permissions_map(request.user),
        'customers': customers,
        'filters': request.GET,
    }
    return render(request, 'city_drivers/customers/urban_customer_list.html', context)


@urban_access_required('can_urban_add_customers')
def urban_customer_create(request):
    """فرم ثبت اطلاعات مشتری شهری (ذخیره در ماژول customers)"""
    form = UrbanCustomerForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        customer = form.save(commit=False)
        national_id = (customer.national_id or '').strip()
        existing = None
        if national_id:
            existing = Customer.objects.filter(national_id=national_id).first()

        if existing:
            # بروزرسانی اطلاعات مشتری موجود
            for field in ('name', 'phone', 'phone2', 'postal', 'address', 'caption'):
                new_value = getattr(customer, field, None)
                if new_value:
                    setattr(existing, field, new_value)
            existing.updated_by = request.user
            existing.updated_by_role = getattr(request.user, 'role', None)
            existing.save()
            customer = existing
            messages.success(request, f'اطلاعات مشتری «{existing.name}» بروزرسانی شد.')
        else:
            customer.created_by = request.user
            customer.created_by_role = getattr(request.user, 'role', None)
            customer.save()
            messages.success(request, 'مشتری شهری جدید با موفقیت ثبت شد.')

        UrbanCustomerProfile.objects.update_or_create(
            customer=customer,
            defaults={
                'note': form.cleaned_data.get('profile_note') or '',
                'updated_by': request.user,
            })
        return redirect('city_drivers:urban_customer_list')

    return render(request, 'city_drivers/customers/urban_customer_form.html', {
        'urban_perms': urban_permissions_map(request.user),
        'form': form,
        'is_edit': False,
    })


@urban_access_required('can_urban_add_customers')
def urban_customer_edit(request, pk):
    """ویرایش اطلاعات مشتری شهری"""
    customer = get_object_or_404(Customer, pk=pk)
    profile = UrbanCustomerProfile.objects.filter(customer=customer).first()
    initial = {'profile_note': profile.note if profile else ''}

    form = UrbanCustomerForm(request.POST or None, instance=customer, initial=initial)

    if request.method == 'POST' and form.is_valid():
        customer = form.save(commit=False)
        customer.updated_by = request.user
        customer.updated_by_role = getattr(request.user, 'role', None)
        customer.save()
        UrbanCustomerProfile.objects.update_or_create(
            customer=customer,
            defaults={
                'note': form.cleaned_data.get('profile_note') or '',
                'updated_by': request.user,
            })
        messages.success(request, 'اطلاعات مشتری شهری با موفقیت بروزرسانی شد.')
        return redirect('city_drivers:urban_customer_list')

    return render(request, 'city_drivers/customers/urban_customer_form.html', {
        'urban_perms': urban_permissions_map(request.user),
        'form': form,
        'is_edit': True,
        'customer': customer,
    })


@urban_access_required('can_urban_view_requests')
def urban_customer_search(request):
    """جستجوی سریع مشتری برای فرم درخواست سرویس (JSON)"""
    q = request.GET.get('q', '').strip()
    qs = Customer.objects.all()
    if q:
        from django.db.models import Q
        qs = qs.filter(Q(name__icontains=q) | Q(phone__icontains=q))
    results = [{
        'id': c.pk,
        'name': c.name,
        'phone': c.phone or '',
        'address': c.address or '',
    } for c in qs[:15]]
    return JsonResponse({'results': results})
