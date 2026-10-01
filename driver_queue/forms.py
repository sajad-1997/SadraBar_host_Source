import re

from django import forms
from django.contrib.auth import get_user_model

from .models import QueueStaff
from .utils import normalize_digits

FIELD_ATTRS = {"class": "field", "dir": "rtl"}


class IdentifyForm(forms.Form):
    """مرحله اول: تطابق هویت با سوابق."""
    name = forms.CharField(
        label="نام و نام خانوادگی", max_length=200,
        widget=forms.TextInput(attrs={**FIELD_ATTRS, "placeholder": "مثلا علی رضایی"}))
    phone = forms.CharField(
        label="شماره تماس", max_length=15,
        widget=forms.TextInput(attrs={**FIELD_ATTRS, "inputmode": "tel",
                                      "placeholder": "09xxxxxxxxx"}))

    def clean_name(self):
        return " ".join(self.cleaned_data["name"].split())

    def clean_phone(self):
        phone = normalize_digits(self.cleaned_data["phone"]).strip()
        if not re.match(r"^09\d{9}$", phone):
            raise forms.ValidationError("شماره تماس باید با ۰۹ شروع شده و ۱۱ رقم باشد.")
        return phone


class RegisterForm(forms.Form):
    """ثبت‌نام راننده جدید."""
    name = forms.CharField(
        label="نام و نام خانوادگی", max_length=200,
        widget=forms.TextInput(attrs={**FIELD_ATTRS, "placeholder": "مثلا علی رضایی"}))
    phone = forms.CharField(
        label="شماره تماس فعال", max_length=15,
        widget=forms.TextInput(attrs={**FIELD_ATTRS, "inputmode": "tel",
                                      "placeholder": "09xxxxxxxxx"}))
    certificate = forms.CharField(
        label="شماره گواهینامه", max_length=50,
        widget=forms.TextInput(attrs={**FIELD_ATTRS, "placeholder": "شماره گواهینامه"}))
    national_id = forms.CharField(
        label="کد ملی", max_length=50,
        widget=forms.TextInput(attrs={**FIELD_ATTRS, "placeholder": "کد ملی ۱۰ رقمی"}))

    def clean_name(self):
        return " ".join(self.cleaned_data["name"].split())

    def clean_phone(self):
        phone = normalize_digits(self.cleaned_data["phone"]).strip()
        if not re.match(r"^09\d{9}$", phone):
            raise forms.ValidationError("شماره تماس باید با ۰۹ شروع شده و ۱۱ رقم باشد.")
        return phone

    def clean_certificate(self):
        return normalize_digits(self.cleaned_data["certificate"]).strip()

    def clean_national_id(self):
        national_id = normalize_digits(self.cleaned_data["national_id"]).strip()
        if len(national_id) != 10:
            raise forms.ValidationError("کد ملی باید ۱۰ رقم باشد.")
        return national_id


class StaffUserAddForm(forms.Form):
    """افزودن کاربر مجاز به پنل (فقط توسط مدیریت)."""
    username = forms.CharField(
        label="نام کاربری",
        widget=forms.TextInput(attrs={**FIELD_ATTRS, "placeholder": "username"}))
    role = forms.ChoiceField(
        label="نقش", choices=QueueStaff.Role.choices,
        initial=QueueStaff.Role.STAFF,
        widget=forms.Select(attrs=FIELD_ATTRS))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        user_model = get_user_model()
        try:
            self.user = user_model.objects.get(
                **{user_model.USERNAME_FIELD: username})
        except user_model.DoesNotExist:
            raise forms.ValidationError("کاربری با این نام کاربری یافت نشد.")
        if QueueStaff.objects.filter(user=self.user).exists():
            raise forms.ValidationError("این کاربر قبلا به پنل اضافه شده است.")
        return username
