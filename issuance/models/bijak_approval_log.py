from django.conf import settings
from django.db import models

from .bijak import Bijak


class BijakApprovalLog(models.Model):
    ACTION_CHOICES = [
        ('approved', 'تأیید شده'),
        ('rejected', 'رد شده'),
    ]

    bijak = models.ForeignKey(
        Bijak,
        on_delete=models.CASCADE,
        related_name='approval_logs',
        verbose_name='بارنامه'
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='انجام‌دهنده'
    )

    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        verbose_name='عملیات'
    )

    reason = models.TextField(
        null=True,
        blank=True,
        verbose_name='توضیح'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='زمان'
    )

    class Meta:
        verbose_name = 'تاریخچه تأیید بارنامه'
        verbose_name_plural = 'تاریخچه تأیید بارنامه‌ها'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.bijak.tracking_code} - {self.get_action_display()}"
