# jalali_filters.py
import jdatetime
from django import template

register = template.Library()


@register.filter
def to_jalali(value, format='%Y/%m/%d'):
    """
    تبدیل تاریخ میلادی به شمسی
    استفاده در تمپلیت: {{ driver.birth_date|to_jalali }}
    """
    if not value:
        return ''

    try:
        # اگر شیء datetime است، به date تبدیل کن
        if hasattr(value, 'date'):
            value = value.date()

        jalali_date = jdatetime.date.fromgregorian(date=value)
        return jalali_date.strftime(format)
    except (ValueError, AttributeError, TypeError) as e:
        # در صورت خطا، مقدار اصلی را برگردان
        return str(value)


@register.filter
def jalali_date(value):
    """نام مستعار برای to_jalali"""
    return to_jalali(value)


@register.filter
def jalali_datetime(value, format='%Y/%m/%d %H:%M'):
    if value:
        try:
            if hasattr(value, 'date'):
                date_part = value.date()
                time_part = value.time()
                jalali_date = jdatetime.date.fromgregorian(date=date_part)
                return f"{jalali_date.strftime('%Y/%m/%d')} {time_part.strftime('%H:%M')}"
            else:
                return to_jalali(value)
        except Exception as e:
            print(f"Error converting datetime: {e}")
            return value
    return value
