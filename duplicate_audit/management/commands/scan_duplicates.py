from django.core.management.base import BaseCommand

from duplicate_audit.services.scan_service import scan_duplicates


class Command(BaseCommand):
    help = 'اسکن بارنامه های تکراری و ایجاد Cluster و Snapshot'

    def handle(self, *args, **options):
        clusters = scan_duplicates()
        self.stdout.write(self.style.SUCCESS(f'{len(clusters)} Cluster ساخته شد!'))
