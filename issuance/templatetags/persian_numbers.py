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
