from django.core.management.base import BaseCommand

from driver_queue import services
from driver_queue.utils import tehran_now


class Command(BaseCommand):
    help = "ارسال اعلان اعلام وضعیت برای رانندگان حاضر در صف امروز"

    def handle(self, *args, **options):
        if not services.is_working_day(tehran_now().date()):
            self.stdout.write(self.style.WARNING("امروز روز کاری نیست."))
            return
        count = services.send_announcements()
        self.stdout.write(self.style.SUCCESS(f"{count} اعلان ارسال شد."))
