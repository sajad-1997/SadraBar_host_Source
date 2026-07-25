# 1️⃣ bijak_manage_views.py

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.cache import never_cache

from .utils import show_form_errors
from ..forms import ShipmentForm, CargoForm
from ..models import Bijak


@login_required
@never_cache
def edit_bijak(request, pk):
    with transaction.atomic():
        bijak = get_object_or_404(
            Bijak.objects.select_for_update(),
            pk=pk
        )

        shipment_form = ShipmentForm(
            request.POST or None,
            instance=bijak,
            prefix='shipment'
        )
        cargo_form = CargoForm(
            request.POST or None,
            instance=bijak.cargo,
            prefix='cargo'
        )

        if request.method == 'POST':
            if shipment_form.is_valid() and cargo_form.is_valid():
                cargo_form.save()
                shipment_form.save()
                messages.success(request, "بارنامه با موفقیت ویرایش شد")
                return redirect('issuance:crud:preview', pk=bijak.id)

            show_form_errors(request, shipment_form, "اطلاعات بارنامه")
            show_form_errors(request, cargo_form, "اطلاعات محموله")

        return render(request, 'issuance/bijak/issuance_form.html', {
            'shipment_form': shipment_form,
            'cargo_form': cargo_form,
            'edit_mode': True,
            'bijak': bijak,
        })


@login_required
def print_page(request):
    # بهینه‌سازی کوئری با select_related برای کاهش تعداد queryهای دیتابیس
    bijaks = Bijak.objects.select_related(
        'sender',
        'receiver',
        'driver',
        'vehicle',
        'cargo'
    ).all().order_by('-id')[:20]
    return render(request, 'issuance/secondary/last_bijaks.html', {
        'bijaks': bijaks
    })
