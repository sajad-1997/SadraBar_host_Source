from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render

from issuance.models import Bijak


def is_manager(user):
    return user.is_superuser or getattr(user, 'role', None) in ['admin', 'manager']


@login_required
@user_passes_test(is_manager)
def waiting_list(request):
    # بهینه‌سازی کوئری با select_related برای کاهش تعداد queryهای دیتابیس
    base_queryset = Bijak.objects.select_related(
        'sender',
        'receiver',
        'driver',
        'vehicle',
        'cargo'
    )
    
    # بارنامه‌های در انتظار تایید
    shipments_pending = base_queryset.filter(
        approval_status='pending'
    ).order_by('-id')

    # بارنامه‌های تایید شده
    shipments_approved = base_queryset.filter(
        approval_status='approved'
    ).order_by('-id')

    # بارنامه‌های رد شده
    shipments_rejected = base_queryset.filter(
        approval_status='rejected'
    ).order_by('-id')

    return render(
        request,
        'issuance/manager/waiting_list.html',
        {
            'shipments_pending': shipments_pending,
            'shipments_approved': shipments_approved,
            'shipments_rejected': shipments_rejected,
        }
    )
