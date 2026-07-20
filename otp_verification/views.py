from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt  # برای تست، در تولید CSRF فعال است
from django.views.decorators.http import require_http_methods
from .forms import PhoneNumberForm, OTPVerificationForm
from .utils import generate_otp, verify_otp
from .services import send_otp_via_smsir

@require_http_methods(["GET", "POST"])
def request_otp(request):
    """مرحله اول: دریافت شماره و ارسال کد"""
    if request.method == "POST":
        form = PhoneNumberForm(request.POST)
        if form.is_valid():
            phone = form.cleaned_data['phone_number']
            # تولید کد
            code = generate_otp(phone)
            # ارسال کد از طریق سرویس
            success, message = send_otp_via_smsir(phone, code)
            if success:
                # ذخیره شماره در session برای مرحله بعد
                request.session['otp_phone'] = phone
                messages.success(request, "کد تأیید برای شما ارسال شد.")
                return redirect('otp_verification:verify_otp')
            else:
                messages.error(request, f"خطا در ارسال پیامک: {message}")
        else:
            messages.error(request, "شماره وارد شده معتبر نیست.")
    else:
        form = PhoneNumberForm()
    return render(request, 'otp_verification/request_otp.html', {'form': form})

@require_http_methods(["GET", "POST"])
def verify_otp_view(request):
    """مرحله دوم: دریافت کد و تأیید"""
    phone = request.session.get('otp_phone')
    if not phone:
        messages.error(request, "لطفاً ابتدا شماره خود را وارد کنید.")
        return redirect('otp_verification:request_otp')

    if request.method == "POST":
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            entered_code = form.cleaned_data['code']
            if verify_otp(phone, entered_code):
                messages.success(request, "احراز هویت با موفقیت انجام شد.")
                # در اینجا می‌توانید کاربر را لاگین کنید یا توکن صادر کنید
                # مثلاً request.session['verified'] = True
                return redirect('otp_verification:success_page')
            else:
                messages.error(request, "کد وارد شده اشتباه یا منقضی شده است.")
        else:
            messages.error(request, "کد نامعتبر است.")
    else:
        form = OTPVerificationForm(initial={'phone_number': phone})
    return render(request, 'otp_verification/verify_otp.html', {'form': form, 'phone': phone})

def success_page(request):
    return render(request, 'otp_verification/success.html')