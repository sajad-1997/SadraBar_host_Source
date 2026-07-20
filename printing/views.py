import json
import random
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from issuance.models import Bijak
from .models import WaybillPrintOTP
from .forms import RequestPrintForm, VerifyOTPForm
from otp_verification.services import send_otp_via_smsir


def generate_otp_code():
    return str(random.randint(100000, 999999))


# ========== ویوهای معمولی (صفحات جداگانه) ==========

@login_required
def request_print_permission(request):
    """مرحله اول: کاربر شماره بارنامه (tracking_code) را وارد می‌کند"""
    if request.method == 'POST':
        form = RequestPrintForm(request.POST)
        if form.is_valid():
            tracking_code = form.cleaned_data['waybill_number']  # نام فیلد در فرم را می‌توانید تغییر دهید
            try:
                bijak = Bijak.objects.get(tracking_code=tracking_code)
            except Bijak.DoesNotExist:
                messages.error(request, 'بارنامه یافت نشد.')
                return render(request, 'printing/request_print.html', {'form': form})

            if bijak.created_by != request.user:
                messages.error(request, 'شما دسترسی به این بارنامه ندارید.')
                return render(request, 'printing/request_print.html', {'form': form})

            if not bijak.driver or not bijak.driver.phone:
                messages.error(request, 'شماره موبایل راننده ثبت نشده است.')
                return render(request, 'printing/request_print.html', {'form': form})

            otp_record, created = WaybillPrintOTP.objects.get_or_create(bijak=bijak)

            # چاپ قبلی داشته → اجازه فوری
            if otp_record.print_count > 0:
                otp_record.print_count += 1
                otp_record.last_print_by = request.user
                otp_record.last_print_time = timezone.now()
                otp_record.save()
                messages.success(request, 'اجازه چاپ صادر شد.')
                return redirect('issuance:crud:print', pk=bijak.id)

            # اولین چاپ: ارسال کد
            new_code = generate_otp_code()
            otp_record.otp_code = new_code
            otp_record.otp_created_at = timezone.now()
            otp_record.is_verified = False
            otp_record.save()

            success, message = send_otp_via_smsir(bijak.driver.phone, new_code)
            if success:
                messages.success(request, 'کد تأیید به راننده ارسال شد.')
                request.session['pending_bijak_id'] = bijak.id
                return redirect('printing:verify_otp')
            else:
                messages.error(request, f'خطا در ارسال پیامک: {message}')
                return render(request, 'printing/request_print.html', {'form': form})
    else:
        form = RequestPrintForm()
    return render(request, 'printing/request_print.html', {'form': form})


@login_required
def verify_otp(request):
    """مرحله دوم: تأیید کد دریافتی"""
    bijak_id = request.session.get('pending_bijak_id')
    if not bijak_id:
        messages.error(request, 'لطفاً ابتدا بارنامه را درخواست کنید.')
        return redirect('printing:request_print')

    bijak = get_object_or_404(Bijak, id=bijak_id)
    otp_record = get_object_or_404(WaybillPrintOTP, bijak=bijak)

    if request.method == 'POST':
        form = VerifyOTPForm(request.POST)
        if form.is_valid():
            entered_code = form.cleaned_data['otp_code']
            if (otp_record.otp_code == entered_code
                    and not otp_record.is_otp_expired()
                    and not otp_record.is_verified):
                otp_record.print_count += 1
                otp_record.last_print_by = request.user
                otp_record.last_print_time = timezone.now()
                otp_record.is_verified = True
                otp_record.save()
                messages.success(request, 'کد تأیید شد. اجازه چاپ صادر گردید.')
                del request.session['pending_bijak_id']
                return redirect('issuance:crud:print', pk=bijak.id)
            else:
                if otp_record.is_otp_expired():
                    messages.error(request, 'کد تأیید منقضی شده است. دوباره درخواست کنید.')
                else:
                    messages.error(request, 'کد وارد شده اشتباه است.')
        else:
            messages.error(request, 'فرم نامعتبر است.')
    else:
        form = VerifyOTPForm(initial={'waybill_number': bijak.tracking_code})
    return render(request, 'printing/verify_otp.html', {'form': form, 'bijak': bijak})


