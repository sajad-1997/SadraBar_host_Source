from django.conf import settings
from django.db import models

from .bijak import Bijak


class BijakFinalStatusLog(models.Model):
    """
    لاگ تغییر وضعیت نهایی بارنامه
    """
    bijak = models.ForeignKey(
        Bijak,
        on_delete=models.CASCADE,
        related_name='final_status_logs',
        verbose_name='بارنامه'
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='انجام‌دهنده'
    )

    old_status = models.CharField(
        max_length=20,
        verbose_name='وضعیت قبلی'
    )

    new_status = models.CharField(
        max_length=20,
        verbose_name='وضعیت جدید'
    )

    note = models.TextField(
        null=True,
        blank=True,
        verbose_name='توضیح'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='زمان تغییر وضعیت'
    )

    class Meta:
        verbose_name = 'تاریخچه وضعیت نهایی بارنامه'
        verbose_name_plural = 'تاریخچه وضعیت نهایی بارنامه‌ها'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.bijak.tracking_code} - {self.old_status} → {self.new_status}"
