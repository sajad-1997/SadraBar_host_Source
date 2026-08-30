import logging
from datetime import datetime, time

import jdatetime
from django import forms
from django.utils import timezone

from .models import Customer, Driver, Vehicle, Cargo, Caption, Bijak
from .utils import persian_to_english_numbers, persian_to_gregorian

logger = logging.getLogger(__name__)


# 🔹 کلاس پایه برای فرم‌ها (اعمال فقط روی فیلدهای مشخص عددی)
class PersianNumberFormMixin:
    """
    تبدیل اعداد فارسی به انگلیسی در فیلدهای عددی
    """
    numeric_fields = []  # لیست فیلدهای عددی باید در کلاس‌های فرزند تعریف شود

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # تنظیم widget برای فیلدهای عددی به صورت text برای پشتیبانی از جداکننده
        for field_name in self.numeric_fields:
            if field_name in self.fields:
                field = self.fields[field_name]
                # اضافه کردن ویژگی‌های HTML برای ورودی متنی با قابلیت عدد
                if hasattr(field, 'widget'):
                    attrs = field.widget.attrs or {}
                    attrs.update({
                        'autocomplete': 'off',
                        'class': attrs.get('class', '') + ' currency-field',
                        'maxlength': '20',  # اجازه تایپ تا 20 کاراکتر (با کاما)
                    })
                    field.widget.attrs = attrs

    def clean(self):
        cleaned_data = super().clean()
        for field in self.numeric_fields:
            value = cleaned_data.get(field)
            if value and isinstance(value, str):
                # حذف جداکننده‌ها و تبدیل اعداد فارسی به انگلیسی
                cleaned_value = value.replace(',', '').replace('٬', '')
                cleaned_data[field] = persian_to_english_numbers(cleaned_value)
            elif value is not None and not isinstance(value, (int, float)):
                # اگر مقدار از نوع دیگری است، سعی می‌کنیم به عدد تبدیل کنیم
                try:
                    cleaned_value = str(value).replace(',', '').replace('٬', '')
                    cleaned_data[field] = int(persian_to_english_numbers(cleaned_value))
                except (ValueError, TypeError):
                    pass
        return cleaned_data


class CustomerForm(PersianNumberFormMixin, forms.ModelForm):
    numeric_fields = ['national_id', 'postal', 'phone']

    class Meta:
        model = Customer
        fields = '__all__'
        exclude = ['created_by', 'created_by_role', 'updated_by', 'updated_by_role']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # مشخص کردن فیلدهای الزامی در فرم
        self.fields['name'].required = True
        # self.fields['national_id'].required = True
        # self.fields['postal'].required = True
        self.fields['address'].required = True

    # اعتبارسنجی فیلدهایی که باید کامل شوند
    def clean(self):
        cleaned_data = super().clean()

        required_fields = ['name', 'address']
        errors = {}

        for f in required_fields:
            if not cleaned_data.get(f):
                errors[f] = "پر کردن این فیلد الزامی است."

        if errors:
            raise forms.ValidationError(errors)

        return cleaned_data


class DriverForm(PersianNumberFormMixin, forms.ModelForm):
    numeric_fields = ['national_id', 'certificate', 'driver_smart_card', 'phone', 'phone2', 'phone3']

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

        # اگر instance وجود دارد، تاریخ‌ها را به Jalali رشته‌ای تبدیل کن
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
            # تبدیل اعداد فارسی به انگلیسی قبل از پردازش
            data = persian_to_english_numbers(data)
            g_date = persian_to_gregorian(data)
            if g_date is None:
                raise forms.ValidationError("تاریخ تولد نامعتبر است")
            return g_date
        return None

    def clean_certificate_date(self):
        data = self.cleaned_data.get('certificate_date')
        if data:
            # تبدیل اعداد فارسی به انگلیسی قبل از پردازش
            data = persian_to_english_numbers(data)
            g_date = persian_to_gregorian(data)
            if g_date is None:
                raise forms.ValidationError("تاریخ صدور گواهینامه نامعتبر است")
            return g_date
        return None

class VehicleForm(PersianNumberFormMixin, forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = [
            'driver',
            'type',
            # 'room_model',
            # 'Animal_feed_license',
            # 'veterinary_code',
            'license_plate_two_digit',
            'license_plate_alphabet',
            'license_plate_three_digit',
            'license_plate_series',
            'vehicle_smart_card',
        ]
        widgets = {
            'driver': forms.Select(attrs={'class': 'form-control'}),
            'type': forms.Select(attrs={'class': 'form-control'}),
            # 'room_model': forms.Select(attrs={'class': 'form-control'}),
            # 'Animal_feed_license': forms.Select(attrs={'class': 'form-control', 'id': 'id_animal_license'}),
            # 'veterinary_code': forms.TextInput(attrs={
            #     'class': 'form-control',
            #     'id': 'id_veterinary_code',
            #     'maxlength': '7',
            #     'inputmode': 'numeric',
            #     'pattern': '[0-9]*',
            #     'disabled': 'disabled'
            # }),
        }

    # def clean(self):
    #     cleaned_data = super().clean()
    #     license_status = cleaned_data.get('Animal_feed_license')
    #     vet_code = cleaned_data.get('veterinary_code')
    #
    #     if license_status == 'Yes' and not vet_code:
    #         self.add_error(
    #             'veterinary_code',
    #             'در صورت داشتن مجوز خوراک دام، وارد کردن کد دامپزشکی الزامی است.'
    #         )
    #
    #     if license_status == 'No':
    #         cleaned_data['veterinary_code'] = ''
    #
    #     return cleaned_data


class CargoForm(PersianNumberFormMixin, forms.ModelForm):
    numeric_fields = ['weight', 'number_of_packaging', ]

    class Meta:
        model = Cargo
        fields = '__all__'
        exclude = ['created_by', 'created_by_role', 'updated_by', 'updated_by_role']


class CaptionForm(forms.ModelForm):
    class Meta:
        model = Caption
        fields = '__all__'

    selected_caption = forms.ModelMultipleChoiceField(
        queryset=Caption.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        # label="انتخاب توضیحات آماده"
    )
    custom_caption = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 3}),
        required=False,
        label="توضیحات دستی"
    )


