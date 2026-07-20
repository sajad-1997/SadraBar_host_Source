from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, render

from issuance.models import Bijak


@login_required
def bijak_print(request, pk):
    bijak = get_object_or_404(Bijak, pk=pk)

    # جلوگیری از چاپ قبل از تایید
    if bijak.approval_status != "approved":
        messages.error(request, "چاپ این بارنامه فقط بعد از تأیید مدیر امکان‌پذیر است.")
        return HttpResponseForbidden("چاپ مجاز نیست")

    # در این مرحله بارنامه مجاز به چاپ است
    return render(request, "issuance/bijak_print.html", {"bijak": bijak})
