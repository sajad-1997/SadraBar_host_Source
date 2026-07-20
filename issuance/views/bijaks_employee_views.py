# views_employee_pending_bijaks.py
# views_employee_pending_bijaks.py
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render
from issuance.models import Bijak


@login_required
def pending_bijaks(request):
    """
    نمایش بارنامه‌های ایجاد شده توسط کارمند که در انتظار تأیید یا رد مدیریت هستند.
    """
    search_query = request.GET.get('q', '').strip()

    bijaks = Bijak.objects.filter(
        created_by=request.user,
        approval_status__in=['pending', 'rejected', 'approved']
    ).order_by('-id')

    if search_query:
        bijaks = bijaks.filter(
            Q(id__icontains=search_query) |
            Q(sender__name__icontains=search_query) |
            Q(receiver__name__icontains=search_query) |
            Q(driver__name__icontains=search_query) |
            Q(driver__phone__icontains=search_query) |
            Q(driver__national_id__icontains=search_query)
        )

    paginator = Paginator(bijaks, 25)  # 25 بارنامه در هر صفحه
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # محاسبه لیست فشرده صفحات (الاید شده)
    # on_each_side=1 : یک صفحه قبل و بعد از صفحه فعلی
    # on_ends=1 : فقط صفحه اول و آخر (بدون سه نقطه در دو انتها)
    elided_page_range = paginator.get_elided_page_range(
        page_obj.number,
        on_each_side=1,
        on_ends=1
    )

    context = {
        'bijaks': page_obj,
        'search_query': search_query,
        'elided_page_range': elided_page_range,  # اضافه شد
        'ELLIPSIS': paginator.ELLIPSIS,          # مقدار سه‌نقطه (معمولاً '…')
    }
    return render(request, 'issuance/bijak/bijak_list_waiting.html', context)