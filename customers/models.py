from django.db import models
from django.conf import settings


class Customer(models.Model):
    name = models.CharField(max_length=50, verbose_name="نام و نام خانوادگی فرستنده", db_index=True)
    national_id = models.CharField(max_length=50, unique=True, blank=True, null=True, db_index=True)
    postal = models.CharField(max_length=10, blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True, db_index=True)
    address = models.TextField(verbose_name="آدرس")
    phone2 = models.TextField(blank=True, null=True)
    caption = models.TextField(blank=True, null=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="customer_created",
        db_index=True
    )
    created_by_role = models.CharField(max_length=50, blank=True, null=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="customer_updated",
        db_index=True
    )
    updated_by_role = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'customer'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['national_id']),
            models.Index(fields=['phone']),
        ]


class CustomerAddress(models.Model):
    """مدل برای ذخیره آدرس‌های متعدد هر مشتری"""
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='addresses',
        db_index=True
    )
    postal = models.CharField(max_length=10, blank=True, null=True, verbose_name="کد پستی")
    phone = models.CharField(max_length=15, blank=True, null=True, verbose_name="شماره تلفن")
    address = models.TextField(verbose_name="آدرس")
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="customer_address_created",
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return f"{self.customer.name} - {self.address[:30]}"

    class Meta:
        db_table = 'customer_address'
        indexes = [
            models.Index(fields=['customer']),
        ]
