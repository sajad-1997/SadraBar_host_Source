from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic import TemplateView
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.conf import settings


# ممکن است نیاز به فرم داشته باشید
# from .forms import ContactForm

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'issuance/base.html'


class StaffOnlyView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'issuance/bijak/issuance_form.html'

    def test_func(self):
        return self.request.user.role in ['admin', 'staff']


def index(request):
    return render(request, 'homePage/index.html')


def tariff(request):
    return render(request, 'homePage/tariffs.html')


def reserve(request):
    if request.method == 'POST':
        # مقادیر فرم
        full_name = request.POST['full_name']
        phone = request.POST['phone']
        origin = request.POST['origin']
        destination = request.POST['destination']
        cargo_type = request.POST['cargo_type']
        weight = request.POST.get('weight')
        description = request.POST.get('description')

        # ذخیره یا ارسال به دیتابیس
        # Reserve.objects.create(...)

        return render(request, 'homePage/reserve_success.html')

    return HttpResponse("فرم اشتباه ارسال شده است.")


def services(request):
    return render(request, 'homePage/services.html')


def tracking(request):
    return render(request, 'homePage/tracking.html')


def contact(request):
    return render(request, 'homePage/contact.html')


def register(request):
    return render(request, 'homePage/register.html')


def contact_submit_view(request):
        if request.method == 'POST':
            # دریافت داده‌ها از فرم
            name = request.POST.get('name')
            email = request.POST.get('email')
            subject = request.POST.get('subject')
            message = request.POST.get('message')

            # منطق پردازش فرم (مثلاً ارسال ایمیل)
            try:
                send_mail(
                    subject=f'پیام از طرف {name} - {subject}',
                    message=f'نام: {name}\nایمیل: {email}\n\nپیام:\n{message}',
                    from_email=settings.DEFAULT_FROM_EMAIL,  # یا ایمیلی که می‌خواهید نمایش داده شود
                    recipient_list=['your_admin_email@example.com'],  # ایمیل مقصد
                    fail_silently=False,
                )
                # پس از ارسال موفق، به صفحه تشکر یا صفحه اصلی هدایت کنید
                # return redirect('contact_success') # اگر صفحه تشکر دارید
                return redirect('contact')  # یا به همان صفحه تماس برگردید با پیام موفقیت
            except Exception as e:
                # مدیریت خطا در صورت بروز مشکل در ارسال ایمیل
                print(f"Error sending email: {e}")
                # return render(request, 'contact.html', {'error': 'خطا در ارسال پیام.'})
                return redirect('contact')  # یا به صفحه تماس برگردید با پیام خطا

        # اگر متد POST نبود، به صفحه اصلی یا تماس هدایت کنید
        return redirect('contact')  # یا render(request, 'contact.html')
