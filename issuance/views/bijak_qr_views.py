# issuance/views/bijak_qr_views.py

import os
import qrcode
from PIL import Image
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.http import FileResponse
from django.urls import reverse
from issuance.models import Bijak

def bijak_qr(request, pk):
    """
    ویو تولید QR کد بارنامه بر اساس کد رهگیری.
    - اگر QR وجود نداشته باشد، آن را تولید می‌کند.
    - اگر موجود باشد، مستقیماً فایل تصویر را بازمی‌گرداند.
    """
    bijak = get_object_or_404(Bijak, pk=pk)

    # استفاده از کد رهگیری برای نام فایل QR
    if not bijak.tracking_code:
        raise ValueError("بارنامه هنوز کد رهگیری ندارد!")

    qr_filename = f"{bijak.tracking_code}.png"
    qr_dir = os.path.join(settings.MEDIA_ROOT, 'qr')
    os.makedirs(qr_dir, exist_ok=True)
    file_path = os.path.join(qr_dir, qr_filename)

    # اگر فایل QR وجود ندارد، تولید شود
    if not os.path.exists(file_path):
        # URL چاپ بارنامه بر اساس PK
        print_url = reverse('issuance:crud:print', args=[pk])
        absolute_url = request.build_absolute_uri(print_url)

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

        # ذخیره در مسیر media/qr
        img_qr.save(file_path)

    # فایل QR را مستقیم برگردان
    return FileResponse(open(file_path, 'rb'), content_type='image/png')
