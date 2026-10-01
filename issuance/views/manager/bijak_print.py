from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, render

from accounts.decorators import can_print_without_approval
from issuance.models import Bijak
from issuance.views.bijak_print_views import _print_context


@login_required
def bijak_print(request, bijak_id):
    """صفحه چاپ بارنامه (نقطه ورود دکمه «چاپ بارنامه» در فرم صدور)."""
    bijak = get_object_or_404(Bijak, pk=bijak_id)

    # بررسی مجوز چاپ بدون تایید مدیریت
    # (مدیریت و مدیر کل بدون نیاز به مجوز، مستقیماً چاپ می‌گیرند؛
    #  نقش‌های سفارشی مبتنی بر مدیریت/مدیر کل نیز همین قاعده را ارث می‌برند؛
    #  برای کارمند فعال بودن مجوز «can_print_without_approval» لازم است)
    if bijak.approval_status != "approved" and not can_print_without_approval(request.user):
        messages.error(request, "چاپ این بارنامه فقط بعد از تأیید مدیر امکان‌پذیر است.")
        return HttpResponseForbidden("چاپ مجاز نیست")

    # در این مرحله بارنامه مجاز به چاپ است
    # (مهر و امضای دیجیتال بر اساس مجوز نقش کاربر فعال/غیرفعال می‌شود)
    return render(
        request,
        'issuance/bijak/final_bijak.html',
        _print_context(bijak, request)
    )
