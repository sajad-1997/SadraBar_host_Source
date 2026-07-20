import threading

from django.conf import settings
from django.db import models
from django.db import transaction
from django.db.models import Max
from django.utils import timezone
from django_jalali.db import models as jmodels
from persian_tools import digits

# تابع get_current_user از middleware خوانده می‌شود تا circular import نشود
# مطمئن شو middleware.py دارای set_current_user/get_current_user است و در MIDDLEWARE ثبت شده.
from .middleware import get_current_user  # اگر مسیر متفاوت است این خط را متناسب با پروژه تغییر بده


# -------------------------------
# BaseModel عمومی برای ذخیره کاربر ایجادکننده و ویرایش‌کننده
# -------------------------------
class UserTrackingModel(models.Model):
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_created"
    )
    created_by_role = models.CharField(max_length=50, blank=True, null=True)

    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_updated"
    )
    updated_by_role = models.CharField(max_length=50, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def _safe_get_role(self, user):
        """تلاش می‌کند نقش را با کمترین ریسک استخراج کند."""
        if not user:
            return None
        # اگر متد get_role_display وجود داشته باشد از آن استفاده کن
        get_role = getattr(user, "get_role_display", None)
        if callable(get_role):
            try:
                return get_role()
            except Exception:
                pass

        # اگر فیلد role یا role_name موجود بود استفاده کن
        for attr in ("role", "role_name"):
            if hasattr(user, attr):
                try:
                    return str(getattr(user, attr))
                except Exception:
                    pass

        return None

    def save(self, *args, **kwargs):
        user = get_current_user()
        if user and not self.pk:
            # رکورد جدید: created_by و created_by_role را ست کن
            self.created_by = user
            role = self._safe_get_role(user)
            if role:
                self.created_by_role = role

        if user:
            # در هر ذخیره (ایجاد یا به‌روزرسانی) updated_by را به‌روز کن
            self.updated_by = user
            role = self._safe_get_role(user)
            if role:
                self.updated_by_role = role

        super().save(*args, **kwargs)


class Customer(UserTrackingModel):
    name = models.CharField(max_length=50, blank=False, verbose_name="نام و نام خانوادگی فرستنده")
    national_id = models.CharField(max_length=50, unique=True, verbose_name="شناسه یا کد ملی", blank=True, null=True)
    postal = models.CharField(max_length=10, verbose_name="کد پستی", blank=True, null=True)
    phone = models.CharField(max_length=15, verbose_name="تلفن", blank=True, null=True)
    address = models.TextField(blank=False, verbose_name="آدرس")
    phone2 = models.TextField(verbose_name="تلفن دوم", blank=True, null=True)
    caption = models.TextField(verbose_name="توضیحات", blank=True, null=True)

    def __str__(self):
        return self.name


class Driver(UserTrackingModel):
    name = models.CharField(max_length=200, verbose_name="نام و نام خانوادگی راننده")
    national_id = models.CharField(max_length=50, unique=True, verbose_name="کد ملی راننده")
    father_name = models.CharField(max_length=50, blank=True, null=True, verbose_name="نام پدر")
    birth_date = jmodels.jDateField(blank=True, null=True, verbose_name="تاریخ تولد")
    residence = models.CharField(max_length=100, blank=True, null=True, verbose_name="شهر محل سکونت")
    certificate = models.CharField(max_length=50, unique=True, verbose_name="شماره گواهینامه")
    certificate_date = jmodels.jDateField(blank=True, null=True, verbose_name="تاریخ صدور گواهینامه")
    driver_smart_card = models.CharField(max_length=50, unique=True, blank=True, null=True,
                                         verbose_name="هوشمند راننده")
    phone = models.CharField(max_length=15, verbose_name="شماره تلفن راننده")
    phone2 = models.CharField(max_length=15, blank=True, null=True, verbose_name="شماره تلفن دوم")
    address = models.TextField(blank=True, null=True, verbose_name="آدرس محل سکونت")
    insurance_policy_number = models.CharField(max_length=50, blank=True, null=True,
                                               verbose_name="شماره بیمه نامه شخص ثالث")
    insurance_policy_expiry = models.CharField(max_length=50, blank=True, null=True,
                                               verbose_name="تاریخ انقضاء بیمه نامه شخص ثالث")

    def __str__(self):
        return self.name


class Vehicle(UserTrackingModel):
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, verbose_name="انتخاب راننده")
    type = models.CharField(
        max_length=50,
        verbose_name='نوع ناوگان',
        choices=[
            ('peykan', 'وانت پیکان'),
            ('neysan', 'وانت نیسان'),
            ('arisan', 'وانت آریسان'),
            ('zamyad', 'وانت زامیاد'),
            ('Bari 20T', 'باری چوبی ۱۷ تا ۲۰ تن'),
        ])
    # room_model = models.CharField(
    #     max_length=50,
    #     verbose_name='مدل اتاق ناوگان',
    #     choices=[
    #         ('Normal', 'معمولی'),
    #         ('flat_floor', 'کف صاف'),
    #         ('sofa_floor', 'کف مبلی'),
    #     ],
    #     default='Normal')
    # Animal_feed_license = models.CharField(
    #     max_length=6,
    #     null=True,
    #     blank=True,
    #     verbose_name='مجوز حمل خوراک دام',
    #     choices=[
    #         ('No', 'ندارد'),
    #         ('Yes', 'دارد'),
    #     ], default='No')
    # veterinary_code = models.CharField(max_length=7, blank=True, null=True, verbose_name="کد دامپزشکی")
    license_plate_two_digit = models.CharField(max_length=2, verbose_name="دو رقم پلاک")
    license_plate_alphabet = models.CharField(max_length=1, verbose_name="الفبای پلاک")
    license_plate_three_digit = models.CharField(max_length=3, verbose_name="سه رقم پلاک")
    license_plate_series = models.CharField(max_length=2, verbose_name="سری پلاک")
    vehicle_smart_card = models.CharField(max_length=50, unique=True, blank=True, null=True,
                                          verbose_name="هوشمند ناوگان")

    def __str__(self):
        return self.type


