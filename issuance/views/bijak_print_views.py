# 6️⃣ bijak_print_views.py

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from accounts.decorators import can_use_digital_stamp
from issuance.models import Bijak, BijakApprovalLog
from .utils import to_jalali


def is_manager(user):
    from accounts.decorators import ROLE_MANAGER, ROLE_ADMIN
    return user.role in [ROLE_MANAGER, ROLE_ADMIN] or user.is_superuser


def _print_context(bijak, request, use_weight_2=False, want_stamp=True, want_signature=True):
    """ساخت کانتکست صفحات چاپ با اعمال مجوز مهر و امضای دیجیتال.

    - اگر کاربر مجوز نداشته باشد، مهر/امضا به‌صورت سروری غیرفعال می‌شود
      (حتی اگر پارامتر stamp/signature در URL باشد).
    - کنترل نمایش دکمه‌ها در قالب با can_use_digital_stamp انجام می‌شود.
    """
    allowed = can_use_digital_stamp(request.user)
    return {
        'shipment': bijak,
        'jalali_date': to_jalali(bijak.issuance_datetime),
        'use_digital_stamp': allowed and want_stamp,
        'use_digital_signature': allowed and want_signature,
        'can_use_digital_stamp': allowed,
        'use_weight_2': use_weight_2,
    }


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
        "can_use_digital_stamp": can_use_digital_stamp(request.user),
    }

    return render(
        request,
        'issuance/secondary/preview.html',
        context
    )


@login_required
def print_page(request, pk):
    bijak = get_object_or_404(Bijak, pk=pk)
    return render(request, 'issuance/bijak/final_bijak.html',
                  _print_context(bijak, request, use_weight_2=False))


@login_required
def print_page_weight2(request, pk):
    bijak = get_object_or_404(Bijak, pk=pk)
    return render(request, 'issuance/bijak/final_bijak.html',
                  _print_context(bijak, request, use_weight_2=True))


@login_required
def print_page_with_stamp(request, pk):
    bijak = get_object_or_404(Bijak, pk=pk)
    return render(request, 'issuance/bijak/final_bijak.html',
                  _print_context(bijak, request, want_stamp=True))


@login_required
def generate_pdf(request, pk):
    """تولید PDF بارنامه با ابعاد A4 شامل دو صفحه A5 افقی"""
    from django.http import HttpResponse
    from django.template.loader import render_to_string
    from weasyprint import HTML, CSS
    import io

    bijak = get_object_or_404(Bijak, pk=pk)

    # اعمال مجوز: اگر کاربر اجازه نداشته باشد، پارامترهای stamp/signature نادیده گرفته می‌شوند
    allowed = can_use_digital_stamp(request.user)
    use_stamp = allowed and request.GET.get('stamp') == '1'
    use_signature = allowed and request.GET.get('signature') == '1'
    use_weight2 = request.GET.get('weight2') == '1'

    context = {
        'shipment': bijak,
        'jalali_date': to_jalali(bijak.issuance_datetime),
        'use_digital_stamp': use_stamp,
        'use_digital_signature': use_signature,
        'use_weight_2': use_weight2,
    }

    html_string = render_to_string('issuance/bijak/final_bijak_pdf.html', context)

    # تنظیمات CSS برای A4 با دو صفحه A5 افقی
    css_string = '''
        @page {
            size: A4 portrait;
            margin: 10mm;
        }
        @media print {
            body {
                margin: 0;
            }
            .container {
                width: 100%;
                height: 100%;
                page-break-after: always;
            }
        }
    '''

    html = HTML(string=html_string)
    css = CSS(string=css_string)

    pdf_file = html.write_pdf(stylesheets=[css])

    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="bijak_{bijak.tracking_code}.pdf"'
    return response
