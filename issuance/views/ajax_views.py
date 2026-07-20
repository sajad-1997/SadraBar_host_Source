# 6️⃣ ajax_views.py

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from ..forms import CustomerForm, DriverForm


@login_required
@require_POST
def save_customer(request):
    form = CustomerForm(request.POST)
    if form.is_valid():
        customer = form.save()
        return JsonResponse({
            'success': True,
            'id': customer.id,
            'name': customer.name
        })
    return JsonResponse({'success': False, 'errors': form.errors})


@login_required
@require_POST
def save_driver(request):
    form = DriverForm(request.POST)
    if form.is_valid():
        driver = form.save()
        return JsonResponse({
            'success': True,
            'id': driver.id,
            'name': driver.name
        })
    return JsonResponse({'success': False, 'errors': form.errors})
