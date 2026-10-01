from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from customers.models import Customer
from drivers.models import Driver

from .. import services
from ..forms import UrbanServiceRequestForm
from ..models import ServiceRequest, UrbanService
from ..permissions import urban_access_required, urban_permissions_map

# نگاشت اکشن‌های تغییر وضعیت
STATUS_ACTIONS = {
    'approve': ServiceRequest.Status.APPROVED,
    'done': ServiceRequest.Status.DONE,
    'cancel': ServiceRequest.Status.CANCELED,
    'reject': ServiceRequest.Status.REJECTED,
}


@urban_access_required('can_urban_view_requests')
def urban_request_list(request):
    """جدول درخواست‌های سرویس مشتریان شهری"""
    qs = (ServiceRequest.objects
          .select_related('customer', 'assigned_driver', 'service', 'rate_card'))

    tracking = request.GET.get('tracking_code', '').strip()
    customer = request.GET.get('customer', '').strip()
    status = request.GET.get('status', '').strip()
    driver_id = request.GET.get('driver', '').strip()
    if tracking:
        qs = qs.filter(tracking_code__icontains=tracking)
    if customer:
        qs = qs.filter(customer__name__icontains=customer)
    if status:
        qs = qs.filter(status=status)
    if driver_id:
        qs = qs.filter(assigned_driver_id=driver_id)

    context = {
        'urban_perms': urban_permissions_map(request.user),
        'requests': qs[:300],
        'filters': request.GET,
        'status_choices': ServiceRequest.Status.choices,
        'drivers': Driver.objects.all().order_by('name'),
    }
    return render(request, 'city_drivers/requests/urban_request_list.html', context)


def _resolve_customer(request):
    """یافتن مشتری انتخاب‌شده یا ساخت مشتری از فیلدهای ورود سریع"""
    customer_id = request.POST.get('customer')
    if customer_id:
        return Customer.objects.filter(pk=customer_id).first()

    name = request.POST.get('quick_name', '').strip()
    phone = request.POST.get('quick_phone', '').strip()
    address = request.POST.get('quick_address', '').strip()
    if not name:
        return None
    customer = Customer.objects.filter(name=name).first()
    if customer is None:
        customer = Customer.objects.create(
            name=name,
            phone=phone or None,
            address=address or '-',
            created_by=request.user,
            created_by_role=getattr(request.user, 'role', None))
    return customer


def _show_form_errors(request, form):
    for field, errors in form.errors.items():
        field_obj = form.fields.get(field)
        label = field_obj.label if field_obj else field
        for error in errors:
            messages.error(request, f'{label}: {error}')


@urban_access_required('can_urban_add_requests')
def urban_request_create(request):
    """فرم ثبت درخواست سرویس مشتری شهری"""
    form = UrbanServiceRequestForm(request.POST or None)

    if request.method == 'POST':
        customer = _resolve_customer(request)
        if customer is None:
            messages.error(request, 'انتخاب مشتری یا وارد کردن اطلاعات مشتری جدید الزامی است.')
        elif form.is_valid():
            sr = form.save(commit=False)
            sr.customer = customer
            sr.created_by = request.user
            sr.created_by_role = getattr(request.user, 'role', None)
            sr.tracking_code = services.generate_tracking_code()
            sr.save()
            services.recompute_fare(sr)
            messages.success(request, f'درخواست سرویس با کد رهگیری {sr.tracking_code} ثبت شد.')
            return redirect('city_drivers:urban_request_list')
        else:
            _show_form_errors(request, form)

    return render(request, 'city_drivers/requests/urban_request_form.html', {
        'urban_perms': urban_permissions_map(request.user),
        'form': form,
        'is_edit': False,
    })


@urban_access_required('can_urban_edit_requests')
def urban_request_edit(request, pk):
    """ویرایش درخواست سرویس"""
    sr = get_object_or_404(ServiceRequest, pk=pk)
    form = UrbanServiceRequestForm(request.POST or None, instance=sr)

    if request.method == 'POST' and form.is_valid():
        sr = form.save(commit=False)
        sr.updated_by = request.user
        sr.updated_by_role = getattr(request.user, 'role', None)
        sr.save()
        services.recompute_fare(sr)
        messages.success(request, f'درخواست سرویس {sr.tracking_code} بروزرسانی شد.')
        return redirect('city_drivers:urban_request_list')
    elif request.method == 'POST':
        _show_form_errors(request, form)

    return render(request, 'city_drivers/requests/urban_request_form.html', {
        'urban_perms': urban_permissions_map(request.user),
        'form': form,
        'is_edit': True,
        'service_request': sr,
    })


@require_POST
@urban_access_required('can_urban_assign_requests')
def urban_request_assign(request, pk):
    """تخصیص راننده به درخواست سرویس"""
    sr = get_object_or_404(ServiceRequest, pk=pk)
    driver = Driver.objects.filter(pk=request.POST.get('driver_id')).first()
    if driver is None:
        messages.error(request, 'انتخاب راننده الزامی است.')
        return redirect('city_drivers:urban_request_list')

    service = UrbanService.objects.filter(pk=request.POST.get('service_id') or None).first()
    services.assign_request(sr, driver, service=service, user=request.user)
    messages.success(request, f'سرویس {sr.tracking_code} به {driver.name} تخصیص یافت؛ پس از قبول راننده، وضعیت به «تخصیص یافته» تغییر می‌کند.')
    return redirect('city_drivers:urban_request_list')


@require_POST
@urban_access_required('can_urban_edit_requests')
def urban_request_status(request, pk):
    """تغییر وضعیت درخواست سرویس"""
    sr = get_object_or_404(ServiceRequest, pk=pk)
    action = request.POST.get('action')
    new_status = STATUS_ACTIONS.get(action)
    if new_status is None:
        messages.error(request, 'عملیات نامعتبر است.')
    else:
        services.change_status(sr, new_status, user=request.user,
                               note=request.POST.get('note') or '')
        messages.success(request, f'وضعیت سرویس {sr.tracking_code} بروزرسانی شد.')
    return redirect('city_drivers:urban_request_list')
