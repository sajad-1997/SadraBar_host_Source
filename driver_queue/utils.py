from datetime import datetime
from math import asin, cos, radians, sin, sqrt
from re import search
from urllib.parse import parse_qs, urlparse
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


def extract_coordinates_from_url(location_url: str) -> tuple[float, float] | None:
    """
    استخراج مختصات (lat, lng) از لینک لوکیشن گوگل مپ یا سایر سرویس‌ها.
    
    پشتیبانی از فرمت‌های مختلف:
    - Google Maps: https://maps.google.com/?q=35.6997,51.3380
    - Google Maps: https://www.google.com/maps/@35.6997,51.3380,15z
    - Google Maps: https://www.google.com/maps/place/35.6997,51.3380
    - Waze: https://waze.com/ul?ll=35.6997,51.3380
    - Direct coordinates: 35.6997,51.3380
    
    Returns:
        tuple (lat, lng) یا None اگر نتوانست استخراج کند
    """
    if not location_url:
        return None
    
    try:
        # اگر مستقیماً مختصات باشد
        if search(r'^-?\d+\.?\d*,-?\d+\.?\d*$', location_url.strip()):
            lat, lng = map(float, location_url.strip().split(','))
            return lat, lng
        
        # اگر URL باشد
        parsed = urlparse(location_url)
        
        # بررسی query parameters
        query_params = parse_qs(parsed.query)
        
        # Google Maps q parameter
        if 'q' in query_params:
            q_value = query_params['q'][0]
            if search(r'^-?\d+\.?\d*,-?\d+\.?\d*$', q_value):
                lat, lng = map(float, q_value.split(','))
                return lat, lng
        
        # Google Maps @ parameter (in path)
        if '@' in parsed.path:
            coords_part = parsed.path.split('@')[1].split(',')[0:2]
            if len(coords_part) == 2:
                lat, lng = map(float, coords_part)
                return lat, lng
        
        # Waze ll parameter
        if 'll' in query_params:
            ll_value = query_params['ll'][0]
            if search(r'^-?\d+\.?\d*,-?\d+\.?\d*$', ll_value):
                lat, lng = map(float, ll_value.split(','))
                return lat, lng
        
        # جستجوی الگوی مختصات در کل URL
        coords_match = search(r'(-?\d+\.?\d*),(-?\d+\.?\d*)', location_url)
        if coords_match:
            lat, lng = map(float, coords_match.groups())
            return lat, lng
            
    except (ValueError, IndexError, AttributeError):
        return None
    
    return None
