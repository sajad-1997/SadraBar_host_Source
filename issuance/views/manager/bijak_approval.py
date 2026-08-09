from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from issuance.models import Bijak


def is_manager(user):
    """فقط مدیر یا ادمین مجاز است"""
    return user.is_superuser or getattr(user, 'role', None) in ['admin', 'manager']


@login_required
@user_passes_test(is_manager)
def bijak_list_waiting_approval(request):
    """نمایش لیست بارنامه‌های در حالت در انتظار تایید"""
    bijaks = Bijak.objects.filter(approval_status="pending").order_by('-id')
    return render(request, 'issuance/bijak/bijak_list_waiting.html', {'bijaks': bijaks})


@login_required
@user_passes_test(is_manager)
def bijak_approve_view(request, pk):
    """نمایش پیش‌نمایش بارنامه برای تایید یا رد"""
    bijak = get_object_or_404(Bijak, pk=pk)
    return render(request, 'issuance/bijak/bijak_approve.html', {'bijak': bijak})


@login_required
@user_passes_test(is_manager)
def bijak_approve_submit(request, pk):
    from django.db import transaction
    
    with transaction.atomic():
        bijak = get_object_or_404(
            Bijak.objects.select_for_update(),
            pk=pk
        )

        action = request.POST.get("action")

        if not action:
            messages.error(request, "عملیات نامعتبر.")
            return redirect(reverse('issuance:bijak_approval:bijak_approve', args=[pk]))

        # جلوگیری از تأیید دوباره
        if bijak.is_approved:
            messages.warning(request, "این بارنامه قبلاً تأیید شده است.")
            return redirect(reverse('issuance:crud:preview', args=[pk]))

        # جلوگیری از رد دوباره
        if bijak.is_rejected:
            messages.warning(request, "این بارنامه قبلاً رد شده است.")
            return redirect(reverse('issuance:crud:preview', args=[pk]))

        # عملیات تأیید
        if action == "approve":
            bijak.approval_status = "approved"
            bijak.approved_by = request.user
            bijak.save()

            messages.success(request, "بارنامه با موفقیت تأیید شد.")
            return redirect(reverse('issuance:crud:preview', args=[pk]))

        # عملیات رد
        elif action == "reject":
            reject_reason = request.POST.get("reject_reason", "")

            if not reject_reason.strip():
                messages.error(request, "علت رد بارنامه باید نوشته شود.")
                return redirect(reverse('issuance:bijak_approval:bijak_approve', args=[pk]))

            # دریافت مجوزهای ویرایش از فرم
            bijak.can_edit_sender = request.POST.get("can_edit_sender") == "on"
            bijak.can_edit_receiver = request.POST.get("can_edit_receiver") == "on"
            bijak.can_edit_driver = request.POST.get("can_edit_driver") == "on"
            bijak.can_edit_cargo = request.POST.get("can_edit_cargo") == "on"
            bijak.can_edit_financial = request.POST.get("can_edit_financial") == "on"

            bijak.approval_status = "rejected"
            bijak.rejected_by = request.user
            bijak.reject_reason = reject_reason
            bijak.save()

            messages.error(request, "بارنامه رد شد.")
            return redirect(reverse('issuance:crud:preview', args=[pk]))

        else:
            messages.error(request, "درخواست ناشناخته.")
            return redirect(reverse('issuance:bijak_approval:bijak_approve', args=[pk]))
