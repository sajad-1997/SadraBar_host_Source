from django.db import models
from django.conf import settings


class Province(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="نام استان")
    slug = models.SlugField(max_length=50, unique=True, allow_unicode=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "استان"
        verbose_name_plural = "استان‌ها"
        ordering = ['name']


class City(models.Model):
    province = models.ForeignKey(Province, on_delete=models.CASCADE, related_name='cities', verbose_name="استان")
    name = models.CharField(max_length=50, verbose_name="نام شهر")
    slug = models.SlugField(max_length=50, allow_unicode=True)

    def __str__(self):
        return f"{self.province.name} - {self.name}"

    class Meta:
        verbose_name = "شهر"
        verbose_name_plural = "شهرها"
        ordering = ['province', 'name']
        unique_together = ['province', 'name']


class Cargo(models.Model):
    name = models.CharField(max_length=50, verbose_name="نام محموله", db_index=True)
    weight = models.IntegerField(verbose_name="وزن/حجم")
    weight_2 = models.IntegerField(default=0, verbose_name="وزن/حجم دوم")
    package_type = models.CharField(max_length=10, blank=True, null=True, verbose_name="نوع بسته بندی")
    number_of_packaging = models.IntegerField(blank=True, null=True, verbose_name="تعداد بسته بندی")
    origin = models.ForeignKey(City, on_delete=models.PROTECT, related_name='cargo_origins', verbose_name="مبدأ بارگیری", db_index=True)
    destination = models.ForeignKey(City, on_delete=models.PROTECT, related_name='cargo_destinations', verbose_name="مقصد تخلیه", db_index=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cargo_created",
        db_index=True
    )
    created_by_role = models.CharField(max_length=50, blank=True, null=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cargo_updated",
        db_index=True
    )
    updated_by_role = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'cargo'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['origin']),
            models.Index(fields=['destination']),
        ]
