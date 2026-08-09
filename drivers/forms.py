from django import forms
from datetime import datetime
import jdatetime
from django.utils import timezone

from .models import Driver
from issuance.utils import persian_to_english_numbers, persian_to_gregorian


class PersianNumberFormMixin:
    """تبدیل اعداد فارسی به انگلیسی در فیلدهای عددی"""
    
    def clean(self):
        cleaned_data = super().clean()
        numeric_fields = getattr(self, 'numeric_fields', [])
        for field in numeric_fields:
            value = cleaned_data.get(field)
            if value and isinstance(value, str):
                cleaned_data[field] = persian_to_english_numbers(value)
        return cleaned_data


class DriverForm(PersianNumberFormMixin, forms.ModelForm):
    numeric_fields = ['national_id', 'certificate', 'phone', 'phone2']

    birth_date = forms.CharField(
        error_messages={'required': 'تاریخ تولد نمی‌تواند خالی باشد.'},
        widget=forms.TextInput(attrs={
            'class': 'form-control date-picker',
            'placeholder': 'تاریخ تولد',
            'autocomplete': 'off'
        })
    )

    certificate_date = forms.CharField(
        error_messages={'required': 'تاریخ صدور گواهینامه نمی‌تواند خالی باشد.'},
        widget=forms.TextInput(attrs={
            'class': 'form-control date-picker',
            'placeholder': 'تاریخ صدور گواهینامه',
            'autocomplete': 'off'
        })
    )

    insurance_policy_expiry = forms.CharField(
        error_messages={'required': 'تاریخ انقضاء بیمه نامه نمی‌تواند خالی باشد.'},
        widget=forms.TextInput(attrs={
            'class': 'form-control date-picker',
            'placeholder': 'تاریخ انقضاء بیمه نامه',
            'autocomplete': 'off'
        })
    )

    name = forms.CharField(
        required=True,
        error_messages={'required': 'نام و نام خانوادگی الزامی است.'},
        widget=forms.TextInput(attrs={'class': 'form-control',
                                      'placeholder': 'نام و نام خانوادگی'})
    )

    national_id = forms.CharField(
        required=True,
        error_messages={'required': 'کد ملی الزامی است.'},
        widget=forms.TextInput(attrs={'class': 'form-control',
                                      'placeholder': 'کد ملی'})
    )

    certificate = forms.CharField(
        required=True,
        error_messages={'required': 'شماره گواهی نامه الزامی است.'},
        widget=forms.TextInput(attrs={'class': 'form-control',
                                      'placeholder': 'شماره گواهی نامه'})
    )

    phone = forms.CharField(
        required=True,
        error_messages={'required': 'شماره تلفن الزامی است.'},
        widget=forms.TextInput(attrs={'class': 'form-control',
                                      'placeholder': 'شماره تلفن'})
    )

    class Meta:
        model = Driver
        fields = '__all__'
        exclude = ['created_by', 'created_by_role', 'updated_by', 'updated_by_role']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # اگر instance وجود دارد، تاریخ‌ها را به Jalali رشته‌ای تبدیل کن
        instance = kwargs.get('instance')
        if instance:
            if instance.birth_date:
                jalali_birth = jdatetime.date.fromgregorian(date=instance.birth_date)
                self.fields['birth_date'].initial = f"{jalali_birth.year}/{jalali_birth.month:02}/{jalali_birth.day:02}"
            if instance.certificate_date:
                jalali_cert = jdatetime.date.fromgregorian(date=instance.certificate_date)
                self.fields[
                    'certificate_date'].initial = f"{jalali_cert.year}/{jalali_cert.month:02}/{jalali_cert.day:02}"
            if instance.insurance_policy_expiry:
                jalali_cert = jdatetime.date.fromgregorian(date=instance.insurance_policy_expiry)
                self.fields[
                    'insurance_policy_expiry'].initial = f"{jalali_cert.year}/{jalali_cert.month:02}/{jalali_cert.day:02}"

    def clean_birth_date(self):
        data = self.cleaned_data.get('birth_date')
        if data:
            g_date = persian_to_gregorian(data)
            if g_date is None:
                raise forms.ValidationError("تاریخ تولد نامعتبر است")
            return g_date
        return None

    def clean_certificate_date(self):
        data = self.cleaned_data.get('certificate_date')
        if data:
            g_date = persian_to_gregorian(data)
            if g_date is None:
                raise forms.ValidationError("تاریخ صدور گواهینامه نامعتبر است")
            return g_date
        return None

    def clean_insurance_policy_expiry(self):
        data = self.cleaned_data.get('insurance_policy_expiry')
        if data:
            g_date = persian_to_gregorian(data)
            if g_date is None:
                raise forms.ValidationError("تاریخ اعتبار بیمه نامه نامعتبر است")
            return g_date
        return None
