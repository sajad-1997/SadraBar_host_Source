import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from . import conf


class QueueProfile(models.Model):
    """پروفایل جانبی راننده در ماژول نوبت‌دهی (بدون دست زدن به مدل Driver)."""
    driver = models.OneToOneField(
        conf.DRIVER_MODEL, verbose_name="راننده",
        on_delete=models.CASCADE, related_name="queue_profile")
    office_approved = models.BooleanField(
        "تایید دفتر باربری", default=False,
        help_text="پس از ارائه اطلاعات تکمیلی به دفتر، از پنل/ادمین True شود.")
    registered_via_queue = models.BooleanField("ثبت‌نام از طریق صفحه نوبت‌دهی", default=True)
    created_at = models.DateTimeField("زمان ایجاد", auto_now_add=True)

    class Meta:
        verbose_name = "پروفایل نوبت‌دهی راننده"
        verbose_name_plural = "پروفایل‌های نوبت‌دهی"

    def __str__(self):
        return f"پروفایل نوبت‌دهی: {self.driver}"


class QueueStaff(models.Model):
    """کاربران مجاز پنل نوبت‌دهی: کارمند (نیازمند تایید) و مدیریت."""

    class Role(models.TextChoices):
        STAFF = "staff", "کارمند"
        MANAGER = "manager", "مدیریت"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, verbose_name="کاربر",
        on_delete=models.CASCADE, related_name="queue_staff")
    role = models.CharField("نقش", max_length=10,
                            choices=Role.choices, default=Role.STAFF)
    approved = models.BooleanField("مورد تایید مدیر", default=False)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="تاییدکننده",
        null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    approved_at = models.DateTimeField("زمان تایید", null=True, blank=True)
    created_at = models.DateTimeField("زمان ایجاد", auto_now_add=True)

    class Meta:
        verbose_name = "کاربر مجاز پنل"
        verbose_name_plural = "کاربران مجاز پنل"

    def __str__(self):
        return f"{self.user} ({self.get_role_display()})"

    @property
    def has_access(self):
        return (self.role == self.Role.MANAGER
                or (self.role == self.Role.STAFF and self.approved))


class QueueTicket(models.Model):
    """نوبت روزانه یک راننده در صف."""

    class Status(models.TextChoices):
        WAITING = "waiting", "در صف"
        LOADED = "loaded", "بار گرفته"
        LEFT = "left", "انصراف"
        REMOVED_NO_RESPONSE = "no_response", "حذف (عدم پاسخ به اعلان)"
        REMOVED_DISTANCE = "distance", "حذف (خارج از محدوده دفتر)"
        REMOVED_BY_STAFF = "staff", "حذف توسط کاربر پنل"

    driver = models.ForeignKey(
        conf.DRIVER_MODEL, verbose_name="راننده",
        on_delete=models.CASCADE, related_name="queue_tickets")
    date = models.DateField("تاریخ صف")
    number = models.PositiveIntegerField("شماره نوبت")
    status = models.CharField("وضعیت", max_length=20,
                              choices=Status.choices, default=Status.WAITING)
    joined_at = models.DateTimeField("زمان پیوستن به صف", auto_now_add=True)
    removed_at = models.DateTimeField("زمان خروج", null=True, blank=True)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    class Meta:
        verbose_name = "نوبت روزانه"
        verbose_name_plural = "نوبت‌های روزانه"
        ordering = ["date", "number"]
        constraints = [
            models.UniqueConstraint(fields=["driver", "date"],
                                    name="uniq_ticket_per_driver_per_day"),
        ]

    def __str__(self):
        return f"نوبت {self.number} - {self.driver} - {self.date}"


class Announcement(models.Model):
    class Response(models.TextChoices):
        LOADED = "loaded", "بار گرفته‌ام"
        STILL_WAITING = "waiting", "هنوز در نوبت هستم"

    ticket = models.ForeignKey(QueueTicket, verbose_name="نوبت",
                               on_delete=models.CASCADE, related_name="announcements")
    day = models.DateField("تاریخ")
    sent_at = models.DateTimeField("زمان ارسال", default=timezone.now)
    response = models.CharField("پاسخ", max_length=10,
                                choices=Response.choices, null=True, blank=True)
    responded_at = models.DateTimeField("زمان پاسخ", null=True, blank=True)
    sms_result = models.TextField("نتیجه ارسال پیامک", blank=True)

    class Meta:
        verbose_name = "اعلان"
        verbose_name_plural = "اعلان‌ها"
        ordering = ["-sent_at"]

    def __str__(self):
        return f"اعلان {self.ticket} - {self.day}"


class QueueLog(models.Model):
    """گزارش عملیات کاربران پنل روی سیستم نوبت‌دهی."""

    class Action(models.TextChoices):
        ADD_TICKET = "add_ticket", "ثبت نوبت دستی"
        REMOVE_TICKET = "remove_ticket", "حذف نوبت"
        MARK_LOADED = "mark_loaded", "ثبت بارگیری"
        APPROVE_DRIVER = "approve_driver", "تایید راننده"
        UNAPPROVE_DRIVER = "unapprove_driver", "لغو تایید راننده"
        STAFF_ADD = "staff_add", "افزودن کاربر مجاز"
        STAFF_APPROVE = "staff_approve", "تایید کاربر مجاز"
        STAFF_UNAPPROVE = "staff_unapprove", "لغو تایید کاربر مجاز"
        STAFF_REMOVE = "staff_remove", "حذف کاربر مجاز"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="کاربر",
        null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    action = models.CharField("عملیات", max_length=20, choices=Action.choices)
    driver = models.ForeignKey(
        conf.DRIVER_MODEL, verbose_name="راننده",
        null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    ticket = models.ForeignKey(QueueTicket, verbose_name="نوبت",
                               null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    detail = models.TextField("توضیح", blank=True)
    created_at = models.DateTimeField("زمان", auto_now_add=True)

    class Meta:
        verbose_name = "گزارش عملیات"
        verbose_name_plural = "گزارش عملیات"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_action_display()} توسط {self.user}"
