from celery import shared_task

from . import services
from .utils import tehran_now


@shared_task
def send_daily_announcements():
    """هر روز کاری ساعت ۱۱:۰۰ -> ارسال اعلان دو گزینه‌ای."""
    now = tehran_now()
    if not services.is_working_day(now.date()):
        return 0
    return services.send_announcements(now)


@shared_task
def purge_queue_nonresponders():
    """هر روز کاری ساعت ۱۱:۱۵ -> حذف عدم‌پاسخ‌دهنده‌ها (۱۵ دقیقه مهلت)."""
    now = tehran_now()
    if not services.is_working_day(now.date()):
        return 0
    return services.purge_nonresponders(now)
