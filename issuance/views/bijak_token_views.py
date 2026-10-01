# issuance/views/bijak_token_views.py

from django.shortcuts import get_object_or_404, render, redirect
from django.http import Http404
from django.urls import reverse
from issuance.models import Bijak
from .utils import to_jalali


def bijak_access_view(request, token):
    """
    ویو دسترسی به بارنامه از طریق توکن عمومی.
    - بدون نیاز به لاگین
    - فقط نمایش اطلاعات پایه بارنامه
    """
    try:
        bijak = get_object_or_404(Bijak, access_token=token)
    except Http404:
        raise Http404("بارنامه مورد نظر یافت نشد.")
    
    # ریدایرکت به صفحه چاپ بارنامه با توکن
    return redirect('issuance:token:bijak_print_token', token=token)


def bijak_print_by_token(request, token):
    """
    ویو چاپ بارنامه از طریق توکن عمومی.
    - بدون نیاز به لاگین
    - مناسب برای اشتراک‌گذاری خارجی
    """
    try:
        bijak = get_object_or_404(Bijak, access_token=token)
    except Http404:
        raise Http404("بارنامه مورد نظر یافت نشد.")
    
    context = {
        'shipment': bijak,
        'jalali_date': to_jalali(bijak.issuance_datetime),
        'is_public_access': True,  # فلگ برای تشخیص دسترسی عمومی در تمپلیت
    }
    
    return render(request, 'issuance/bijak/final_bijak.html', context)
