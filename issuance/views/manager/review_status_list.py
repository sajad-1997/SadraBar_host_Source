from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.shortcuts import render

from issuance.models import Bijak


def is_manager(user):
    return user.is_superuser or getattr(user, 'role', None) in ['admin', 'manager']


@login_required
@user_passes_test(is_manager)
def final_status_list(request):
    shipments = Bijak.objects.all().order_by('-id')

    status_groups = [
        ('draft', 'پیش‌نویس'),
        ('sent', 'ارسال شده'),
        ('Sent-Customer Version', 'ارسال شده-نسخه مشتری'),
        ('Sent-Driver Version', 'ارسال شده-نسخه راننده'),
        ('delivered', 'تحویل شده'),
        ('Delivered-Customer Version', 'تحویل شده-نسخه مشتری'),
        ('Delivered-Driver Version', 'تحویل شده-نسخه راننده'),
        ('canceled', 'لغو شده'),
        ('inactive', 'تکراری-غیر فعال'),
    ]

    # بارنامه‌های تعیین نشده (NULL یا رشته خالی)
    unassigned_shipments = shipments.filter(Q(type__isnull=True) | Q(type=''))

    context = {
        'shipments': shipments,
        'status_groups': status_groups,
        'unassigned_shipments': unassigned_shipments,
    }
    return render(request, 'issuance/manager/status_list.html', context)
