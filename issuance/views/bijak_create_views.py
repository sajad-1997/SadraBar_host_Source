# 3️⃣ bijak_create_views.py (ایجاد بارنامه)

from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.cache import never_cache

# دیگر نیازی به khayyam نیست
# from khayyam import JalaliDatetime

from .utils import persian_to_english_numbers, show_form_errors
from accounts.decorators import ROLE_ADMIN, ROLE_MANAGER
from system_control.services import check_issuance_allowed
from ..forms import ShipmentForm
from captions.models import Caption
from captions.utils import normalize_caption
from customers.models import Customer
from drivers.models import Driver
from fleet.models import Vehicle
from cargo.forms import CargoForm

@login_required
@never_cache
def create_new(request):
    captions = Caption.objects.all().order_by("-id")
    user_role = getattr(request.user, "role", "employee")

    # -------------------------------
    # کنترل سهمیه صدور بارنامه
    # (بر اساس آمار صدور و محدودیت‌های تعیین‌شده توسط سوپر ادمین)
    # -------------------------------
    quota_ok, quota_message, quota_statuses = check_issuance_allowed(request.user)
    if not quota_ok:
        messages.error(request, quota_message)
        return redirect("issuance:crud:pending")

    # مقادیر پیش فرض برای نمایش مجدد فرم
    selected_caption_id = None
    custom_caption = ""

    # -------------------------------
    # نمایش فرم
    # -------------------------------
    if request.method != "POST":
        return render(
            request,
            "issuance/bijak/issuance_form.html",
            {
                "shipment_form": ShipmentForm(prefix="shipment"),
                "cargo_form": CargoForm(prefix="cargo"),
                "captions": captions,
                "user_role": user_role,
                "selected_caption_id": selected_caption_id,
                "custom_caption": custom_caption,
            },
        )

    # -------------------------------
    # فرم ها
    # -------------------------------
    shipment_form = ShipmentForm(request.POST, prefix="shipment")
    cargo_form = CargoForm(request.POST, prefix="cargo")

    # توضیحات
    custom_caption = request.POST.get(
        "shipment-custom_caption",
        ""
    ).strip()

    selected_caption_id = request.POST.get(
        "shipment-selected_caption"
    )

    # -------------------------------
    # اعتبارسنجی فرم ها
    # -------------------------------
    if not (shipment_form.is_valid() and cargo_form.is_valid()):
        show_form_errors(request, shipment_form, "اطلاعات بارنامه")
        show_form_errors(request, cargo_form, "اطلاعات محموله")

        return render(
            request,
            "issuance/bijak/issuance_form.html",
            {
                "shipment_form": shipment_form,
                "cargo_form": cargo_form,
                "captions": captions,
                "user_role": user_role,
                "selected_caption_id": selected_caption_id,
                "custom_caption": custom_caption,
            },
        )

    # -------------------------------
    # فرستنده / گیرنده / راننده
    # -------------------------------
    sender_id = request.POST.get("sender")
    receiver_id = request.POST.get("receiver")
    driver_id = request.POST.get("driver")

    if not sender_id or not receiver_id or not driver_id:
        messages.error(
            request,
            "انتخاب فرستنده، گیرنده و راننده الزامی است."
        )

        return render(
            request,
            "issuance/bijak/issuance_form.html",
            {
                "shipment_form": shipment_form,
                "cargo_form": cargo_form,
                "captions": captions,
                "user_role": user_role,
                "selected_caption_id": selected_caption_id,
                "custom_caption": custom_caption,
            },
        )

    # -------------------------------
    # تاریخ و ساعت
    # -------------------------------
    issuance_datetime = shipment_form.cleaned_data.get(
        "issuance_datetime"
    )

    if not issuance_datetime:
        messages.error(
            request,
            "تاریخ یا ساعت وارد شده معتبر نیست."
        )

        return render(
            request,
            "issuance/bijak/issuance_form.html",
            {
                "shipment_form": shipment_form,
                "cargo_form": cargo_form,
                "captions": captions,
                "user_role": user_role,
                "selected_caption_id": selected_caption_id,
                "custom_caption": custom_caption,
            },
        )

    # -------------------------------
    # بررسی تکراری بودن توضیح دستی
    # (به جای متوقف کردن ثبت، توضیح موجود مجدداً استفاده می‌شود)
    # -------------------------------
    existing_caption = None

    if custom_caption:

        normalized_input = normalize_caption(custom_caption)

        for caption in Caption.objects.filter(content__isnull=False):

            if normalize_caption(caption.content) == normalized_input:
                existing_caption = caption
                break

    # -------------------------------
    # دریافت اطلاعات
    # -------------------------------
    sender = get_object_or_404(Customer, pk=sender_id)
    receiver = get_object_or_404(Customer, pk=receiver_id)
    driver = get_object_or_404(Driver, pk=driver_id)

    vehicle = (
        Vehicle.objects.filter(driver=driver)
        .order_by("-id")
        .first()
    )

    if not vehicle:

        messages.error(
            request,
            "برای راننده انتخاب‌شده وسیله نقلیه ثبت نشده است."
        )

        return render(
            request,
            "issuance/bijak/issuance_form.html",
            {
                "shipment_form": shipment_form,
                "cargo_form": cargo_form,
                "captions": captions,
                "user_role": user_role,
                "selected_caption_id": selected_caption_id,
                "custom_caption": custom_caption,
            },
        )

    # -------------------------------
    # ذخیره
    # -------------------------------
    with transaction.atomic():

        cargo = cargo_form.save()

        bijak = shipment_form.save(commit=False)

        caption_obj = None

        # اگر توضیح دستی وارد شده باشد
        if custom_caption:

            if existing_caption:
                # توضیح مشابه قبلاً ثبت شده؛ همان توضیح استفاده می‌شود
                caption_obj = existing_caption
            else:
                caption_obj = Caption.objects.create(
                    name=custom_caption[:100],
                    content=custom_caption,
                )

        # اگر توضیح آماده انتخاب شده باشد
        elif selected_caption_id:

            caption_obj = Caption.objects.filter(
                pk=selected_caption_id
            ).first()

        # اطلاعات اصلی
        bijak.sender = sender
        bijak.receiver = receiver
        bijak.driver = driver
        bijak.vehicle = vehicle
        bijak.cargo = cargo
        bijak.issuance_datetime = issuance_datetime
        bijak.status = "draft"
        bijak.approval_status = "pending"

        # توضیحات
        bijak.selected_caption = caption_obj
        bijak.custom_caption = custom_caption

        bijak.save()

    # کاربران دارای نقش ادمین/مدیریت (و سوپریوزر) مستقیماً به صفحه پیش‌نمایش
    # مدیریتی (تصمیم‌گیری تأیید یا رد بارنامه) هدایت می‌شوند
    is_manager_role = (
        request.user.is_superuser
        or user_role in [ROLE_ADMIN, ROLE_MANAGER]
    )

    if is_manager_role:
        messages.success(
            request,
            "بارنامه با موفقیت ثبت شد. برای تأیید یا رد، تصمیم‌گیری کنید."
        )

        return redirect(
            "issuance:manager:manager_preview",
            pk=bijak.id,
        )

    # کاربران با نقش کارمند همان پیش‌نمایش عادی بارنامه را می‌بینند
    messages.success(
        request,
        "بارنامه با موفقیت ثبت شد و در انتظار تأیید مدیریت است."
    )

    return redirect(
        "issuance:crud:preview",
        pk=bijak.id,
    )