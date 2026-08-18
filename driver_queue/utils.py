from datetime import datetime
from math import asin, cos, radians, sin, sqrt
from zoneinfo import ZoneInfo

from django.conf import settings
from django.utils import timezone

from . import conf

_FA_TO_EN = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")
_AR_TO_EN = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")


def normalize_digits(value: str) -> str:
    """تبدیل ارقام فارسی/عربی به لاتین."""
    return (value or "").translate(_FA_TO_EN).translate(_AR_TO_EN)


def is_valid_national_id(code: str) -> bool:
    """اعتبارسنجی کد ملی ایران با الگوریتم چک‌سام رسمی."""
    code = normalize_digits(code).strip()
    if len(code) != 10 or not code.isdigit() or len(set(code)) == 1:
        return False
    remainder = sum(int(d) * (10 - i) for i, d in enumerate(code[:9])) % 11
    control = remainder if remainder < 2 else 11 - remainder
    return int(code[-1]) == control


def haversine_km(lat1, lng1, lat2, lng2) -> float:
    """فاصله تقریبی دو نقطه جغرافیایی بر حسب کیلومتر."""
    la1, lo1, la2, lo2 = map(radians, (lat1, lng1, lat2, lng2))
    dlat, dlng = la2 - la1, lo2 - lo1
    a = sin(dlat / 2) ** 2 + cos(la1) * cos(la2) * sin(dlng / 2) ** 2
    return 2 * 6371.0088 * asin(sqrt(a))


def tehran_now() -> datetime:
    """
    زمان حال در منطقه زمانی ماژول (پیش‌فرض تهران).
    - اگر USE_TZ=True باشد: datetime آگاه (aware) برمی‌گرداند.
    - اگر USE_TZ=False باشد: datetime ساده (naive) برمی‌گرداند تا با
      دیتابیس‌هایی مثل SQLite در حالت بدون timezone سازگار باشد.
    """
    tz = ZoneInfo(conf.TIMEZONE)
    if settings.USE_TZ:
        return timezone.now().astimezone(tz)
    return datetime.now(tz).replace(tzinfo=None)
