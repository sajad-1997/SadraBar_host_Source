# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'مدیر کل سیستم'),
        ('manager', 'مدیریت'),
        ('staff', 'کارمند'),
        ('driver', 'راننده'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='staff')

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    # توابع کمکی برای راحتی در سطح دسترسی
    def is_admin(self):
        return self.role == 'admin'

    def is_manager(self):
        return self.role == 'manager'

    def is_staff_role(self):
        return self.role == 'staff'


class RolePermission(models.Model):
    ROLE_CHOICES = (
        ('manager', 'مدیریت'),
        ('staff', 'کارمند'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, unique=True)
    can_access_dashboard = models.BooleanField(default=False, verbose_name="دسترسی به داشبورد اصلی")
    can_manage_shipments = models.BooleanField(default=False, verbose_name="دسترسی به مدیریت بارنامه‌ها")
    can_issuance_shipments = models.BooleanField(default=False, verbose_name="دسترسی به صدور بارنامه‌ها")
    can_view_reports = models.BooleanField(default=False, verbose_name="دسترسی به گزارش‌ها")
    can_manage_users = models.BooleanField(default=False, verbose_name="دسترسی به مدیریت کاربران")
    can_manage_customers = models.BooleanField(default=False, verbose_name="دسترسی به لیست مشتریان")
    can_manage_drivers = models.BooleanField(default=False, verbose_name="دسترسی به لیست رانندگان")

    def __str__(self):
        return f"مجوزهای نقش {self.get_role_display()}"
