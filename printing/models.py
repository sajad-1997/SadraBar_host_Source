from django.db import models
from django.conf import settings  # ← اضافه شود
from django.utils import timezone
from issuance.models import Bijak


class WaybillPrintOTP(models.Model):
    """
    جدول ذخیره کدهای تأیید و سوابق چاپ برای هر بارنامه (Bijak)
    """
    bijak = models.OneToOneField(
        Bijak,
        on_delete=models.CASCADE,
        related_name='print_otp',
        verbose_name='بارنامه'
    )
    otp_code = models.CharField(max_length=6, blank=True, null=True, verbose_name='کد تأیید')
    print_count = models.PositiveIntegerField(default=0, verbose_name='تعداد دفعات چاپ')
    last_print_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # ← اصلاح شده (به جای 'auth.User')
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='آخرین چاپ توسط'
    )
    last_print_time = models.DateTimeField(null=True, blank=True, verbose_name='زمان آخرین چاپ')
    otp_created_at = models.DateTimeField(null=True, blank=True, verbose_name='زمان تولید کد')
    is_verified = models.BooleanField(default=False, verbose_name='کد تأیید شده؟')

    class Meta:
        verbose_name = 'ثبت چاپ بارنامه'
        verbose_name_plural = 'ثبت چاپ بارنامه‌ها'

    def is_otp_expired(self):
        """بررسی انقضای کد (۲ دقیقه)"""
        if not self.otp_created_at:
            return True
        return (timezone.now() - self.otp_created_at).seconds > 120

    def __str__(self):
        waybill_identifier = getattr(self.bijak, 'waybill_number', str(self.bijak.id))
        return f"{waybill_identifier} - چاپ {self.print_count} بار"
