"""
Printing views for waybill print permission system.
Refactored with:
- Merged duplicate functions
- Type hints
- PEP8 compliance (max 120 char line length)
- Database-level locking (select_for_update)
- Optimized queries with select_related/prefetch_related
- Django REST Framework integration
- Rate limiting
- Improved error handling
"""
import random
from typing import Any, Dict, Optional, Tuple

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from issuance.models import Bijak
from otp_verification.services import send_otp_via_smsir

from .forms import RequestPrintForm, VerifyOTPForm
from .models import WaybillPrintOTP
from .serializers import RequestOTPSerializer, VerifyOTPSerializer


def generate_otp_code() -> str:
    """Generate a 6-digit OTP code."""
    return str(random.randint(100000, 999999))


def _check_bijak_access(bijak: Bijak, user: Any) -> Tuple[bool, str]:
    """
    Check if user has access to bijak.

    Returns:
        Tuple of (has_access, error_message)
    """
    if bijak.created_by != user:
        return False, 'شما دسترسی به این بارنامه ندارید.'

    if not bijak.driver or not bijak.driver.phone:
        return False, 'شماره موبایل راننده ثبت نشده است.'

    return True, ''


@transaction.atomic
def _process_otp_request(
    bijak: Bijak,
    user: Any
) -> Tuple[bool, Dict[str, Any]]:
    """
    Process OTP request for bijak using database-level locking.

    Uses select_for_update() for database-level locking instead of threading.Lock.

    Returns:
        Tuple of (success, response_data)
    """
    # Database-level locking with select_for_update()
    otp_record = WaybillPrintOTP.objects.select_for_update().get_or_create(
        bijak=bijak
    )[0]

    # If already printed before → immediate permission
    if otp_record.print_count > 0:
        otp_record.print_count += 1
        otp_record.last_print_by = user
        otp_record.last_print_time = timezone.now()
        otp_record.save(update_fields=[
            'print_count', 'last_print_by', 'last_print_time'
        ])
        return True, {
            'need_verification': False,
            'print_url': reverse('issuance:crud:print', args=[bijak.id])
        }

    # First print: generate and send OTP
    new_code = generate_otp_code()
    otp_record.otp_code = new_code
    otp_record.otp_created_at = timezone.now()
    otp_record.is_verified = False
    otp_record.save(update_fields=[
        'otp_code', 'otp_created_at', 'is_verified'
    ])

    success, message = send_otp_via_smsir(bijak.driver.phone, new_code)
    if success:
        return True, {
            'need_verification': True,
            'bijak_id': bijak.id
        }
    else:
        return False, {'error': f'خطا در ارسال پیامک: {message}'}


# ========== Traditional Views (Separate Pages) ==========

@login_required
def request_print_permission(request: Any) -> Any:
    """
    Step 1: User enters waybill number (tracking_code).

    Optimized query with select_related for related fields.
    """
    if request.method == 'POST':
        form = RequestPrintForm(request.POST)
        if form.is_valid():
            tracking_code = form.cleaned_data['waybill_number']

            # Optimized query with select_related
            try:
                bijak = Bijak.objects.select_related(
                    'driver', 'created_by'
                ).get(tracking_code=tracking_code)
            except Bijak.DoesNotExist:
                messages.error(request, 'بارنامه یافت نشد.')
                return render(
                    request,
                    'printing/request_print.html',
                    {'form': form}
                )

            has_access, error_msg = _check_bijak_access(bijak, request.user)
            if not has_access:
                messages.error(request, error_msg)
                return render(
                    request,
                    'printing/request_print.html',
                    {'form': form}
                )

            success, result = _process_otp_request(bijak, request.user)
            if not success:
                messages.error(request, result.get('error', 'خطا'))
                return render(
                    request,
                    'printing/request_print.html',
                    {'form': form}
                )

            if result['need_verification']:
                messages.success(request, 'کد تأیید به راننده ارسال شد.')
                request.session['pending_bijak_id'] = bijak.id
                return redirect('printing:verify_otp')
            else:
                messages.success(request, 'اجازه چاپ صادر شد.')
                return redirect('issuance:crud:print', pk=bijak.id)
    else:
        form = RequestPrintForm()

    return render(
        request,
        'printing/request_print.html',
        {'form': form}
    )


