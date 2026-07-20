# accounts/views.py
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib.auth.views import LogoutView
from django.shortcuts import redirect
from django.urls import reverse_lazy

logger = logging.getLogger(__name__)


class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'

    def get_success_url(self):
        user = self.request.user
        if user.role == 'admin':
            return reverse_lazy('dashboard:admin_dashboard')
        elif user.role == 'manager':
            return reverse_lazy('dashboard:manager_dashboard')
        elif user.role == 'staff':
            return reverse_lazy('dashboard:staff_dashboard')
        else:
            return reverse_lazy('home')


class SuperAdminLoginView(LoginView):
    template_name = 'accounts/super_admin_login.html'

    def get_success_url(self):
        user = self.request.user
        # فقط کاربری با نقش admin اجازه ورود داره
        if user.role == 'admin':
            return reverse_lazy('home_dashboard')
        else:
            return reverse_lazy('home')


class CustomLogoutView(LogoutView):
    """
    نسخه حرفه‌ای خروج:
    - پشتیبانی از GET (بدون خطای CSRF)
    - ثبت لاگ خروج
    - پیام خروج به کاربر
    - ریدایرکت به صفحه اصلی
    """

    next_page = '/'  # مقصد بعد از خروج

    # def get(self, request, *args, **kwargs):
    #     """اجازه خروج با GET بدون نیاز به CSRF"""
    #     return self.post(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        # ذخیره نام کاربر قبل از logout
        username = request.user.username if request.user.is_authenticated else None

        # خروج کاربر
        response = super().post(request, *args, **kwargs)

        # پیام موفقیت
        if username:
            messages.success(request, f"کاربر «{username}» با موفقیت خارج شد.")

        # ثبت در لاگ‌ها (logs)
        if username:
            logger.info(f"User '{username}' logged out successfully.")

        return response


@login_required
def go_to_dashboard(request):
    user = request.user

    # مدیر کل سیستم → داشبورد مدیر کل
    if user.is_admin():
        return redirect("dashboard:admin_dashboard")

    # مدیریت → داشبورد مدیریت
    if user.is_manager():
        return redirect("dashboard:manager_dashboard")

    # کارمند → داشبورد کارمند
    if user.is_staff_role():
        return redirect("dashboard:staff_dashboard")

    # حالت fallback
    return redirect("home")
