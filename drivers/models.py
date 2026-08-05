from django.db import models
from django_jalali.db import models as jmodels
from django.conf import settings


class Driver(models.Model):
    name = models.CharField(max_length=200, verbose_name="نام و نام خانوادگی", db_index=True)
    national_id = models.CharField(max_length=50, unique=True, verbose_name="کد ملی", db_index=True)
    father_name = models.CharField(max_length=50, blank=True, null=True, verbose_name="نام پدر")
    birth_date = jmodels.jDateField(blank=True, null=True, verbose_name="تاریخ تولد")
    residence = models.CharField(max_length=100, blank=True, null=True, verbose_name="شهر سکونت")
    certificate = models.CharField(max_length=50, unique=True, verbose_name="شماره گواهینامه", db_index=True)
    certificate_date = jmodels.jDateField(blank=True, null=True, verbose_name="تاریخ صدور گواهینامه")
    driver_smart_card = models.CharField(max_length=50, unique=True, blank=True, null=True, verbose_name="شماره هوشمند راننده", db_index=True)
    phone = models.CharField(max_length=15, verbose_name="شماره تلفن راننده", db_index=True)
    phone2 = models.CharField(max_length=15, blank=True, null=True, verbose_name="شماره تلفن دوم")
    phone3 = models.CharField(max_length=15, blank=True, null=True, verbose_name="شماره تلفن سوم")
    address = models.TextField(blank=True, null=True, verbose_name="آدرس")

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="driver_created",
        db_index=True
    )
    created_by_role = models.CharField(max_length=50, blank=True, null=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="driver_updated",
        db_index=True
    )
    updated_by_role = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'driver'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['national_id']),
            models.Index(fields=['certificate']),
            models.Index(fields=['phone']),
        ]
