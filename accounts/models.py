# accounts/models.py
import random

from django.contrib.auth.models import AbstractUser
from django.db import models, transaction, IntegrityError

# حداکثر تلاش برای تولید کد کاربر یکتا در شرایط همزمانی
MAX_USER_CODE_ATTEMPTS = 25


class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'مدیر کل سیستم'),
        ('manager', 'مدیریت'),
        ('employee', 'کارمند'),
        ('driver', 'راننده'),
        ('customer', 'مشتری'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='employee')
    user_code = models.CharField(max_length=4, unique=True, null=True, blank=True, verbose_name="کد کاربر")

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    def generate_user_code(self):
        """تولید کد کاربر ۴ رقمی یکتا"""
        # ابتدا تلاش تصادفی (سریع)
        for _ in range(MAX_USER_CODE_ATTEMPTS):
            code = str(random.randint(1000, 9999))
            if not User.objects.filter(user_code=code).exists():
                return code

        # فال‌بک: پیدا کردن اولین کد خالی به صورت ترتیبی
        # (وقتی فضای کدها تقریباً پر شده یا تصادفی مدام تکرار می‌شود)
        used_codes = set(
            User.objects.exclude(user_code__isnull=True)
            .values_list('user_code', flat=True)
        )
        for number in range(1000, 10000):
            code = str(number)
            if code not in used_codes:
                return code

        raise RuntimeError("ظرفیت کدهای کاربر ۴ رقمی تکمیل شده است.")

    def save(self, *args, **kwargs):
        """ذخیره کاربر با اختصاص ایمن کد کاربر در شرایط همزمانی.

        دو فرآیند ممکن است همزمان کاربر بسازند و همان کد تصادفی را انتخاب کنند.
        با تراکنش atomic + retry روی خطای یکتایی user_code، از این تداخل جلوگیری می‌شود.
        """
        needs_code = not self.user_code and self.role in ['admin', 'manager', 'employee']

        if not needs_code:
            super().save(*args, **kwargs)
            return

        for attempt in range(MAX_USER_CODE_ATTEMPTS):
            self.user_code = self.generate_user_code()
            try:
                with transaction.atomic():
                    super().save(*args, **kwargs)
                return  # ذخیره موفق
            except IntegrityError as exc:
                # اگر تداخل مربوط به فیلد دیگری است (مثل username) دوباره تلاش نکن
                if 'user_code' not in str(exc):
                    raise
                # کد تکراری توسط فرآیند دیگر رزرو شده؛ کد جدید بگیر و دوباره تلاش کن
                self.user_code = None

        raise RuntimeError(
            "تولید کد کاربر یکتا پس از چندبار تلاش ناموفق بود. لطفاً دوباره تلاش کنید."
        )

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

    # مجوز چاپ بارنامه با مهر و امضای دیجیتال
    # (مدیریت و مدیر کل همیشه مجاز هستند؛ این مجوز برای نقش کارمند است)
    can_use_digital_stamp = models.BooleanField(
        default=False,
        verbose_name="اجازه چاپ بارنامه با مهر و امضای دیجیتال"
    )

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
