from django import forms

from customers.models import Customer

from .models import DriverAttendance, RateCard, ServiceRequest


# =========================================================
# فرم ثبت/ویرایش مشتری شهری
# (اطلاعات در جدول Customer ماژول customers ذخیره می‌شود)
# =========================================================
class UrbanCustomerForm(forms.ModelForm):
    profile_note = forms.CharField(
        required=False, label='یادداشت داخلی شهری',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2,
                                     'placeholder': 'یادداشت مخصوص بخش رانندگان شهری'}))

    class Meta:
        model = Customer
        fields = ['name', 'national_id', 'phone', 'phone2', 'postal', 'address', 'caption']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام و نام خانوادگی'}),
            'national_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'کد ملی'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'شماره تلفن'}),
            'phone2': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'شماره تلفن دوم'}),
            'postal': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'کد پستی'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'آدرس'}),
            'caption': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'توضیحات'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].required = True
        self.fields['address'].required = True

    def clean(self):
        cleaned_data = super().clean()
        errors = {}
        for field in ('name', 'address'):
            if not cleaned_data.get(field):
                errors[field] = 'پر کردن این فیلد الزامی است.'
        if errors:
            raise forms.ValidationError(errors)
        return cleaned_data


# =========================================================
# فرم درخواست سرویس مشتری شهری
# =========================================================
class UrbanServiceRequestForm(forms.ModelForm):
    class Meta:
        model = ServiceRequest
        fields = [
            'customer', 'service', 'rate_card',
            'origin_address', 'destination_address',
            'origin_lat', 'origin_lng', 'destination_lat', 'destination_lng',
            'requested_time', 'distance_km',
            'passenger_name', 'passenger_phone', 'note',
        ]
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'service': forms.Select(attrs={'class': 'form-select'}),
            'rate_card': forms.Select(attrs={'class': 'form-select'}),
            'origin_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2,
                                                    'placeholder': 'آدرس دقیق مبدأ'}),
            'destination_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2,
                                                         'placeholder': 'آدرس دقیق مقصد'}),
            'origin_lat': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'origin_lng': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'destination_lat': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'destination_lng': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'requested_time': forms.TextInput(attrs={'class': 'form-control datepicker-input',
                                                     'placeholder': '1404/06/27 14:30'}),
            'distance_km': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1',
                                                    'placeholder': 'مثال: 12.5'}),
            'passenger_name': forms.TextInput(attrs={'class': 'form-control'}),
            'passenger_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # مشتری جداگانه از طریق فرم/جستجو انتخاب می‌شود (الزامی بودن آن در ویو بررسی می‌شود)
        self.fields['customer'].required = False
        self.fields['customer'].empty_label = '— انتخاب مشتری —'
        self.fields['origin_address'].required = True
        self.fields['destination_address'].required = True


# =========================================================
# فرم نرخ‌نامه
# =========================================================
class RateCardForm(forms.ModelForm):
    class Meta:
        model = RateCard
        fields = ['title', 'service', 'vehicle_type', 'base_fare', 'per_km_fare',
                  'minimum_fare', 'commission_percent', 'description', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'service': forms.Select(attrs={'class': 'form-select'}),
            'vehicle_type': forms.Select(attrs={'class': 'form-select'}),
            'base_fare': forms.NumberInput(attrs={'class': 'form-control'}),
            'per_km_fare': forms.NumberInput(attrs={'class': 'form-control'}),
            'minimum_fare': forms.NumberInput(attrs={'class': 'form-control'}),
            'commission_percent': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


# =========================================================
# فرم محاسبه گر کرایه
# =========================================================
class FareCalculatorForm(forms.Form):
    rate_card = forms.ModelChoiceField(
        queryset=RateCard.objects.filter(is_active=True),
        label='نرخ‌نامه', empty_label='— انتخاب نرخ‌نامه —',
        widget=forms.Select(attrs={'class': 'form-select'}))
    distance_km = forms.FloatField(
        label='مسافت (کیلومتر)', min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1',
                                        'placeholder': 'مثال: 12.5'}))


# =========================================================
# فرم حضور و غیاب
# =========================================================
class DriverAttendanceForm(forms.ModelForm):
    class Meta:
        model = DriverAttendance
        fields = ['driver', 'date', 'status', 'note']
        widgets = {
            'driver': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.TextInput(attrs={'class': 'form-control datepicker-input',
                                           'placeholder': '1404/06/27'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
