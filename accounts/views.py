# accounts/views.py
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib.auth.views import LogoutView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from .decorators import ROLE_ADMIN, ROLE_MANAGER, ROLE_EMPLOYEE, ROLE_DRIVER, ROLE_CUSTOMER
from system_control.security_monitor import SecurityMonitor

logger = logging.getLogger(__name__)


class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = False

    def _get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def dispatch(self, request, *args, **kwargs):
        logger.info(f"Login view accessed - Method: {request.method}")
        return super().dispatch(request, *args, **kwargs)

    def form_invalid(self, form):
        username = form.cleaned_data.get('username', 'unknown')
        ip_address = self._get_client_ip(self.request)
        user_agent = self.request.META.get('HTTP_USER_AGENT', '')
        
        logger.warning(f"Login failed for username: {username}")
        logger.warning(f"Form errors: {form.errors}")
        logger.warning(f"Non-field errors: {form.non_field_errors}")
        
        # Log failed login attempt
        SecurityMonitor.log_login_attempt(username, ip_address, False, user_agent)
        SecurityMonitor.log_event(
            'login_failure',
            ip_address=ip_address,
            user_agent=user_agent,
            path=self.request.path,
            severity='medium',
            details={'username': username}
        )
        
        # Check for brute force
        if SecurityMonitor.check_brute_force(username, ip_address):
            SecurityMonitor.log_event(
                'brute_force_attempt',
                ip_address=ip_address,
                user_agent=user_agent,
                path=self.request.path,
                severity='high',
                details={'username': username}
            )
            messages.error(self.request, 'تلاش‌های ناموفق زیاد. لطفاً چند دقیقه صبر کنید.')
        
        messages.error(self.request, 'نام کاربری یا رمز عبور اشتباه است.')
        return super().form_invalid(form)

    def form_valid(self, form):
        username = form.cleaned_data.get('username')
        ip_address = self._get_client_ip(self.request)
        user_agent = self.request.META.get('HTTP_USER_AGENT', '')
        
        logger.info(f"Login successful for username: {username}")
        logger.info(f"User role: {form.get_user().role}")
        logger.info(f"Redirecting to: {self.get_success_url()}")
        
        # Log successful login
        SecurityMonitor.log_login_attempt(username, ip_address, True, user_agent)
        SecurityMonitor.log_event(
            'login_success',
            user=form.get_user(),
            ip_address=ip_address,
            user_agent=user_agent,
            path=self.request.path,
            severity='low'
        )
        
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
