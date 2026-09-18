# accounts/views.py
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib.auth.views import LogoutView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from .decorators import ROLE_ADMIN, ROLE_MANAGER, ROLE_EMPLOYEE, ROLE_DRIVER, ROLE_CUSTOMER

logger = logging.getLogger(__name__)


class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = False

    def dispatch(self, request, *args, **kwargs):
        logger.info(f"Login view accessed - Method: {request.method}")
        return super().dispatch(request, *args, **kwargs)

    def form_invalid(self, form):
        logger.warning(f"Login failed for username: {form.cleaned_data.get('username', 'unknown')}")
        logger.warning(f"Form errors: {form.errors}")
        logger.warning(f"Non-field errors: {form.non_field_errors}")
        messages.error(self.request, 'نام کاربری یا رمز عبور اشتباه است.')
        return super().form_invalid(form)

    def form_valid(self, form):
        logger.info(f"Login successful for username: {form.cleaned_data.get('username')}")
        logger.info(f"User role: {form.get_user().role}")
        logger.info(f"Redirecting to: {self.get_success_url()}")
        return super().form_valid(form)

    def get_success_url(self):
        user = self.request.user
        if not user.is_authenticated:
            logger.warning("User not authenticated in get_success_url")
            return reverse_lazy('home')
        
        logger.info(f"Redirecting user {user.username} with role {user.role}")
        if user.role == ROLE_ADMIN:
            return reverse_lazy('dashboard:admin_dashboard')
        elif user.role == ROLE_MANAGER:
            return reverse_lazy('dashboard:manager_dashboard')
        elif user.role == ROLE_EMPLOYEE:
            return reverse_lazy('dashboard:staff_dashboard')
        elif user.role == ROLE_DRIVER:
            return reverse_lazy('home')
        elif user.role == ROLE_CUSTOMER:
            return reverse_lazy('home')
        else:
            return reverse_lazy('home')


class SuperAdminLoginView(LoginView):
    template_name = 'accounts/super_admin_login.html'

    def get_success_url(self):
        user = self.request.user
        # فقط کاربری با نقش admin اجازه ورود داره
        if user.role == ROLE_ADMIN:
            return reverse_lazy('home_dashboard')
        else:
            return reverse_lazy('home')


class CustomLogoutView(LogoutView):
    """
    نسخه حرفه‌ای خروج:
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
    if user.is_employee():
        return redirect("dashboard:staff_dashboard")

    # حالت fallback
    return redirect("home")
