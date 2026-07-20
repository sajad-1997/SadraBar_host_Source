from django.db import models
from django_jalali.db import models as jmodels

from .base import UserTrackingModel


class Driver(UserTrackingModel):
    name = models.CharField(max_length=200, verbose_name="نام و نام خانوادگی")
    national_id = models.CharField(max_length=50, unique=True, verbose_name="کد ملی")
    father_name = models.CharField(max_length=50, blank=True, null=True, verbose_name="نام پدر")
    birth_date = jmodels.jDateField(blank=True, null=True, verbose_name="تاریخ تولد")
    residence = models.CharField(max_length=100, blank=True, null=True, verbose_name="شهر سکونت")
    certificate = models.CharField(max_length=50, unique=True, verbose_name="شماره گواهینامه")
    certificate_date = jmodels.jDateField(blank=True, null=True, verbose_name="تاریخ صدور گواهینامه")
    driver_smart_card = models.CharField(max_length=50, unique=True, blank=True, null=True, verbose_name="شماره هوشمند راننده")
    phone = models.CharField(max_length=15, verbose_name="شماره تلفن راننده")
    phone2 = models.CharField(max_length=15, blank=True, null=True, verbose_name="شماره تلفن دوم")
    address = models.TextField(blank=True, null=True, verbose_name="آدرس")
    insurance_policy_number = models.CharField(max_length=50, blank=True, null=True, verbose_name="شماره بیمه نامه")
    insurance_policy_expiry = jmodels.jDateField(blank=True, null=True, verbose_name="تاریخ اعتبار بیمه نامه")

    def __str__(self):
        return self.name
