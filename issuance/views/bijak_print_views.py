# 6️⃣ bijak_print_views.py

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from issuance.models import Bijak, BijakApprovalLog
from .utils import to_jalali


def is_manager(user):
    return user.is_staff or user.is_superuser


@login_required
def preview_page(request, pk):
    """
    پیش‌نمایش بارنامه برای کارمند
    - فقط نمایش اطلاعات
    - بدون امکان تأیید یا رد
    """

    bijak = get_object_or_404(Bijak, pk=pk)

    # دریافت سوابق بررسی بارنامه (تایم‌لاین)
    approval_logs = BijakApprovalLog.objects.filter(
        bijak=bijak
    ).order_by('-created_at')

    context = {
        "bijak": bijak,
        "approval_logs": approval_logs,
    }

    return render(
        request,
        'issuance/secondary/preview.html',
        context
    )


def print_page(request, pk):
    bijak = get_object_or_404(Bijak, pk=pk)
    return render(request, 'issuance/bijak/final_bijak.html', {
        'shipment': bijak,
        'jalali_date': to_jalali(bijak.issuance_datetime)
    })
