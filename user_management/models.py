from django.db import models
from django.conf import settings
from django.utils import timezone


class DriverBlock(models.Model):
    """
    مدل برای مسدود کردن دسترسی رانندگان به سیستم
    """
    driver = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'driver'},
        related_name='driver_block',
        verbose_name='راننده'
    )
    is_blocked = models.BooleanField(default=False, verbose_name='مسدود شده')
    block_reason = models.TextField(blank=True, null=True, verbose_name='دلیل مسدود شدن')
    blocked_at = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ مسدود شدن')
    blocked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='blocked_drivers',
        verbose_name='مسدود شده توسط'
    )
    unblocked_at = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ رفع مسدودی')
    unblocked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='unblocked_drivers',
        verbose_name='رفع مسدودی توسط'
    )
    notes = models.TextField(blank=True, null=True, verbose_name='یادداشت‌ها')

    def block(self, blocked_by_user, reason=''):
        """مسدود کردن راننده"""
        self.is_blocked = True
        self.block_reason = reason
        self.blocked_at = timezone.now()
        self.blocked_by = blocked_by_user
        self.unblocked_at = None
        self.unblocked_by = None
        self.save()

    def unblock(self, unblocked_by_user):
        """رفع مسدودی راننده"""
        self.is_blocked = False
        self.unblocked_at = timezone.now()
        self.unblocked_by = unblocked_by_user
        self.save()

    def __str__(self):
        status = 'مسدود' if self.is_blocked else 'فعال'
        return f"{self.driver.username} - {status}"

    class Meta:
        verbose_name = 'مسدودی راننده'
        verbose_name_plural = 'مسدودی رانندگان'
