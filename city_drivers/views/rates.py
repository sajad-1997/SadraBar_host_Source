from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from ..forms import FareCalculatorForm, RateCardForm
from ..models import RateCard
from ..permissions import urban_access_required, urban_permissions_map


@urban_access_required('can_urban_view_rates')
def urban_rate_list(request):
    """لیست نرخ‌نامه‌ها + محاسبه گر کرایه"""
    rate_cards = RateCard.objects.all().select_related('service')

    form = FareCalculatorForm(request.GET or None, prefix='calc')
    fare_result = None
    if 'calc-submit' in request.GET:
        if form.is_valid():
            rate = form.cleaned_data['rate_card']
            distance = form.cleaned_data['distance_km']
            fare = rate.calculate_fare(distance)
            commission = rate.commission_for(fare)
            fare_result = {
                'rate': rate,
                'distance': distance,
                'fare': fare,
                'commission': commission,
                'net': fare - commission,
            }
        else:
            messages.error(request, 'برای محاسبه کرایه، انتخاب نرخ‌نامه و وارد کردن مسافت الزامی است.')

    context = {
        'urban_perms': urban_permissions_map(request.user),
        'rate_cards': rate_cards,
        'calc_form': form,
        'fare_result': fare_result,
    }
    return render(request, 'city_drivers/rates/urban_rate_list.html', context)


@urban_access_required('can_urban_manage_rates')
def urban_rate_create(request):
    """ثبت نرخ‌نامه جدید"""
    form = RateCardForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        rate = form.save(commit=False)
        rate.created_by = request.user
        rate.save()
        messages.success(request, 'نرخ‌نامه جدید ثبت شد.')
        return redirect('city_drivers:urban_rate_list')
    elif request.method == 'POST':
        for field, errors in form.errors.items():
            field_obj = form.fields.get(field)
            label = field_obj.label if field_obj else field
            for error in errors:
                messages.error(request, f'{label}: {error}')

    return render(request, 'city_drivers/rates/urban_rate_form.html', {
        'urban_perms': urban_permissions_map(request.user),
        'form': form,
        'is_edit': False,
    })


@urban_access_required('can_urban_manage_rates')
def urban_rate_edit(request, pk):
    """ویرایش نرخ‌نامه"""
    rate = get_object_or_404(RateCard, pk=pk)
    form = RateCardForm(request.POST or None, instance=rate)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'نرخ‌نامه بروزرسانی شد.')
        return redirect('city_drivers:urban_rate_list')
    elif request.method == 'POST':
        for field, errors in form.errors.items():
            field_obj = form.fields.get(field)
            label = field_obj.label if field_obj else field
            for error in errors:
                messages.error(request, f'{label}: {error}')

    return render(request, 'city_drivers/rates/urban_rate_form.html', {
        'urban_perms': urban_permissions_map(request.user),
        'form': form,
        'is_edit': True,
        'rate_card': rate,
    })


@require_POST
@urban_access_required('can_urban_manage_rates')
def urban_rate_toggle(request, pk):
    """فعال/غیرفعال کردن نرخ‌نامه"""
    rate = get_object_or_404(RateCard, pk=pk)
    rate.is_active = not rate.is_active
    rate.save(update_fields=['is_active', 'updated_at'])
    messages.success(request, f'نرخ‌نامه «{rate.title}» {"فعال" if rate.is_active else "غیرفعال"} شد.')
    return redirect('city_drivers:urban_rate_list')


@urban_access_required('can_urban_view_rates')
def urban_fare_calculator(request):
    """صفحه جداگانه محاسبه کرایه"""
    form = FareCalculatorForm(request.GET or None, prefix='calc')
    fare_result = None
    if 'calc-submit' in request.GET and form.is_valid():
        rate = form.cleaned_data['rate_card']
        distance = form.cleaned_data['distance_km']
        fare = rate.calculate_fare(distance)
        commission = rate.commission_for(fare)
        fare_result = {
            'rate': rate,
            'distance': distance,
            'fare': fare,
            'commission': commission,
            'net': fare - commission,
        }

    context = {
        'urban_perms': urban_permissions_map(request.user),
        'calc_form': form,
        'fare_result': fare_result,
    }
    return render(request, 'city_drivers/rates/urban_fare_calculator.html', context)
