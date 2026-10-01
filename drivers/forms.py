import jdatetime
from django import forms

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
    numeric_fields = [
        'national_id',
        'certificate',
        'driver_smart_card',
        'phone',
        'phone2',
        'phone3',
    ]

    birth_date = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control date-picker',
            'placeholder': 'تاریخ تولد',
            'autocomplete': 'off'
        })
    )

    certificate_date = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control date-picker',
            'placeholder': 'تاریخ صدور گواهینامه',
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
        fields = [
            'name',
            'national_id',
            'father_name',
            'birth_date',
            'residence',
            'certificate',
            'certificate_date',
            'driver_smart_card',
            'phone',
            'phone2',
            'phone3',
            'address',
        ]
        widgets = {
            'father_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام پدر'}),
            'residence': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'شهر سکونت'}),
            'driver_smart_card': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'شماره هوشمند راننده'}),
            'phone2': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'شماره تلفن دوم'}),
            'phone3': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'شماره تلفن سوم'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'آدرس'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        instance = kwargs.get('instance')
        if instance:
            if instance.birth_date:
                self.fields['birth_date'].initial = self._format_jalali_date(instance.birth_date)
            if instance.certificate_date:
                self.fields['certificate_date'].initial = self._format_jalali_date(instance.certificate_date)

    @staticmethod
    def _format_jalali_date(value):
        if isinstance(value, jdatetime.date):
            jalali_date = value
        else:
            jalali_date = jdatetime.date.fromgregorian(date=value)
        return f"{jalali_date.year}/{jalali_date.month:02}/{jalali_date.day:02}"

    def clean_birth_date(self):
        data = self.cleaned_data.get('birth_date')
        if data:
            data = persian_to_english_numbers(data)
            g_date = persian_to_gregorian(data)
            if g_date is None:
                raise forms.ValidationError("تاریخ تولد نامعتبر است")
            return g_date
        return None

    def clean_certificate_date(self):
        data = self.cleaned_data.get('certificate_date')
        if data:
            data = persian_to_english_numbers(data)
            g_date = persian_to_gregorian(data)
            if g_date is None:
                raise forms.ValidationError("تاریخ صدور گواهینامه نامعتبر است")
            return g_date
        return None
