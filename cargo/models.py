from django.db import models
from django.conf import settings


class Cargo(models.Model):
    name = models.CharField(max_length=50, verbose_name="نام محموله", db_index=True)
    weight = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="وزن/حجم")
    package_type = models.CharField(max_length=10, blank=True, null=True, verbose_name="نوع بسته بندی")
    number_of_packaging = models.IntegerField(blank=True, null=True, verbose_name="تعداد بسته بندی")
    origin = models.CharField(max_length=50, verbose_name="مبدأ بارگیری", db_index=True)
    destination = models.CharField(max_length=50, verbose_name="مقصد تخلیه", db_index=True)

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
        db_table = 'cargo_cargo'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['origin']),
            models.Index(fields=['destination']),
        ]
