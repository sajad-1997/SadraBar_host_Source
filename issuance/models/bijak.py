import threading

from django.conf import settings
from django.db import models, transaction
from django.db.models import Max
from django.utils import timezone
from django_jalali.db import models as jmodels
# from persian_tools import digits

from .base import UserTrackingModel
from .caption import Caption
from .cargo import Cargo
from .customer import Customer
from .driver import Driver
from .vehicle import Vehicle


class Bijak(UserTrackingModel):
    # =========================
    # اطلاعات پایه بارنامه
    # =========================
    tracking_code = models.CharField(max_length=15, unique=True)
    issuance_datetime = jmodels.jDateTimeField(verbose_name="تاریخ و ساعت صدور بارنامه")
    value = models.CharField(max_length=100, verbose_name="ارزش محموله")
    insurance = models.CharField(max_length=100, verbose_name="مبلغ بیمه")
    loading_fee = models.CharField(max_length=100, blank=True, null=True, verbose_name="هزینه بارگیری")
    unloading_fee = models.CharField(max_length=100, blank=True, null=True, verbose_name="هزینه تخلیه")
    scale_fee = models.CharField(max_length=100, blank=True, null=True, verbose_name="هزینه باسکول")
    freight = models.CharField(max_length=100, verbose_name="کل کرایه")
    total_fare = models.CharField(max_length=100, verbose_name="کرایه پرداختی در مقصد")

    sender = models.ForeignKey('Customer', on_delete=models.CASCADE, related_name='sender_bijaks')
    receiver = models.ForeignKey('Customer', on_delete=models.CASCADE, related_name='received_bijaks')
    driver = models.ForeignKey('Driver', on_delete=models.CASCADE, related_name='driver_bijaks')
    vehicle = models.ForeignKey('Vehicle', on_delete=models.CASCADE, related_name='vehicle_bijaks')
    cargo = models.ForeignKey('Cargo', on_delete=models.CASCADE, related_name='cargo_bijaks')
    # insurance_company = models.ForeignKey('insurance.InsuranceCompany', null=True, blank=True, on_delete=models.SET_NULL,
    #                                       default='بیمه ایران', related_name='insurance_bijaks')

    # =========================
    # وضعیت اجرایی بارنامه
    # =========================
    STATUS_CHOICES = [
        ('draft', 'پیش‌نویس'),
        ('issued', 'صادر شده'),
        ('sent', 'ارسال شده'),
        ('delivered', 'تحویل شده'),
    ]

    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='draft'
    )

    # =========================
    # وضعیت نهایی بارنامه
    # =========================
    TYPE_CHOICES = [
        ('draft', 'پیش‌نویس'),
        ('sent', 'ارسال شده'),
        ('Sent-Customer Version', 'ارسال شده-نسخه مشتری'),
        ('Sent-Driver Version', 'ارسال شده-نسخه راننده'),
        ('delivered', 'تحویل شده'),
        ('Delivered-Customer Version', 'تحویل شده-نسخه مشتری'),
        ('Delivered-Driver Version', 'تحویل شده-نسخه راننده'),
        ('canceled', 'لغو شده'),
        ('inactive', 'تکراری-غیر فعال'),
    ]

    type = models.CharField(
        max_length=50,
        choices=TYPE_CHOICES,
        default='sent'
    )
    
    # =========================
    # وضعیت تأیید مدیریتی (جدید)
    # =========================
    APPROVAL_STATUS_CHOICES = [
        ('pending', 'در انتظار تأیید'),
        ('approved', 'تأیید شده'),
        ('rejected', 'رد شده'),
    ]

    approval_status = models.CharField(
        max_length=20,
        choices=APPROVAL_STATUS_CHOICES,
        default='pending'
    )

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='approved_bijaks'
    )

    rejected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='rejected_bijaks'
    )

    reject_reason = models.TextField(null=True, blank=True)

    approved_at = models.DateTimeField(null=True, blank=True)

    # =========================
    # توضیحات
    # =========================
    selected_caption = models.ForeignKey(
        Caption, on_delete=models.SET_NULL, null=True, blank=True
    )
    custom_caption = models.TextField(blank=True, null=True)
    final_description = models.TextField(blank=True, null=True)

    default_description = 'هرگونه آب خوردگی و خیس شدن بار به مسئولیت راننده میباشد.'

    _lock = threading.Lock()

    # =========================
    # پراپرتی‌های کمکی
    # =========================
    @property
    def num_in_words(self):
        try:
            return digits.convert_to_word(int(self.total_fare.replace(',', ''))) + " ریال"
        except Exception:
            return ""

    @property
    def is_approved(self):
        return self.approval_status == 'approved'

    @property
    def is_rejected(self):
        return self.approval_status == 'rejected'

    @property
    def can_print(self):
        return self.is_approved and self.status == 'issued'

    # =========================
    # منطق تولید کد رهگیری
    # =========================
    def generate_tracking_code(self):
        today = timezone.now().date()
        prefix = f"{today.year % 100:02d}{today.month:02d}"

        with transaction.atomic(), Bijak._lock:
            last = Bijak.objects.filter(
                tracking_code__startswith=prefix
            ).aggregate(
                Max("tracking_code")
            )["tracking_code__max"]

            counter = int(last[-5:]) + 1 if last else 1
            return prefix + str(counter).zfill(5)

    # =========================
    # ذخیره
    # =========================
    def save(self, *args, **kwargs):
        parts = [self.default_description]

        if self.selected_caption:
            parts.append(self.selected_caption.content)


        self.final_description = " | ".join(parts)

        if not self.tracking_code:
            self.tracking_code = self.generate_tracking_code()

        if not self.issuance_datetime:
            self.issuance_datetime = timezone.now()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"بیجک {self.tracking_code} - {self.issuance_datetime}"
