import logging
from datetime import datetime, time
import jdatetime
from django import forms

from captions.models import Caption
from .models import Bijak

logger = logging.getLogger(__name__)


class PersianNumberFormMixin:
    """
    میکسین برای تبدیل خودکار اعداد فارسی/عربی به انگلیسی و حذف جداکننده‌ها (کاما)
    """
    numeric_fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.numeric_fields:
            if field_name in self.fields:
                field = self.fields[field_name]
                attrs = field.widget.attrs or {}
                attrs.update({
                    'autocomplete': 'off',
                    'inputmode': 'numeric',  # نمایش کیبورد عددی در موبایل
                    'class': (attrs.get('class', '') + ' currency-field').strip(),
                })
                field.widget.attrs = attrs

    def clean(self):
        cleaned_data = super().clean()

        # جدول تبدیل اعداد فارسی و عربی به انگلیسی
        persian_nums = "۰۱۲۳۴۵۶۷۸۹"
        arabic_nums = "٠١٢٣٤٥٦٧٨٩"
        english_nums = "0123456789"
        translation_table = str.maketrans(persian_nums + arabic_nums, english_nums + english_nums)

        for field_name in self.numeric_fields:
            if field_name not in cleaned_data:
                continue

            value = cleaned_data.get(field_name)

            # اگر مقدار قبلاً عدد است (مثلاً در حالت ویرایش)، کاری نکن
            if isinstance(value, (int, float)):
                continue

            if value is not None:
                try:
                    val_str = str(value)

                    # ۱. حذف تمام انواع کاما و جداکننده‌ها (انگلیسی، عربی و فارسی)
                    val_str = val_str.replace(',', '').replace('٬', '').replace('،', '').strip()

                    # ۲. تبدیل اعداد به انگلیسی
                    val_str = val_str.translate(translation_table)

                    # ۳. بررسی خالی بودن پس از پاکسازی
                    if not val_str:
                        self.add_error(field_name, "این فیلد نمی‌تواند خالی باشد")
                        continue

                    # ۴. تبدیل نهایی به float (سازگار با DecimalField و FloatField مدل)
                    cleaned_data[field_name] = float(val_str)

                except (ValueError, TypeError):
                    self.add_error(field_name, "لطفاً یک عدد معتبر وارد کنید")

        return cleaned_data


class ShipmentForm(PersianNumberFormMixin, forms.ModelForm):
    # تعریف فیلدهایی که باید به صورت متنی دریافت شوند تا کاربر بتواند کاما و عدد فارسی تایپ کند
    total_fare = forms.CharField(label="کرایه پرداختی در مقصد", required=True,
                                 widget=forms.TextInput(attrs={'class': 'form-control'}))
    value = forms.CharField(label="ارزش محموله", required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    insurance = forms.CharField(label="مبلغ بیمه", required=True,
                                widget=forms.TextInput(attrs={'class': 'form-control'}))
    loading_fee = forms.CharField(label="هزینه بارگیری", required=False,
                                  widget=forms.TextInput(attrs={'class': 'form-control'}))
    unloading_fee = forms.CharField(label="هزینه تخلیه", required=False,
                                    widget=forms.TextInput(attrs={'class': 'form-control'}))
    scale_fee = forms.CharField(label="هزینه باسکول", required=False,
                                widget=forms.TextInput(attrs={'class': 'form-control'}))
    freight = forms.CharField(label="کل کرایه", required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))

    issuance_date = forms.CharField(
        label="تاریخ صدور بارنامه",
        required=True,
        widget=forms.TextInput(attrs={'class': 'date-picker form-control', 'placeholder': 'سال/ماه/روز'})
    )

    issuance_time = forms.CharField(
        label="ساعت صدور بارنامه",
        required=True,
        widget=forms.TextInput(attrs={'class': 'time-picker form-control', 'placeholder': 'ساعت:دقیقه:ثانیه'})
    )

    numeric_fields = [
        'total_fare', 'value', 'insurance',
        'loading_fee', 'unloading_fee', 'scale_fee', 'freight'
    ]

    class Meta:
        model = Bijak
        # نکته حیاتی: فیلدها باید در اینجا لیست شوند تا ModelForm آن‌ها را به درستی به مدل متصل کند
        fields = [
            'total_fare', 'value', 'insurance',
            'loading_fee', 'unloading_fee', 'scale_fee', 'freight'
        ]

    def clean(self):
        cleaned_data = super().clean()

        raw_date = cleaned_data.get('issuance_date')
        raw_time = cleaned_data.get('issuance_time')

        if not raw_date or not raw_time:
            raise forms.ValidationError("تاریخ و ساعت صدور الزامی است.")

        try:
            # تبدیل اعداد فارسی به انگلیسی برای تاریخ و ساعت
            persian_nums = "۰۱۲۳۴۵۶۷۸۹"
            english_nums = "0123456789"
            translation_table = str.maketrans(persian_nums, english_nums)

            date_str = str(raw_date).translate(translation_table).strip()
            time_str = str(raw_time).translate(translation_table).strip()

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
            logger.error("ERROR in ShipmentForm.clean: %s", e)
            logger.error("raw_date=%r, raw_time=%r", raw_date, raw_time)
            raise forms.ValidationError("تاریخ یا ساعت وارد شده معتبر نیست. لطفاً فرمت صحیح را رعایت کنید.")

        return cleaned_data
