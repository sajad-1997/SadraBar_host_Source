from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.db import models

import jdatetime
from django_jalali.db import models as jmodels

from drivers.models import Driver


# انواع خودرو / سرویس شهری
VEHICLE_TYPE_CHOICES = (
    ('sedan', 'سواری'),
    ('vanet', 'ون'),
    ('pickup', 'وانت'),
    ('nissan', 'نیسان'),
    ('minibus', 'مینی‌بوس'),
    ('other', 'سایر'),
)


# =========================================================
# انواع سرویس شهری
# =========================================================
class UrbanService(models.Model):
    """انواع سرویس‌های شهری (مسافری، حمل وسیله، خرید و ...)"""

    title = models.CharField(max_length=100, unique=True, verbose_name='عنوان سرویس')
    commission_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('10.00'),
        verbose_name='درصد کمیسیون آژانس')
    base_fare = models.DecimalField(
        max_digits=15, decimal_places=0, default=0,
        verbose_name='کرایه پایه (تومان)')
    per_km_fare = models.DecimalField(
        max_digits=15, decimal_places=0, default=0,
        verbose_name='کرایه هر کیلومتر (تومان)')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    sort_order = models.PositiveIntegerField(default=0, verbose_name='ترتیب نمایش')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'سرویس شهری'
        verbose_name_plural = 'سرویس‌های شهری'
        ordering = ('sort_order', 'id')

    def __str__(self):
        return self.title


# =========================================================
# نرخ‌نامه و محاسبه کرایه
# =========================================================
class RateCard(models.Model):
    """نرخ‌نامه کرایه سرویس‌های شهری"""

    title = models.CharField(max_length=150, verbose_name='عنوان نرخ‌نامه')
    service = models.ForeignKey(
        UrbanService, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='rate_cards', verbose_name='سرویس مرتبط')
    vehicle_type = models.CharField(
        max_length=20, choices=VEHICLE_TYPE_CHOICES, default='sedan',
        verbose_name='نوع خودرو')
    base_fare = models.DecimalField(
        max_digits=15, decimal_places=0, default=0,
        verbose_name='کرایه پایه (تومان)')
    per_km_fare = models.DecimalField(
        max_digits=15, decimal_places=0, default=0,
        verbose_name='کرایه هر کیلومتر (تومان)')
    minimum_fare = models.DecimalField(
        max_digits=15, decimal_places=0, default=0,
        verbose_name='حداقل کرایه (تومان)')
    commission_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('10.00'),
        verbose_name='درصد کمیسیون آژانس')
    description = models.TextField(blank=True, null=True, verbose_name='توضیحات')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='urban_rate_cards_created',
        verbose_name='ایجاد کننده')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'نرخ‌نامه'
        verbose_name_plural = 'نرخ‌نامه‌ها'
        ordering = ('-is_active', 'title')

    def __str__(self):
        return self.title

    # ---------- محاسبات کرایه ----------
    def calculate_fare(self, distance_km):
        """محاسبه کرایه بر اساس مسافت (کیلومتر).

        کرایه = کرایه پایه + (کرایه هر کیلومتر × مسافت)
        در صورت کمتر بودن از حداقل کرایه، همان حداقل لحاظ می‌شود.
        """
        km = Decimal(str(distance_km or 0))
        fare = Decimal(self.base_fare or 0) + (Decimal(self.per_km_fare or 0) * km)
        if self.minimum_fare and fare < Decimal(self.minimum_fare):
            fare = Decimal(self.minimum_fare)
        return fare.quantize(Decimal('1'), rounding=ROUND_HALF_UP)

    def commission_for(self, fare_amount):
        """کمیسیون آژانس برای یک مبلغ کرایه"""
        fare = Decimal(fare_amount or 0)
        commission = fare * self.commission_percent / Decimal('100')
        return commission.quantize(Decimal('1'), rounding=ROUND_HALF_UP)


# =========================================================
# مشتریان شهری (اطلاعات اصلی در ماژول customers ذخیره می‌شود)
# =========================================================
class UrbanCustomerProfile(models.Model):
    """پروفایل مشتری شهری.

    اطلاعات اصلی مشتری در دیتابیس ماژول customers (جدول Customer)
    ذخیره می‌شود و این مدل فقط اطلاعات تکمیلی مخصوص بخش شهری را نگه می‌دارد.
    """

    customer = models.OneToOneField(
        'customers.Customer', on_delete=models.CASCADE,
        related_name='urban_profile', verbose_name='مشتری')
    note = models.TextField(blank=True, null=True, verbose_name='یادداشت داخلی شهری')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='urban_profiles_created',
        verbose_name='ایجاد کننده')
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='urban_profiles_updated',
        verbose_name='آخرین ویرایش توسط')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'پروفایل مشتری شهری'
        verbose_name_plural = 'پروفایل‌های مشتریان شهری'

    def __str__(self):
        return f'پروفایل شهری: {self.customer.name}'


