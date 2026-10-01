import jdatetime
from django.utils import timezone


def to_jalali(gdate):
    """تبدیل تاریخ میلادی به شمسی"""
    if not gdate:
        return None
    return jdatetime.date.fromgregorian(date=gdate)


def jalali_today():
    """تاریخ شمسی امروز (بر اساس منطقه زمانی پروژه)"""
    return to_jalali(timezone.now().date())


def jalali_str(jd):
    """نمایش رشته‌ای تاریخ شمسی به فرمت YYYY/MM/DD"""
    return jd.strftime('%Y/%m/%d') if jd else '-'


def format_jalali_datetime(dt):
    """نمایش تاریخ و ساعت شمسی برای یک datetime"""
    if not dt:
        return '-'
    jd = to_jalali(dt.date())
    return f'{jd.strftime("%Y/%m/%d")} - {dt.strftime("%H:%M")}'


def parse_jalali_date(value, default=None):
    """تبدیل رشته تاریخ شمسی 'YYYY/MM/DD' به jdatetime.date"""
    if not value:
        return default
    try:
        parts = value.replace('-', '/').split('/')
        return jdatetime.date(int(parts[0]), int(parts[1]), int(parts[2]))
    except (ValueError, IndexError, TypeError):
        return default


def today_start():
    """آغاز روز جاری به عنوان datetime محلی"""
    now = timezone.now()
    return now.replace(hour=0, minute=0, second=0, microsecond=0)
