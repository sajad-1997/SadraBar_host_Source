from django import template

register = template.Library()

EN_TO_FA_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


@register.filter(name='persian_numbers')
def persian_numbers(value):
    """
    تبدیل همه اعداد انگلیسی به فارسی در قالب‌ها
    """
    if value is None:
        return ""
    return str(value).translate(EN_TO_FA_DIGITS)


@register.filter(name='persian_currency')
def persian_currency(value):
    """
    تبدیل عدد به فرمت پولی فارسی با کاما جداکننده
    """
    if value is None:
        return ""

    # تبدیل به رشته و حذف اعشار
    try:
        num = float(value)
        value_str = f"{int(num)}"
    except (ValueError, TypeError):
        value_str = str(value)

    # اضافه کردن کاما جداکننده
    if value_str.isdigit():
        # جدا کردن سه رقم سه رقم از سمت راست
        parts = []
        for i in range(len(value_str), 0, -3):
            start = max(0, i - 3)
            parts.insert(0, value_str[start:i])
        value_str = '،'.join(parts)

    # تبدیل اعداد به فارسی
    return value_str.translate(EN_TO_FA_DIGITS)
