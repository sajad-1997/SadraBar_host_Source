# 2️⃣ utils.py (توابع عمومی و Helperها)

import jdatetime
from django.contrib import messages
import re


FIELD_LABELS = {
    "issuance_date": "تاریخ صدور بارنامه",
    "issuance_time": "ساعت صدور بارنامه",
    "sender": "فرستنده",
    "receiver": "گیرنده",
    "driver": "راننده",
    "vehicle": "وسیله نقلیه",
}

ERROR_TRANSLATIONS = {
    "This field is required.": "تکمیل این فیلد الزامی است.",
    "Enter a valid date.": "تاریخ وارد شده معتبر نیست.",
    "Enter a valid time.": "ساعت وارد شده معتبر نیست.",
    "Enter a valid value.": "مقدار وارد شده معتبر نیست.",
    "Ensure this value is greater than or equal to 0.": "مقدار وارد شده نمی‌تواند منفی باشد.",
    "Enter a valid date/time in YYYY-MM-DD HH:MM[:ss[.uuuuuu]] format.":
        "تاریخ یا ساعت صدور بارنامه به‌درستی وارد نشده است.",
}


def show_form_errors(request, form, section_title=None):
    for field, errors in form.errors.items():
        label = form.fields[field].label if field in form.fields else FIELD_LABELS.get(field, field)
        for error in errors:
            msg = ERROR_TRANSLATIONS.get(error, error)
            if section_title:
                messages.error(request, f"{section_title} - {label}: {msg}")
            else:
                messages.error(request, f"{label}: {msg}")


def persian_to_english_numbers(value):
    if not value:
        return value
    persian = '۰۱۲۳۴۵۶۷۸۹'
    english = '0123456789'
    return value.translate(str.maketrans(persian, english))


def to_jalali(date_obj):
    if not date_obj:
        return "—"
    return jdatetime.date.fromgregorian(date=date_obj).strftime("%Y/%m/%d")




def normalize_caption(text):
    if not text:
        return ""

    text = text.strip()

    # عربی به فارسی
    text = text.replace("ي", "ی")
    text = text.replace("ك", "ک")

    # حذف نیم فاصله
    text = text.replace("\u200c", " ")

    # حذف فاصله های اضافی
    text = re.sub(r"\s+", " ", text)

    # حذف فاصله قبل از علائم
    text = re.sub(r"\s+([.,،؛:!?])", r"\1", text)

    return text