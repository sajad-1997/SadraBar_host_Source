from django import forms
from django.contrib.auth.password_validation import validate_password

from accounts.models import User
from .models import IssuanceQuota, Role, SystemRule
from .services import all_roles


class UserCreateForm(forms.ModelForm):
    """فرم ایجاد کاربر توسط سوپر ادمین"""

    password1 = forms.CharField(
        label='رمز عبور', widget=forms.PasswordInput, strip=False)
    password2 = forms.CharField(
        label='تکرار رمز عبور', widget=forms.PasswordInput, strip=False)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'role')
        labels = {
            'username': 'نام کاربری',
            'first_name': 'نام',
            'last_name': 'نام خانوادگی',
            'email': 'ایمیل',
            'role': 'نقش',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].choices = all_roles()

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('این نام کاربری قبلاً استفاده شده است.')
        return username

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('رمزهای عبور یکسان نیستند.')
        if p2:
            validate_password(p2)
        return p2


class CustomRoleForm(forms.ModelForm):
    """فرم ایجاد نقش سفارشی"""

    class Meta:
        model = Role
        fields = ('code', 'name', 'base_role')
        labels = {'code': 'کد نقش (لاتین، حداکثر ۲۰ کاراکتر)', 'name': 'نام نقش'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['base_role'].choices = [
            (code, label) for code, label in all_roles()
            if code in dict(User.ROLE_CHOICES)
        ]

    def clean_code(self):
        code = self.cleaned_data['code'].strip().lower()
        if code in dict(User.ROLE_CHOICES):
            raise forms.ValidationError('این کد برای نقش‌های استاندارد رزرو شده است.')
        if Role.objects.filter(code=code).exists():
            raise forms.ValidationError('نقشی با این کد وجود دارد.')
        if not code.replace('_', '').isalnum():
            raise forms.ValidationError('کد نقش فقط شامل حروف لاتین، عدد و _ باشد.')
        return code


class SystemRuleForm(forms.ModelForm):
    """فرم قوانین سراسری سیستم"""

    class Meta:
        model = SystemRule
        fields = (
            'enforce_module_locks', 'lock_all_modules', 'enforce_quotas',
            'default_daily_limit', 'wallet_enabled',
        )


class IssuanceQuotaForm(forms.ModelForm):
    """فرم سهمیه صدور بارنامه"""

    class Meta:
        model = IssuanceQuota
        fields = ('scope', 'role', 'user', 'period', 'max_count', 'is_active', 'note')
        labels = {
            'max_count': 'حداکثر تعداد مجاز (0 = ممنوعیت کامل)',
            'note': 'توضیح',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'] = forms.ChoiceField(
            choices=[('', '---------')] + all_roles(), required=False,
            label='نقش')
        self.fields['user'].queryset = User.objects.all().order_by('username')