class ShipmentForm(PersianNumberFormMixin, forms.ModelForm):
    numeric_fields = ['total_fare', 'value', 'insurance', 'loading_fee', 'unloading_fee', 'scale_fee', 'freight']
    
    # =========================
    # تاریخ و ساعت صدور
    # =========================
    issuance_date = forms.CharField(
        label="تاریخ صدور بارنامه",
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'date-picker form-control',
            'placeholder': 'سال/ماه/روز'
        })
    )

    issuance_time = forms.CharField(
        label="ساعت صدور بارنامه",
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'time-picker form-control',
            'placeholder': 'ساعت:دقیقه:ثانیه'
        })
    )

    # =========================
    # توضیحات
    # =========================
    # selected_caption = forms.ModelChoiceField(
    #     queryset=Caption.objects.all().order_by('-id'),
    #     required=False,
    #     label="توضیح آماده",
    #     widget=forms.Select(attrs={
    #         'class': 'form-select'
    #     })
    # )

    # custom_caption = forms.CharField(
    #     required=False,
    #     label="توضیح دستی",
    #     widget=forms.Textarea(attrs={
    #         'rows': 3,
    #         'class': 'form-control',
    #         'placeholder': 'اگر توضیح خاصی دارید، اینجا بنویسید...'
    #     })
    # )

    # =========================
    # Meta
    # =========================
    class Meta:
        model = Bijak
        fields = (
            'total_fare',
            'value',
            'insurance',
            'loading_fee',
            'unloading_fee',
            'scale_fee',
            'freight',
            # 'selected_caption',
            # 'custom_caption',
        )
        widgets = {
            'total_fare': forms.TextInput(attrs={'class': 'form-control'}),
            'value': forms.TextInput(attrs={'class': 'form-control'}),
            'insurance': forms.TextInput(attrs={'class': 'form-control'}),
            'loading_fee': forms.TextInput(attrs={'class': 'form-control'}),
            'unloading_fee': forms.TextInput(attrs={'class': 'form-control'}),
            'scale_fee': forms.TextInput(attrs={'class': 'form-control'}),
            'freight': forms.TextInput(attrs={'class': 'form-control'}),
        }

    # =========================
    # Clean
    # =========================
    # def clean(self):
    #     cleaned_data = super().clean()

    #     raw_date = cleaned_data.get('issuance_date')
    #     raw_time = cleaned_data.get('issuance_time')

    #     if not raw_date or not raw_time:
    #         raise forms.ValidationError("تاریخ و ساعت صدور الزامی است.")

    #     try:
    #         # تبدیل اعداد فارسی به انگلیسی (اگر تابع داری)
    #         date_str = persian_to_english_numbers(raw_date).strip()
    #         time_str = persian_to_english_numbers(raw_time).strip()

    #         # تاریخ شمسی
    #         j_date = jdatetime.date.fromisoformat(
    #             date_str.replace('/', '-')
    #         )

    #         # ساعت
    #         parts = time_str.split(':')
    #         if len(parts) not in (2, 3):
    #             raise ValueError("Invalid time format")

    #         hour = int(parts[0])
    #         minute = int(parts[1])
    #         second = int(parts[2]) if len(parts) == 3 else 0

    #         issuance_time_obj = time(hour, minute, second)

    #         # datetime نهایی میلادی
    #         cleaned_data['issuance_datetime'] = datetime.combine(
    #             j_date.togregorian(),
    #             issuance_time_obj
    #         )

    #     except Exception:
    #         logger.exception(
    #             "Invalid issuance date/time | date=%s time=%s",
    #             raw_date, raw_time
    #         )
    #         raise forms.ValidationError(
    #             "تاریخ یا ساعت وارد شده معتبر نیست."
    #         )

    #     return cleaned_data
    
    def clean(self):
        cleaned_data = super().clean()

        raw_date = cleaned_data.get('issuance_date')
        raw_time = cleaned_data.get('issuance_time')

        if not raw_date or not raw_time:
            raise forms.ValidationError("تاریخ و ساعت صدور الزامی است.")

        try:
            # تبدیل اعداد فارسی به انگلیسی
            date_str = persian_to_english_numbers(raw_date).strip()
            time_str = persian_to_english_numbers(raw_time).strip()

            # جایگزینی / با - برای سازگاری با fromisoformat
            j_date = jdatetime.date.fromisoformat(date_str.replace('/', '-'))

            parts = time_str.split(':')
            if len(parts) not in (2, 3):
                raise ValueError("Invalid time format")

            hour = int(parts[0])
            minute = int(parts[1])
            second = int(parts[2]) if len(parts) == 3 else 0

            issuance_time_obj = time(hour, minute, second)

            cleaned_data['issuance_datetime'] = datetime.combine(
                j_date.togregorian(),
                issuance_time_obj
            )

        except Exception as e:
            # لاگ خطا به جای print
            logger.error("ERROR in ShipmentForm.clean: %s", e)
            logger.error("raw_date=%r (type=%s)", raw_date, type(raw_date))
            logger.error("raw_time=%r (type=%s)", raw_time, type(raw_time))
            logger.exception("Invalid issuance date/time | date=%s time=%s", raw_date, raw_time)

            raise forms.ValidationError("تاریخ یا ساعت وارد شده معتبر نیست.")

        return cleaned_data
