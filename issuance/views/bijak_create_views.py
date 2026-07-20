# 3️⃣ bijak_create_views.py (ایجاد بارنامه)

from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.cache import never_cache

# دیگر نیازی به khayyam نیست
# from khayyam import JalaliDatetime

from .utils import persian_to_english_numbers, show_form_errors, normalize_caption
from ..forms import ShipmentForm, CargoForm
from ..models import Customer, Driver, Vehicle, Caption


@login_required
@never_cache
def create_new(request):
    captions = Caption.objects.all().order_by("-id")
    user_role = getattr(request.user, "role", "staff")

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
    # -------------------------------
    if custom_caption:

        normalized_input = normalize_caption(custom_caption)

        duplicate_caption = Caption.objects.filter(
            content__isnull=False
        )

        for caption in duplicate_caption:

            if normalize_caption(caption.content) == normalized_input:

                messages.warning(
                    request,
                    "این توضیح قبلاً ثبت شده است. لطفاً از لیست توضیحات آماده انتخاب کنید."
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

    messages.success(
        request,
        "بارنامه با موفقیت ثبت شد و در انتظار تأیید مدیریت است."
    )

    if user_role == "staff":
        return redirect("issuance:crud:pending")

    return redirect(
        "issuance:crud:preview",
        pk=bijak.id,
    )