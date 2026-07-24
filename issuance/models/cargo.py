from django.db import models

from .base import UserTrackingModel


class Cargo(UserTrackingModel):
    name = models.CharField(max_length=50, verbose_name="نام محموله")
    weight = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="وزن/حجم")
    package_type = models.CharField(max_length=10, blank=True, null=True, verbose_name="نوع بسته بندی")
    number_of_packaging = models.IntegerField(blank=True, null=True, verbose_name="تعداد بسته بندی")
    origin = models.CharField(max_length=50, verbose_name="مبدأ بارگیری")
    destination = models.CharField(max_length=50, verbose_name="مقصد تخلیه")

    def __str__(self):
        return self.name