# =========================================================
# درخواست سرویس مشتریان شهری
# =========================================================
class ServiceRequest(models.Model):
    """درخواست سرویس مشتریان شهری"""

    class Status(models.TextChoices):
        PENDING = 'pending', 'در انتظار بررسی'
        APPROVED = 'approved', 'تایید شده'
        ASSIGNED = 'assigned', 'تخصیص یافته'
        IN_PROGRESS = 'in_progress', 'در حال انجام'
        DONE = 'done', 'انجام شده'
        CANCELED = 'canceled', 'لغو شده'
        REJECTED = 'rejected', 'رد شده'

    tracking_code = models.CharField(
        max_length=20, unique=True, verbose_name='کد رهگیری', db_index=True)
    customer = models.ForeignKey(
        'customers.Customer', on_delete=models.PROTECT,
        related_name='urban_service_requests', verbose_name='مشتری')
    service = models.ForeignKey(
        UrbanService, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='service_requests', verbose_name='نوع سرویس')
    rate_card = models.ForeignKey(
        RateCard, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='service_requests', verbose_name='نرخ‌نامه')
    origin_address = models.TextField(verbose_name='آدرس مبدأ')
    destination_address = models.TextField(verbose_name='آدرس مقصد')
    origin_lat = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
        verbose_name='عرض جغرافیایی مبدأ')
    origin_lng = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
        verbose_name='طول جغرافیایی مبدأ')
    destination_lat = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
        verbose_name='عرض جغرافیایی مقصد')
    destination_lng = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
        verbose_name='طول جغرافیایی مقصد')
    passenger_name = models.CharField(
        max_length=100, blank=True, null=True, verbose_name='نام مسافر/گیرنده')
    passenger_phone = models.CharField(
        max_length=15, blank=True, null=True, verbose_name='تلفن مسافر/گیرنده')
    requested_time = jmodels.jDateTimeField(
        null=True, blank=True, verbose_name='زمان نوبت درخواست')
    distance_km = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True,
        verbose_name='مسافت (کیلومتر)')
    fare_amount = models.DecimalField(
        max_digits=15, decimal_places=0, null=True, blank=True,
        verbose_name='کرایه (تومان)')
    commission_amount = models.DecimalField(
        max_digits=15, decimal_places=0, default=0,
        verbose_name='کمیسیون آژانس (تومان)')
    commission_paid = models.BooleanField(
        default=False, verbose_name='کمیسیون تسویه شد')
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING,
        verbose_name='وضعیت', db_index=True)
    assigned_driver = models.ForeignKey(
        Driver, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='urban_service_requests', verbose_name='راننده')
    note = models.TextField(blank=True, null=True, verbose_name='توضیحات')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='urban_requests_created',
        verbose_name='ایجاد کننده')
    created_by_role = models.CharField(max_length=50, blank=True, null=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='urban_requests_updated',
        verbose_name='آخرین ویرایش توسط')
    updated_by_role = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        verbose_name = 'درخواست سرویس شهری'
        verbose_name_plural = 'درخواست‌های سرویس شهری'
        ordering = ('-id',)

    def __str__(self):
        return f'{self.tracking_code} - {self.customer.name}'

    @property
    def jalali_created(self):
        """تاریخ و ساعت ایجاد به شمسی"""
        if not self.created_at:
            return '-'
        jd = jdatetime.date.fromgregorian(date=self.created_at.date())
        return f"{jd.strftime('%Y/%m/%d')} - {self.created_at.strftime('%H:%M')}"


class ServiceRequestStatusLog(models.Model):
    """تاریخچه تغییر وضعیت درخواست سرویس"""

    service_request = models.ForeignKey(
        ServiceRequest, on_delete=models.CASCADE,
        related_name='status_logs', verbose_name='درخواست')
    from_status = models.CharField(max_length=20, blank=True, null=True, verbose_name='وضعیت قبلی')
    to_status = models.CharField(max_length=20, verbose_name='وضعیت جدید')
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='urban_status_logs',
        verbose_name='تغییر دهنده')
    note = models.CharField(max_length=200, blank=True, null=True, verbose_name='توضیح')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'تاریخچه وضعیت سرویس'
        verbose_name_plural = 'تاریخچه وضعیت سرویس‌ها'
        ordering = ('-id',)

    def __str__(self):
        return f'{self.service_request_id}: {self.to_status}'


