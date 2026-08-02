from django import forms
import jdatetime
from django.utils import timezone

from .models import Vehicle
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


class VehicleForm(PersianNumberFormMixin, forms.ModelForm):
    numeric_fields = [
        'license_plate_two_digit',
        'license_plate_three_digit',
    ]

    insurance_policy_expiry = forms.CharField(
        error_messages={'required': 'تاریخ انقضاء بیمه نامه نمی‌تواند خالی باشد.'},
        widget=forms.TextInput(attrs={
            'class': 'form-control date-picker',
            'placeholder': 'تاریخ انقضاء بیمه نامه',
            'autocomplete': 'off'
        }),
        required=False
    )

    class Meta:
        model = Vehicle
        fields = [
            'driver',
            'type',
            'room_model',
            'Animal_feed_license',
            'veterinary_code',
            'license_plate_two_digit',
            'license_plate_alphabet',
            'license_plate_three_digit',
            'license_plate_series',
            'vehicle_smart_card',
            'insurance_policy_number',
            'insurance_policy_expiry',
        ]
        widgets = {
            'driver': forms.Select(attrs={'class': 'form-control'}),
            'type': forms.Select(attrs={'class': 'form-control'}),
            'room_model': forms.Select(attrs={'class': 'form-control'}),
            'Animal_feed_license': forms.Select(attrs={'class': 'form-control', 'id': 'id_animal_license'}),
            'veterinary_code': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'id_veterinary_code',
                'maxlength': '7',
                'inputmode': 'numeric',
                'pattern': '[0-9]*',
                'disabled': 'disabled'
            }),
            'license_plate_two_digit': forms.TextInput(attrs={
                'class': 'form-control',
                'maxlength': '2',
                'inputmode': 'numeric',
            }),
            'license_plate_alphabet': forms.TextInput(attrs={
                'class': 'form-control',
                'maxlength': '1',
                'style': 'text-transform: uppercase;',
            }),
            'license_plate_three_digit': forms.TextInput(attrs={
                'class': 'form-control',
                'maxlength': '3',
                'inputmode': 'numeric',
            }),
            'license_plate_series': forms.TextInput(attrs={
                'class': 'form-control',
                'maxlength': '2',
                'inputmode': 'numeric',
            }),
            'vehicle_smart_card': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'insurance_policy_number': forms.TextInput(attrs={
                'class': 'form-control',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # اگر instance وجود دارد، تاریخ بیمه را به Jalali رشته‌ای تبدیل کن
        instance = kwargs.get('instance')
        if instance and instance.insurance_policy_expiry:
            jalali_insurance = jdatetime.date.fromgregorian(date=instance.insurance_policy_expiry)
            self.fields['insurance_policy_expiry'].initial = f"{jalali_insurance.year}/{jalali_insurance.month:02}/{jalali_insurance.day:02}"

    def clean(self):
        cleaned_data = super().clean()
        license_status = cleaned_data.get('Animal_feed_license')
        vet_code = cleaned_data.get('veterinary_code')

        if license_status == 'Yes' and not vet_code:
            self.add_error(
                'veterinary_code',
                'در صورت داشتن مجوز خوراک دام، وارد کردن کد دامپزشکی الزامی است.'
            )

        if license_status == 'No':
            cleaned_data['veterinary_code'] = ''

        return cleaned_data

    def clean_insurance_policy_expiry(self):
        data = self.cleaned_data.get('insurance_policy_expiry')
        if data:
            g_date = persian_to_gregorian(data)
            if g_date is None:
                raise forms.ValidationError("تاریخ اعتبار بیمه نامه نامعتبر است")
            return g_date
        return None
