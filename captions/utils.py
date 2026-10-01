# 1️⃣ utils.py ماژول captions (توابع عمومی توضیحات)

import re


def normalize_caption(text):
    """نرمال‌سازی متن توضیح برای مقایسه (یکنواخت‌سازی املایی)"""
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
