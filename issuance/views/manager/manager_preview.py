from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from issuance.models import Bijak, BijakApprovalLog


def is_manager(user):
    return user.is_superuser or user.role in ['admin', 'manager']

@login_required
def manager_preview_page(request, pk):
    bijak = get_object_or_404(Bijak, pk=pk)

    # فقط مدیران می‌توانند وضعیت بارنامه را تغییر دهند
    if request.method == "POST" and is_manager(request.user):
        action = request.POST.get("action")
        reject_reason = request.POST.get("reject_reason", "").strip()

        if action == "approve":
            bijak.approval_status = "approved"
            bijak.status = "issued"  # تغییر وضعیت به صادر شده
            bijak.approved_by = request.user
            bijak.approved_at = timezone.now()
            bijak.reject_reason = ""
            bijak.save()

            # ایجاد لاگ
            BijakApprovalLog.objects.create(
                bijak=bijak,
                user=request.user,
                action="approve",
                reason="بارنامه تأیید شد"
            )

            messages.success(request, "بارنامه با موفقیت تأیید شد")

        elif action == "reject":
            if not reject_reason:
                messages.error(request, "در صورت رد بارنامه، علت رد الزامی است")
                return redirect("issuance:manager:manager_preview", pk=bijak.id)
            bijak.approval_status = "rejected"
            bijak.status = "draft"  # باقی ماندن در حالت پیش‌نویس برای اصلاح
            bijak.reject_reason = reject_reason
            bijak.save()

            # ایجاد لاگ
            BijakApprovalLog.objects.create(
                bijak=bijak,
                user=request.user,
                action="reject",
                reason=reject_reason
            )

            messages.success(request, "بارنامه رد شد و علت ثبت شد")

        return redirect("issuance:manager:manager_preview", pk=bijak.id)

    # دریافت لاگ‌ها برای نمایش تایم‌لاین
    logs = BijakApprovalLog.objects.filter(bijak=bijak).order_by("-created_at")

    context = {
        "bijak": bijak,
        "is_manager": is_manager(request.user),
        "logs": logs
    }
    return render(request, "issuance/manager/manager_preview.html", context)
