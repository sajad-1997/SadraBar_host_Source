from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from issuance.models import Bijak, BijakFinalStatusLog

ALLOWED_UNLOCK_ROLES = ['admin', 'manager']


def is_manager(user):
    return user.is_superuser or user.is_staff or getattr(user, 'is_manager', False)


@login_required
def manager_set_final_status(request, pk):
    b = get_object_or_404(Bijak, pk=pk)

    # بررسی نقش مدیریتی
    # is_manager = request.user.groups.filter(
    #     name__in=ALLOWED_UNLOCK_ROLES
    # ).exists()

    can_override_lock = (
            request.user.is_superuser
            or request.user.is_staff
            or is_manager
    )

    logs = BijakFinalStatusLog.objects.filter(
        bijak=b
    ).order_by('-created_at')

    # 🔒 قفل فقط برای کاربر عادی
    is_locked = logs.exists() and not can_override_lock

    if request.method == "POST":

        if is_locked:
            messages.error(
                request,
                "این بارنامه قبلاً نهایی شده و امکان تغییر برای شما وجود ندارد."
            )
            return redirect('issuance:manager:manager_status', pk=b.pk)

        final_status = request.POST.get("final_status")
        note = request.POST.get("note", "").strip()

        # اعتبارسنجی وضعیت
        if final_status not in dict(Bijak.TYPE_CHOICES).keys():
            messages.error(request, "وضعیت انتخاب‌شده معتبر نیست.")
            return redirect('issuance:manager:manager_status', pk=b.pk)

        # 🔴 توضیح برای همه اجباری
        if not note:
            messages.error(request, "وارد کردن توضیح الزامی است.")
            return redirect('issuance:manager:manager_status', pk=b.pk)

        old_status = b.type

        # اگر وضعیت تغییر نکرده، فقط پیام بده
        if old_status == final_status:
            messages.warning(
                request,
                "وضعیت انتخاب‌شده با وضعیت فعلی یکسان است."
            )
            return redirect('issuance:manager:manager_status', pk=b.pk)

        # ثبت تغییر
        b.type = final_status
        b.save()

        # ثبت لاگ دقیق و شفاف
        BijakFinalStatusLog.objects.create(
            bijak=b,
            user=request.user,
            old_status=old_status,
            new_status=final_status,
            note=note
        )

        messages.success(request, "وضعیت با موفقیت ثبت شد.")
        return redirect('issuance:manager:manager_status', pk=b.pk)

    context = {
        'b': b,
        'logs': logs,
        'is_locked': is_locked,
        'can_override_lock': can_override_lock,
    }

    return render(request, 'issuance/manager/manager_status.html', context)
