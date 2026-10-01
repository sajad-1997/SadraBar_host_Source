import random
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from .models import (
    CommissionDebt,
    DriverAttendance,
    DriverLocation,
    ServiceRequest,
    ServiceRequestStatusLog,
)

TRACKING_ATTEMPTS = 25


# =========================================================
# درخواست سرویس
# =========================================================
def generate_tracking_code():
    """تولید کد رهگیری یکتا برای درخواست سرویس"""
    for _ in range(TRACKING_ATTEMPTS):
        code = f'UD-{random.randint(100000, 999999)}'
        if not ServiceRequest.objects.filter(tracking_code=code).exists():
            return code
    raise RuntimeError('تولید کد رهگیری یکتا ناموفق بود؛ لطفاً دوباره تلاش کنید.')


def compute_fare(service_request):
    """محاسبه کرایه و کمیسیون سرویس.

    خروجی: (کرایه، کمیسیون)
    اگر نرخ‌نامه یا مسافت ثبت نشده باشد، مقادیر فعلی حفظ می‌شود؛
    در صورت ثبت کرایه دستی، کمیسیون بر اساس نرخ‌نامه محاسبه می‌شود.
    """
    rate = service_request.rate_card
    if rate is None:
        return service_request.fare_amount, (service_request.commission_amount or Decimal(0))

    if service_request.distance_km is not None:
        fare = rate.calculate_fare(service_request.distance_km)
        return fare, rate.commission_for(fare)

    if service_request.fare_amount:
        return service_request.fare_amount, rate.commission_for(service_request.fare_amount)

    return service_request.fare_amount, (service_request.commission_amount or Decimal(0))


def recompute_fare(service_request, save=True):
    """محاسبه مجدد کرایه و کمیسیون درخواست سرویس"""
    fare, commission = compute_fare(service_request)
    service_request.fare_amount = fare
    service_request.commission_amount = commission or Decimal(0)
    if save:
        service_request.save(update_fields=['fare_amount', 'commission_amount', 'updated_at'])
    return service_request


def log_status(service_request, from_status, to_status, user=None, note=''):
    """ثبت تاریخچه تغییر وضعیت"""
    return ServiceRequestStatusLog.objects.create(
        service_request=service_request,
        from_status=from_status or '',
        to_status=to_status,
        changed_by=user if getattr(user, 'is_authenticated', False) else None,
        note=note or '',
    )


@transaction.atomic
def assign_request(service_request, driver, service=None, user=None):
    """تخصیص راننده به درخواست سرویس.

    وضعیت سرویس تغییر نمی‌کند؛ وضعیت «تخصیص یافته» پس از قبول سرویس
    توسط راننده (تغییر وضعیت به ASSIGNED) اعمال می‌شود.
    """
    service_request.assigned_driver = driver
    if service is not None:
        service_request.service = service

    recompute_fare(service_request, save=False)
    service_request.save()

    log_status(service_request, service_request.status, service_request.status,
               user, note='تخصیص راننده (در انتظار قبول راننده)')

    # راننده تخصیص یافته در وضعیت «در حال انجام سرویس» قرار می‌گیرد
    DriverLocation.refresh_location(
        driver, status=DriverLocation.Status.BUSY, current_request=service_request)
    return service_request


@transaction.atomic
def change_status(service_request, new_status, user=None, note=''):
    """تغییر وضعیت درخواست سرویس با ثبت تاریخچه و اثرات جانبی"""
    old_status = service_request.status
    service_request.status = new_status

    if new_status == ServiceRequest.Status.DONE:
        recompute_fare(service_request, save=False)
        service_request.save()

        # ثبت بدهی کمیسیون راننده به آژانس
        if service_request.assigned_driver_id:
            commission = service_request.commission_amount or Decimal(0)
            if commission > 0:
                debt = CommissionDebt.objects.filter(
                    driver_id=service_request.assigned_driver_id,
                    service_request=service_request,
                    is_settled=False,
                ).first()
                if debt:
                    debt.amount = commission
                    debt.save()
                else:
                    CommissionDebt.objects.create(
                        driver_id=service_request.assigned_driver_id,
                        service_request=service_request,
                        amount=commission,
                    )

            # راننده پس از اتمام سرویس، بدون سرویس می‌شود
            DriverLocation.refresh_location(
                service_request.assigned_driver,
                status=DriverLocation.Status.IDLE, current_request=None)

    elif new_status in (ServiceRequest.Status.CANCELED, ServiceRequest.Status.REJECTED):
        if service_request.assigned_driver_id:
            DriverLocation.refresh_location(
                service_request.assigned_driver,
                status=DriverLocation.Status.IDLE, current_request=None)
        service_request.save()
    else:
        service_request.save()

    log_status(service_request, old_status, new_status, user, note)
    return service_request


# =========================================================
# حضور و غیاب
# =========================================================
def set_attendance(driver, date, status, user=None, note=''):
    """ثبت/بروزرسانی حضور و غیاب راننده برای یک تاریخ شمسی"""
    defaults = {'status': status, 'note': note or ''}
    if getattr(user, 'is_authenticated', False):
        defaults['updated_by'] = user
    obj, _ = DriverAttendance.objects.update_or_create(
        driver=driver, date=date, defaults=defaults)
    return obj


# =========================================================
# بدهی کمیسیون
# =========================================================
@transaction.atomic
def settle_debt(debt, amount, user=None, note=''):
    """پرداخت (کامل یا قسمتی) بدهی کمیسیون راننده"""
    amount = Decimal(amount or 0)
    if amount <= 0:
        raise ValueError('مبلغ پرداخت باید بزرگ‌تر از صفر باشد.')

    debt.paid_amount = (debt.paid_amount or Decimal(0)) + amount
    if debt.paid_amount >= debt.amount:
        debt.is_settled = True
        debt.settled_at = timezone.now()
    if note:
        debt.note = note
    debt.save()

    # اگر بدهی سرویس مربوطه کاملاً تسویه شد، سرویس را تسویه‌شده علامت بزن
    if debt.is_settled and debt.service_request_id:
        ServiceRequest.objects.filter(pk=debt.service_request_id).update(commission_paid=True)
    return debt