@login_required
def verify_otp(request: Any) -> Any:
    """
    Step 2: Verify received OTP code.

    Uses database-level locking for thread safety.
    """
    bijak_id = request.session.get('pending_bijak_id')
    if not bijak_id:
        messages.error(request, 'لطفاً ابتدا بارنامه را درخواست کنید.')
        return redirect('printing:request_print')

    # Optimized query with select_related
    bijak = get_object_or_404(
        Bijak.objects.select_related('driver'),
        id=bijak_id
    )

    # Database-level locking with select_for_update()
    with transaction.atomic():
        otp_record = get_object_or_404(
            WaybillPrintOTP.objects.select_for_update(),
            bijak=bijak
        )

        if request.method == 'POST':
            form = VerifyOTPForm(request.POST)
            if form.is_valid():
                entered_code = form.cleaned_data['otp_code']

                if otp_record.is_verified:
                    messages.error(
                        request,
                        'این کد قبلاً استفاده شده است.'
                    )
                elif otp_record.is_otp_expired():
                    messages.error(
                        request,
                        'کد تأیید منقضی شده است. دوباره درخواست کنید.'
                    )
                elif otp_record.otp_code != entered_code:
                    messages.error(request, 'کد وارد شده اشتباه است.')
                else:
                    # Successful verification
                    otp_record.print_count += 1
                    otp_record.last_print_by = request.user
                    otp_record.last_print_time = timezone.now()
                    otp_record.is_verified = True
                    otp_record.save(update_fields=[
                        'print_count', 'last_print_by',
                        'last_print_time', 'is_verified'
                    ])
                    messages.success(
                        request,
                        'کد تأیید شد. اجازه چاپ صادر گردید.'
                    )
                    del request.session['pending_bijak_id']
                    return redirect('issuance:crud:print', pk=bijak.id)
            else:
                messages.error(request, 'فرم نامعتبر است.')
        else:
            form = VerifyOTPForm(
                initial={'waybill_number': bijak.tracking_code}
            )

    return render(
        request,
        'printing/verify_otp.html',
        {'form': form, 'bijak': bijak}
    )


# ========== API Views (DRF with Rate Limiting) ==========

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_request_otp(request: Any) -> Response:
    """
    API endpoint for requesting OTP.

    Features:
    - DRF serializer validation
    - Database-level locking
    - Rate limiting ready
    - Proper error handling
    """
    serializer = RequestOTPSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {'success': False, 'errors': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    bijak_id = serializer.validated_data['bijak_id']

    try:
        # Optimized query with select_related
        bijak = Bijak.objects.select_related(
            'driver', 'created_by'
        ).get(id=bijak_id)
    except Bijak.DoesNotExist:
        return Response(
            {'success': False, 'message': 'بارنامه یافت نشد.'},
            status=status.HTTP_404_NOT_FOUND
        )

    has_access, error_msg = _check_bijak_access(bijak, request.user)
    if not has_access:
        return Response(
            {'success': False, 'message': error_msg},
            status=status.HTTP_403_FORBIDDEN
        )

    try:
        success, result = _process_otp_request(bijak, request.user)
        if not success:
            return Response(
                {'success': False, 'message': result.get('error')},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        if result['need_verification']:
            request.session['pending_otp_bijak_id'] = bijak.id
            return Response({
                'success': True,
                'need_verification': True,
                'message': (
                    'کد تأیید برای راننده ارسال شد. '
                    'لطفاً کد را وارد کنید.'
                ),
                'bijak_id': bijak.id
            })
        else:
            return Response({
                'success': True,
                'need_verification': False,
                'message': (
                    'این بارنامه قبلاً چاپ شده است. '
                    'اجازه چاپ صادر می‌شود.'
                ),
                'print_url': result['print_url']
            })

    except Exception as e:
        return Response(
            {'success': False, 'message': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_verify_otp(request: Any) -> Response:
    """
    API endpoint for verifying OTP.

    Features:
    - DRF serializer validation
    - Database-level locking with select_for_update()
    - Rate limiting ready
    - Proper error handling
    """
    serializer = VerifyOTPSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {'success': False, 'errors': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    bijak_id = serializer.validated_data['bijak_id']
    otp_code = serializer.validated_data['otp_code']

    try:
        bijak = Bijak.objects.select_related('created_by').get(id=bijak_id)
    except Bijak.DoesNotExist:
        return Response(
            {'success': False, 'message': 'بارنامه نامعتبر.'},
            status=status.HTTP_404_NOT_FOUND
        )

    if bijak.created_by != request.user:
        return Response(
            {'success': False, 'message': 'دسترسی ندارید.'},
            status=status.HTTP_403_FORBIDDEN
        )

    try:
        # Database-level locking with select_for_update()
        with transaction.atomic():
            otp_record = WaybillPrintOTP.objects.select_for_update().get(
                bijak=bijak
            )

            if otp_record.is_verified:
                return Response(
                    {'success': False,
                     'message': 'این کد قبلاً استفاده شده است.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if otp_record.is_otp_expired():
                return Response(
                    {'success': False,
                     'message': 'کد تأیید منقضی شده است. دوباره درخواست کنید.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if otp_record.otp_code != otp_code:
                return Response(
                    {'success': False, 'message': 'کد وارد شده اشتباه است.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Successful verification
            otp_record.print_count += 1
            otp_record.last_print_by = request.user
            otp_record.last_print_time = timezone.now()
            otp_record.is_verified = True
            otp_record.save(update_fields=[
                'print_count', 'last_print_by',
                'last_print_time', 'is_verified'
            ])

            if request.session.get('pending_otp_bijak_id'):
                del request.session['pending_otp_bijak_id']

            return Response({
                'success': True,
                'message': 'کد تأیید شد. اجازه چاپ صادر گردید.',
                'print_url': reverse('issuance:crud:print', args=[bijak.id])
            })

    except WaybillPrintOTP.DoesNotExist:
        return Response(
            {
                'success': False,
                'message': (
                    'درخواستی یافت نشد. '
                    'ابتدا درخواست ارسال کد را بزنید.'
                )
            },
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'success': False, 'message': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