# =========================================================
# حضور و غیاب رانندگان شهری (تاریخ شمسی)
# =========================================================
class DriverAttendance(models.Model):
    """حضور و غیاب روزانه رانندگان شهری"""

    class Status(models.TextChoices):
        PRESENT = 'present', 'حاضر'
        ABSENT = 'absent', 'غایب'
        LEAVE = 'leave', 'مرخصی'
        MISSION = 'mission', 'ماموریت'

    driver = models.ForeignKey(
        Driver, on_delete=models.CASCADE,
        related_name='urban_attendances', verbose_name='راننده')
    date = jmodels.jDateField(verbose_name='تاریخ (شمسی)', db_index=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PRESENT,
        verbose_name='وضعیت حضور')
    check_in = models.TimeField(null=True, blank=True, verbose_name='ساعت ورود')
    check_out = models.TimeField(null=True, blank=True, verbose_name='ساعت خروج')
    note = models.TextField(blank=True, null=True, verbose_name='توضیحات')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='urban_attendances_created',
        verbose_name='ثبت کننده')
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='urban_attendances_updated',
        verbose_name='آخرین ویرایش توسط')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'حضور و غیاب راننده'
        verbose_name_plural = 'حضور و غیاب رانندگان'
        unique_together = ('driver', 'date')
        ordering = ('-date', 'driver__name')

    def __str__(self):
        return f'{self.driver.name} - {self.date} - {self.get_status_display()}'


# =========================================================
# موقعیت رانندگان
# =========================================================
class DriverLocation(models.Model):
    """آخرین موقعیت ثبت‌شده و وضعیت کاری هر راننده"""

    class Status(models.TextChoices):
        IDLE = 'idle', 'بدون سرویس'
        BUSY = 'busy', 'در حال انجام سرویس'

    # مقدار نشانگر برای تفکیک «ارسال نشدن» از «پاک کردن» سرویس جاری
    _UNSET = object()

    driver = models.OneToOneField(
        Driver, on_delete=models.CASCADE,
        related_name='urban_location', verbose_name='راننده')
    lat = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
        verbose_name='عرض جغرافیایی')
    lng = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
        verbose_name='طول جغرافیایی')
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.IDLE,
        verbose_name='وضعیت کاری')
    current_request = models.ForeignKey(
        ServiceRequest, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='driver_locations', verbose_name='سرویس جاری')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'موقعیت راننده'
        verbose_name_plural = 'موقعیت رانندگان'

    def __str__(self):
        return f'{self.driver.name} - {self.get_status_display()}'

    @property
    def maps_url(self):
        if self.lat and self.lng:
            return f'https://maps.google.com/?q={self.lat},{self.lng}'
        return ''

    @classmethod
    def refresh_location(cls, driver, lat=None, lng=None, status=None, current_request=_UNSET):
        """بروزرسانی موقعیت/وضعیت راننده (idempotent).

        برای پاک کردن سرویس جاری، current_request=None ارسال شود.
        """
        obj, _ = cls.objects.get_or_create(driver=driver)
        if lat is not None:
            obj.lat = lat
        if lng is not None:
            obj.lng = lng
        if status in cls.Status.values:
            obj.status = status
        if current_request is not cls._UNSET:
            obj.current_request = current_request
        obj.save()
        return obj


# =========================================================
# بدهی کمیسیون رانندگان به آژانس
# =========================================================
class CommissionDebt(models.Model):
    """بدهی کمیسیون پرداخت‌نشده راننده به آژانس"""

    driver = models.ForeignKey(
        Driver, on_delete=models.CASCADE,
        related_name='urban_commission_debts', verbose_name='راننده')
    service_request = models.ForeignKey(
        ServiceRequest, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='commission_debts', verbose_name='سرویس مرتبط')
    amount = models.DecimalField(
        max_digits=15, decimal_places=0, verbose_name='مبلغ بدهی (تومان)')
    paid_amount = models.DecimalField(
        max_digits=15, decimal_places=0, default=0,
        verbose_name='پرداخت شده (تومان)')
    is_settled = models.BooleanField(default=False, verbose_name='تسویه شده')
    settled_at = models.DateTimeField(null=True, blank=True, verbose_name='زمان تسویه')
    note = models.CharField(max_length=200, blank=True, null=True, verbose_name='توضیح')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'بدهی کمیسیون'
        verbose_name_plural = 'بدهی‌های کمیسیون'
        ordering = ('is_settled', '-created_at')

    def __str__(self):
        return f'{self.driver.name} - {self.amount}'

    @property
    def remaining(self):
        return (self.amount or Decimal(0)) - (self.paid_amount or Decimal(0))
