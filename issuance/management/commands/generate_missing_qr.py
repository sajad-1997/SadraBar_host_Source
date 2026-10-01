# issuance/management/commands/generate_missing_qr.py

import os
import qrcode
from PIL import Image
from django.core.management.base import BaseCommand
from django.conf import settings
from django.urls import reverse
from issuance.models import Bijak


class Command(BaseCommand):
    help = 'Generate missing QR codes for all Bijaks based on tracking_code'

    def handle(self, *args, **options):
        qr_dir = os.path.join(settings.MEDIA_ROOT, 'qr')
        os.makedirs(qr_dir, exist_ok=True)

        bijaks = Bijak.objects.filter(tracking_code__isnull=False)
        total = bijaks.count()
        self.stdout.write(f"Found {total} Bijaks with tracking code")

        for bijak in bijaks:
            qr_filename = f"{bijak.tracking_code}.png"
            file_path = os.path.join(qr_dir, qr_filename)

            if os.path.exists(file_path):
                self.stdout.write(f"QR already exists for {bijak.tracking_code}")
                continue

            # تولید URL چاپ بارنامه
            print_url = reverse('issuance:crud:print', args=[bijak.pk])
            absolute_url = f"{getattr(settings, 'SITE_URL', 'http://localhost')}{print_url}"

            # تولید QR
            qr = qrcode.QRCode(
                version=2,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=4
            )
            qr.add_data(absolute_url)
            qr.make(fit=True)

            img_qr = qr.make_image(fill_color="black", back_color="white").convert('RGB')

            # ذخیره فایل
            img_qr.save(file_path)
            self.stdout.write(f"QR generated for {bijak.tracking_code}")

        self.stdout.write(self.style.SUCCESS("All missing QR codes generated successfully!"))