# ========== ویوهای API برای استفاده در مودال (AJAX) ==========

@login_required
@require_http_methods(["POST"])
def api_request_otp(request):
    try:
        data = json.loads(request.body)
        bijak_id = data.get('bijak_id')
        if not bijak_id:
            return JsonResponse({'success': False, 'message': 'شناسه بارنامه ارسال نشده است.'})

        bijak = get_object_or_404(Bijak, id=bijak_id)
        if bijak.created_by != request.user:
            return JsonResponse({'success': False, 'message': 'شما دسترسی به این بارنامه ندارید.'})

        if not bijak.driver or not bijak.driver.phone:
            return JsonResponse({'success': False, 'message': 'شماره موبایل راننده ثبت نشده است.'})

        otp_record, created = WaybillPrintOTP.objects.get_or_create(bijak=bijak)

        # چاپ قبلی داشته → اجازه فوری
        if otp_record.print_count > 0:
            return JsonResponse({
                'success': True,
                'need_verification': False,
                'message': 'این بارنامه قبلاً چاپ شده است. اجازه چاپ صادر می‌شود.',
                'print_url': reverse('issuance:crud:print', args=[bijak.id])
            })

        # اولین چاپ: تولید و ارسال کد
        new_code = generate_otp_code()
        otp_record.otp_code = new_code
        otp_record.otp_created_at = timezone.now()
        otp_record.is_verified = False
        otp_record.save()

        success, message = send_otp_via_smsir(bijak.driver.phone, new_code)
        if success:
            request.session['pending_otp_bijak_id'] = bijak.id
            return JsonResponse({
                'success': True,
                'need_verification': True,
                'message': 'کد تأیید برای راننده ارسال شد. لطفاً کد را وارد کنید.',
                'bijak_id': bijak.id
            })
        else:
            return JsonResponse({'success': False, 'message': f'خطا در ارسال پیامک: {message}'})

    except Bijak.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'بارنامه یافت نشد.'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@require_http_methods(["POST"])
def api_verify_otp(request):
    try:
        data = json.loads(request.body)
        bijak_id = data.get('bijak_id')
        otp_code = data.get('otp_code')
        if not bijak_id or not otp_code:
            return JsonResponse({'success': False, 'message': 'اطلاعات کامل نیست.'})

        bijak = get_object_or_404(Bijak, id=bijak_id)
        if bijak.created_by != request.user:
            return JsonResponse({'success': False, 'message': 'دسترسی ندارید.'})

        otp_record = get_object_or_404(WaybillPrintOTP, bijak=bijak)

        if otp_record.is_verified:
            return JsonResponse({'success': False, 'message': 'این کد قبلاً استفاده شده است.'})
        if otp_record.is_otp_expired():
            return JsonResponse({'success': False, 'message': 'کد تأیید منقضی شده است. دوباره درخواست کنید.'})
        if otp_record.otp_code != otp_code:
            return JsonResponse({'success': False, 'message': 'کد وارد شده اشتباه است.'})

        # تأیید موفق
        otp_record.print_count += 1
        otp_record.last_print_by = request.user
        otp_record.last_print_time = timezone.now()
        otp_record.is_verified = True
        otp_record.save()

        if request.session.get('pending_otp_bijak_id'):
            del request.session['pending_otp_bijak_id']

        return JsonResponse({
            'success': True,
            'message': 'کد تأیید شد. اجازه چاپ صادر گردید.',
            'print_url': reverse('issuance:crud:print', args=[bijak.id])
        })

    except Bijak.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'بارنامه نامعتبر.'})
    except WaybillPrintOTP.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'درخواستی یافت نشد. ابتدا درخواست ارسال کد را بزنید.'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})
