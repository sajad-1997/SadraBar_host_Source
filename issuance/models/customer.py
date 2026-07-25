from django.db import models

from .base import UserTrackingModel


class Customer(UserTrackingModel):
    name = models.CharField(max_length=50, verbose_name="نام و نام خانوادگی فرستنده", db_index=True)
    national_id = models.CharField(max_length=50, unique=True, blank=True, null=True, db_index=True)
    postal = models.CharField(max_length=10, blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True, db_index=True)
    address = models.TextField(verbose_name="آدرس")
    phone2 = models.TextField(blank=True, null=True)
    caption = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name