class Cargo(UserTrackingModel):
    name = models.CharField(max_length=50, verbose_name="نام محموله")
    weight = models.CharField(max_length=5, verbose_name="وزن(کیلوگرم)/حجم(لیتر)")
    package_type = models.CharField(max_length=10, blank=True, null=True, verbose_name="نوع بسته بندی")
    number_of_packaging = models.CharField(max_length=3, blank=True, null=True, verbose_name="تعداد بسته بندی")
    origin = models.CharField(max_length=50, verbose_name="مبدا بارگیری")
    destination = models.CharField(max_length=50, verbose_name="مقصد تخلیه")

    def __str__(self):
        return self.name


class Caption(UserTrackingModel):
    name = models.CharField(max_length=100, blank=True, null=True, verbose_name="عنوان")
    content = models.TextField(blank=True, null=True, verbose_name="توضیحات")

    def __str__(self):
        return self.content[:50]


class Bijak(UserTrackingModel):  # اکنون از UserTrackingModel ارث می‌برد
    tracking_code = models.CharField(max_length=15, unique=True, verbose_name="کد رهگیری")
    issuance_datetime = jmodels.jDateTimeField(verbose_name="تاریخ و ساعت صدور بارنامه")
    value = models.CharField(max_length=100, verbose_name="ارزش محموله")
    insurance = models.CharField(max_length=100, verbose_name="حق بیمه")
    loading_fee = models.CharField(max_length=100, blank=True, null=True, verbose_name="هزینه بارگیری")
    unloading_fee = models.CharField(max_length=100, blank=True, null=True, verbose_name="هزینه تخلیه")
    scale_fee = models.CharField(max_length=100, blank=True, null=True, verbose_name="هزینه باسکول")
    freight = models.CharField(max_length=100, verbose_name="مبلغ کرایه")
    total_fare = models.CharField(max_length=100, verbose_name="کل کرایه پرداختی در مقصد")

    sender = models.ForeignKey('Customer', on_delete=models.CASCADE, related_name='sender_bijaks')
    receiver = models.ForeignKey('Customer', on_delete=models.CASCADE, related_name='received_bijaks')
    driver = models.ForeignKey('Driver', on_delete=models.CASCADE, related_name='driver_bijaks')
    vehicle = models.ForeignKey('Vehicle', on_delete=models.CASCADE, related_name='vehicle_bijaks')
    cargo = models.ForeignKey('Cargo', on_delete=models.CASCADE, related_name='cargo_bijaks')
    # insurance_company = models.ForeignKey('insurance.InsuranceCompany', null=True, blank=True, on_delete=models.SET_NULL,
    #                                       default='بیمه ایران', related_name='insurance_bijaks')

    status = models.CharField(
        max_length=50,
        verbose_name='وضعیت بارنامه',
        choices=[
            ('draft', 'پیش‌نویس'),
            ('issued', 'صادر شده'),
            ('waiting_approval', 'در انتظار تأیید مدیر'),
            ('approved', 'تأیید شده'),
            ('rejected', 'رد شده'),
            ('sent', 'ارسال شده'),
            ('delivered', 'تحویل شده'),
        ],
        default='draft'
    )
    type = models.CharField(
        max_length=50,
        verbose_name='نوع بارنامه',
        choices=[
            ('Fare change', 'تغییر کرایه'),
            ('informal', 'سوری'),
            ('reprint', 'چاپ مجدد'),
            ('driver_request', 'به درخواست راننده'),
        ])

    default_description = 'هرگونه آب خوردگی و خیس شدن بار به مسئولیت راننده میباشد.'

    selected_caption = models.ForeignKey(
        'Caption', on_delete=models.SET_NULL, null=True, blank=True, related_name='caption_bijaks')
    custom_caption = models.TextField(blank=True, null=True)
    final_description = models.TextField(blank=True, null=True)

    _lock = threading.Lock()  # جلوگیری از برخورد در درخواست‌ها

    def issuance_date(self):
        return self.issuance_datetime.date()

    def issuance_time(self):
        return self.issuance_datetime.time()

    @property
    def num_in_words(self):
        if self.total_fare:
            try:
                value_str = str(self.total_fare).replace(",", "").replace(".", "")
                num = int(value_str)
                return digits.convert_to_word(num) + " ریال"
            except ValueError:
                return ""
        return ""

    def generate_tracking_code(self):
        """نسخه نهایی تولید کد رهگیری: YYMM + 5DIGIT"""

        today = timezone.now().date()
        yy = str(today.year % 100).zfill(2)
        mm = str(today.month).zfill(2)

        prefix = yy + mm  # مثال: 2411

        with transaction.atomic(), Bijak._lock:
            last_code = (
                Bijak.objects
                    .filter(tracking_code__startswith=prefix)
                    .aggregate(max_code=Max("tracking_code"))
                    .get("max_code")
            )

            if last_code:
                counter = int(last_code[-5:]) + 1
            else:
                counter = 1

            new_code = prefix + str(counter).zfill(5)
            return new_code

    def save(self, *args, **kwargs):
        parts = [self.default_description]
        if self.selected_caption:
            parts.append(self.selected_caption.content)
        if self.custom_caption:
            parts.append(self.custom_caption)
        self.final_description = " | ".join(parts)

        if not self.tracking_code:
            self.tracking_code = self.generate_tracking_code()

        if not self.issuance_date:
            self.issuance_date = timezone.now().date()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"بیجک {self.tracking_code} - {self.issuance_datetime}"


class BijakApprovalLog(models.Model):
    bijak = models.ForeignKey(Bijak, on_delete=models.CASCADE, related_name="approval_logs")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=20, choices=[
        ("sent_for_approval", "ارسال برای تایید"),
        ("approved", "تایید شد"),
        ("rejected", "رد شد"),
    ])
    description = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "تاریخچه تایید بیجک"
        verbose_name_plural = "تاریخچه تایید بیجک ها"

    def __str__(self):
        return f"{self.bijak.tracking_code} - {self.action}"
