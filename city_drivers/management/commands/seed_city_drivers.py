from decimal import Decimal

from django.core.management.base import BaseCommand

from city_drivers.models import RateCard, UrbanService


class Command(BaseCommand):
    help = 'ایجاد داده‌های اولیه ماژول رانندگان شهری (idempotent)'

    def handle(self, *args, **options):
        services = [
            ('مسافری شهری', Decimal('10.00'), 20000, 8000),
            ('حمل وسیله درون‌شهری', Decimal('10.00'), 30000, 10000),
            ('ارسال بسته', Decimal('12.00'), 25000, 9000),
        ]
        for title, percent, base, per_km in services:
            service, created = UrbanService.objects.get_or_create(
                title=title,
                defaults={
                    'commission_percent': percent,
                    'base_fare': base,
                    'per_km_fare': per_km,
                })
            if created:
                self.stdout.write(self.style.SUCCESS(f'سرویس «{title}» ایجاد شد.'))

        if not RateCard.objects.exists():
            service = UrbanService.objects.first()
            RateCard.objects.create(
                title='نرخ‌نامه پیش‌فرض سواری',
                service=service,
                vehicle_type='sedan',
                base_fare=20000,
                per_km_fare=8000,
                minimum_fare=30000,
                commission_percent=Decimal('10.00'),
                created_by=None,
            )
            self.stdout.write(self.style.SUCCESS('نرخ‌نامه پیش‌فرض ایجاد شد.'))

        self.stdout.write(self.style.SUCCESS('داده‌های اولیه ماژول رانندگان شهری آماده است.'))
