from django.core.management.base import BaseCommand

from driver_queue import services
from driver_queue.utils import tehran_now


class Command(BaseCommand):
    help = "حذف خودکار رانندگانی که به اعلان پاسخ نداده‌اند (پس از ۱۵ دقیقه)"

    def handle(self, *args, **options):
        if not services.is_working_day(tehran_now().date()):
            self.stdout.write(self.style.WARNING("امروز روز کاری نیست."))
            return
        count = services.purge_nonresponders()
        self.stdout.write(self.style.SUCCESS(f"{count} راننده از صف حذف شد."))
