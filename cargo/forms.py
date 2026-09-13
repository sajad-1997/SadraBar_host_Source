from django import forms
from .models import Cargo, City


class CargoForm(forms.ModelForm):
    origin_display = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'مبدأ بارگیری (نام شهر یا استان)',
        'autocomplete': 'off'
    }))
    destination_display = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'مقصد تخلیه (نام شهر یا استان)',
        'autocomplete': 'off'
    }))
    origin = forms.ModelChoiceField(queryset=City.objects.all(), required=False, widget=forms.HiddenInput())
    destination = forms.ModelChoiceField(queryset=City.objects.all(), required=False, widget=forms.HiddenInput())

    # فیلدهای عددی به صورت متنی دریافت می‌شوند تا کاربر بتواند کاما و اعداد فارسی تایپ کند
    # (دقیقاً مثل فیلد کل کرایه در فرم صدور بارنامه)
    weight = forms.CharField(
        label="وزن/حجم",
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control currency-field',
            'placeholder': 'وزن/حجم (کیلوگرم)',
            'inputmode': 'numeric',
            'autocomplete': 'off',
        })
    )
    weight_2 = forms.CharField(
        label="وزن/حجم دوم",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control currency-field',
            'placeholder': 'وزن/حجم دوم (اختیاری)',
            'inputmode': 'numeric',
            'autocomplete': 'off',
        })
    )
    number_of_packaging = forms.CharField(
        label="تعداد بسته بندی",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control currency-field',
            'placeholder': 'تعداد بسته بندی',
            'inputmode': 'numeric',
            'autocomplete': 'off',
        })
    )

    class Meta:
        model = Cargo
        fields = '__all__'
        exclude = ['created_by', 'created_by_role', 'updated_by', 'updated_by_role']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام محموله'}),
            'package_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نوع بسته بندی'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].required = True
        self.fields['weight'].required = True
        self.fields['weight_2'].required = False
        self.fields['origin'].required = True
        self.fields['destination'].required = True
        
        # مقداردهی اولیه فیلدهای نمایش بر اساس داده‌های موجود
        if self.instance and hasattr(self.instance, 'origin') and self.instance.origin:
            self.fields['origin_display'].initial = f"{self.instance.origin.province.name} - {self.instance.origin.name}"
        if self.instance and hasattr(self.instance, 'destination') and self.instance.destination:
            self.fields['destination_display'].initial = f"{self.instance.destination.province.name} - {self.instance.destination.name}"
        
        # اضافه کردن کلاس is-invalid به فیلدهایی که خطا دارند
        if hasattr(self, 'errors'):
            for field_name, errors in self.errors.items():
                if field_name in self.fields:
                    existing_class = self.fields[field_name].widget.attrs.get('class', '')
                    if 'is-invalid' not in existing_class:
                        self.fields[field_name].widget.attrs['class'] = f"{existing_class} is-invalid".strip()

    @staticmethod
    def _normalize_number(value):
        """تبدیل اعداد فارسی/عربی به انگلیسی و حذف تمام جداکننده‌ها (مثل فیلد کرایه)"""
        if value is None:
            return None
        persian_nums = "۰۱۲۳۴۵۶۷۸۹"
        arabic_nums = "٠١٢٣٤٥٦٧٨٩"
        english_nums = "0123456789"
        translation_table = str.maketrans(persian_nums + arabic_nums, english_nums + english_nums)
        return (
            str(value)
            .replace(',', '')
            .replace('٬', '')
            .replace('،', '')
            .translate(translation_table)
            .strip()
        )

    def clean_weight(self):
        weight = self.cleaned_data.get('weight')
        if weight in (None, ''):
            return weight
        weight_str = self._normalize_number(weight)
        if not weight_str:
            raise forms.ValidationError('لطفاً یک عدد معتبر وارد کنید')
        try:
            value = float(weight_str)
        except (ValueError, TypeError):
            raise forms.ValidationError('لطفاً یک عدد معتبر وارد کنید')
        # مدل از IntegerField استفاده می‌کند؛ وزن اعشاری مجاز نیست
        if not value.is_integer():
            raise forms.ValidationError('وزن باید عدد صحیح باشد')
        return int(value)

    def clean_weight_2(self):
        weight_2 = self.cleaned_data.get('weight_2')
        # فیلد اختیاری است؛ مقدار خالی باید صفر باشد (فیلد مدل NOT NULL است)
        if weight_2 in (None, ''):
            return 0
        weight_2_str = self._normalize_number(weight_2)
        if not weight_2_str:
            return 0
        try:
            value = float(weight_2_str)
        except (ValueError, TypeError):
            raise forms.ValidationError('لطفاً یک عدد معتبر وارد کنید')
        # مدل از IntegerField استفاده می‌کند؛ وزن اعشاری مجاز نیست
        if not value.is_integer():
            raise forms.ValidationError('وزن باید عدد صحیح باشد')
        return int(value)

    def clean_number_of_packaging(self):
        number_of_packaging = self.cleaned_data.get('number_of_packaging')
        # فیلد اختیاری و nullable است؛ مقدار خالی باید None باشد نه رشته خالی
        if number_of_packaging in (None, ''):
            return None
        number_str = self._normalize_number(number_of_packaging)
        if not number_str:
            return None
        try:
            value = float(number_str)
            if not value.is_integer():
                raise forms.ValidationError('تعداد بسته بندی باید عدد صحیح باشد')
            return int(value)
        except (ValueError, TypeError):
            raise forms.ValidationError('لطفاً یک عدد معتبر وارد کنید')

    def clean(self):
        cleaned_data = super().clean()
        
        # اولویت با فیلد مخفی است که توسط جاوااسکریپت پر می‌شود
        origin = cleaned_data.get('origin')
        destination = cleaned_data.get('destination')
        origin_display = cleaned_data.get('origin_display')
        destination_display = cleaned_data.get('destination_display')
        
        # اگر فیلد مخفی مقدار دارد، از آن استفاده کن
        if not origin and origin_display:
            # استخراج شهر از فرمت "استان - شهر"
            if '-' in origin_display:
                parts = origin_display.split('-')
                city_name = parts[-1].strip()
                province_name = '-'.join(parts[:-1]).strip()
                
                try:
                    city = City.objects.get(name=city_name, province__name=province_name)
                    cleaned_data['origin'] = city
                except City.DoesNotExist:
                    # اگر شهر پیدا نشد، سعی کن فقط با نام شهر پیدا کنی
                    try:
                        city = City.objects.get(name=city_name)
                        cleaned_data['origin'] = city
                    except City.DoesNotExist:
                        self.add_error('origin_display', 'شهر انتخاب شده معتبر نیست')
            else:
                # اگر فرمت صحیح نیست، سعی کن با نام شهر پیدا کنی
                try:
                    city = City.objects.get(name=origin_display.strip())
                    cleaned_data['origin'] = city
                except City.DoesNotExist:
                    self.add_error('origin_display', 'شهر انتخاب شده معتبر نیست')
        
        # اگر فیلد مخفی مقدار دارد، از آن استفاده کن
        if not destination and destination_display:
            # استخراج شهر از فرمت "استان - شهر"
            if '-' in destination_display:
                parts = destination_display.split('-')
                city_name = parts[-1].strip()
                province_name = '-'.join(parts[:-1]).strip()
                
                try:
                    city = City.objects.get(name=city_name, province__name=province_name)
                    cleaned_data['destination'] = city
                except City.DoesNotExist:
                    # اگر شهر پیدا نشد، سعی کن فقط با نام شهر پیدا کنی
                    try:
                        city = City.objects.get(name=city_name)
                        cleaned_data['destination'] = city
                    except City.DoesNotExist:
                        self.add_error('destination_display', 'شهر انتخاب شده معتبر نیست')
            else:
                # اگر فرمت صحیح نیست، سعی کن با نام شهر پیدا کنی
                try:
                    city = City.objects.get(name=destination_display.strip())
                    cleaned_data['destination'] = city
                except City.DoesNotExist:
                    self.add_error('destination_display', 'شهر انتخاب شده معتبر نیست')
        
        # بررسی اینکه فیلدهای مبدا و مقصد پر شده باشند
        if not cleaned_data.get('origin'):
            self.add_error('origin_display', 'لطفاً مبدا بارگیری را انتخاب کنید')
        if not cleaned_data.get('destination'):
            self.add_error('destination_display', 'لطفاً مقصد تخلیه را انتخاب کنید')
        
        return cleaned_data
