from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone

from issuance.models import Bijak, BijakApprovalLog


def is_admin_or_manager(user):
    return user.is_superuser or user.role in ['admin', 'manager']


@login_required
def send_for_approval(request, bijak_id):
    bijak = get_object_or_404(Bijak, id=bijak_id)

    if bijak.approval_status != "pending":
        messages.warning(request, "این بارنامه قبلاً بررسی شده است.")
        return redirect(reverse("issuance:manager:manager_preview", args=[bijak.id]))

    messages.success(request, "بارنامه با موفقیت برای بررسی مدیر ارسال شد.")
    return redirect(reverse("issuance:manager:manager_preview", args=[bijak.id]))


@login_required
@user_passes_test(is_admin_or_manager)
def approve_bijak(request, bijak_id):
    bijak = get_object_or_404(Bijak, id=bijak_id)

    if bijak.is_approved:
        messages.warning(request, "این بارنامه قبلاً تأیید شده است.")
        return redirect(reverse("issuance:manager:waiting_list"))

    bijak.approval_status = "approved"
    bijak.status = "issued"
    bijak.approved_by = request.user
    bijak.approved_at = timezone.now()
    bijak.save()

    BijakApprovalLog.objects.create(
        bijak=bijak,
        user=request.user,
        action="approved",
    )

    messages.success(request, "بارنامه تأیید شد و مجوز چاپ گرفت.")
    return redirect(reverse("issuance:manager:waiting_list"))


@login_required
@user_passes_test(is_admin_or_manager)
def reject_bijak(request, bijak_id):
    bijak = get_object_or_404(Bijak, id=bijak_id)
    reason = request.POST.get("reason", "").strip()

    if not reason:
        messages.error(request, "علت رد باید وارد شود.")
        return redirect(reverse("issuance:manager:waiting_list"))

    bijak.approval_status = "rejected"
    bijak.status = "draft"
    bijak.rejected_by = request.user
    bijak.reject_reason = reason
    bijak.save()

    BijakApprovalLog.objects.create(
        bijak=bijak,
        user=request.user,
        action="rejected",
        reason=reason
    )

    messages.error(request, "بارنامه رد شد.")
    return redirect(reverse("issuance:manager:waiting_list"))
