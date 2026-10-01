"""
تنظیمات ماژول نوبت‌دهی.
همه مقادیر در لحظه دسترسی از settings خوانده می‌شوند (PEP 562)
تا با override_settings در تست‌ها سازگار باشند.
"""
from django.conf import settings

from .utils import extract_coordinates_from_url


def __getattr__(name):
    if name == "DRIVER_MODEL":
        # مدل راننده ماژول شما؛ اگر app label متفاوت است تغییر دهید
        return getattr(settings, "QUEUE_DRIVER_MODEL", "drivers.Driver")
    if name == "TIMEZONE":
        return getattr(settings, "QUEUE_TIMEZONE", getattr(settings, "TIME_ZONE", "Asia/Tehran"))
    if name == "START_TIME":
        return getattr(settings, "QUEUE_START_TIME", "08:00")
    if name == "END_TIME":
        return getattr(settings, "QUEUE_END_TIME", "11:00")
    if name == "ANNOUNCE_TIME":
        return getattr(settings, "QUEUE_ANNOUNCE_TIME", "11:00")
    if name == "ANNOUNCE_WINDOW_MINUTES":
        return int(getattr(settings, "QUEUE_ANNOUNCE_WINDOW_MINUTES", 30))
    if name == "RESPONSE_GRACE_MINUTES":
        return int(getattr(settings, "QUEUE_RESPONSE_GRACE_MINUTES", 15))
    if name == "WORKING_WEEKDAYS":
        # دوشنبه=0 ... یکشنبه=6 | پیش‌فرض: همه‌روزه به‌جز جمعه(4)
        return tuple(getattr(settings, "QUEUE_WORKING_WEEKDAYS", (0, 1, 2, 3, 5, 6)))
    if name == "HOLIDAYS":
        return set(getattr(settings, "QUEUE_HOLIDAYS", []))
    if name == "OFFICE_LOCATION":
        # لینک لوکیشن یا مختصات مستقیم دفتر باربری
        location_input = getattr(settings, "OFFICE_LOCATION", "35.6997,51.3380")
        coords = extract_coordinates_from_url(location_input)
        if coords:
            return coords
        # اگر استخراج نشد، مقدار پیش‌فرض را برگردان
        return (35.6997, 51.3380)
    if name == "OFFICE_LAT":
        location = __getattr__("OFFICE_LOCATION")
        return float(location[0])
    if name == "OFFICE_LNG":
        location = __getattr__("OFFICE_LOCATION")
        return float(location[1])
    if name == "GEOFENCE_RADIUS_KM":
        return float(getattr(settings, "QUEUE_GEOFENCE_RADIUS_KM", 5.0))
    if name == "BASE_URL":
        return getattr(settings, "QUEUE_BASE_URL", "http://127.0.0.1:8000")
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
