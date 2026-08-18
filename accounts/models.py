# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'مدیر کل سیستم'),
        ('manager', 'مدیریت'),
        ('employee', 'کارمند'),
        ('driver', 'راننده'),
        ('customer', 'مشتری'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='employee')

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    # توابع کمکی برای راحتی در سطح دسترسی
    def is_admin(self):
        return self.role == 'admin'

    def is_manager(self):
        return self.role == 'manager'

    def is_employee(self):
        return self.role == 'employee'

    def is_driver(self):
        return self.role == 'driver'

    def is_customer(self):
        return self.role == 'customer'


class RolePermission(models.Model):
    ROLE_CHOICES = (
        ('admin', 'مدیر کل سیستم'),
        ('manager', 'مدیریت'),
        ('employee', 'کارمند'),
        ('driver', 'راننده'),
        ('customer', 'مشتری'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, unique=True)
    can_access_dashboard = models.BooleanField(default=False, verbose_name="دسترسی به داشبورد اصلی")
    can_manage_shipments = models.BooleanField(default=False, verbose_name="دسترسی به مدیریت بارنامه‌ها")
    can_issuance_shipments = models.BooleanField(default=False, verbose_name="دسترسی به صدور بارنامه‌ها")
    can_view_reports = models.BooleanField(default=False, verbose_name="دسترسی به گزارش‌ها")
    can_manage_users = models.BooleanField(default=False, verbose_name="دسترسی به مدیریت کاربران")
    can_manage_customers = models.BooleanField(default=False, verbose_name="دسترسی به لیست مشتریان")
    can_manage_drivers = models.BooleanField(default=False, verbose_name="دسترسی به لیست رانندگان")
    
    # مجوزهای پیامک و تایید دو مرحله‌ای
    can_send_sms_verification = models.BooleanField(default=False, verbose_name="دسترسی به ارسال پیامک تایید")
    can_verify_sms_code = models.BooleanField(default=False, verbose_name="دسترسی به تایید کد پیامکی")
    can_manage_otp_settings = models.BooleanField(default=False, verbose_name="دسترسی به تنظیمات OTP")
    
    # مجوزهای ماژول نوبت‌دهی رانندگان
    can_access_driver_queue = models.BooleanField(default=False, verbose_name="دسترسی به پنل نوبت‌دهی رانندگان")
    can_manage_queue_settings = models.BooleanField(default=False, verbose_name="دسترسی به تنظیمات نوبت‌دهی")
    can_approve_queue_staff = models.BooleanField(default=False, verbose_name="دسترسی به تایید کارکنان نوبت‌دهی")
    can_view_queue_reports = models.BooleanField(default=False, verbose_name="دسترسی به گزارش‌های نوبت‌دهی")
    can_manage_queue_announcements = models.BooleanField(default=False, verbose_name="دسترسی به مدیریت اعلان‌های نوبت‌دهی")
    can_override_queue_rules = models.BooleanField(default=False, verbose_name="دسترسی به نادیده گرفتن قوانین نوبت‌دهی")

    def __str__(self):
        return f"مجوزهای نقش {self.get_role_display()}"
