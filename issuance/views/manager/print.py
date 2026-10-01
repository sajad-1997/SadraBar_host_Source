from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, render

from issuance.models import Bijak
from issuance.views.bijak_print_views import _print_context


@login_required
def bijak_print(request, bijak_id):
    bijak = get_object_or_404(Bijak, id=bijak_id)

    if not bijak.can_print:
        return HttpResponseForbidden("این بارنامه هنوز تأیید نشده یا صادر نشده است.")

    # قالب final_bijak.html متغیر shipment را مصرف می‌کند
    return render(request, 'issuance/bijak/final_bijak.html', _print_context(bijak, request))
