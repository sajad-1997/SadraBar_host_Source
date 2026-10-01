from django import forms
from django.utils import timezone

from .models import Customer


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = '__all__'
        exclude = ['created_by', 'created_by_role', 'updated_by', 'updated_by_role']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام و نام خانوادگی'}),
            'national_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'کد ملی'}),
            'postal': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'کد پستی'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'شماره تلفن'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'آدرس', 'rows': 3}),
            'phone2': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'شماره تلفن دوم'}),
            'caption': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'توضیحات', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].required = True
        self.fields['address'].required = True

    def clean_national_id(self):
        """بررسی تکراری نبودن کد ملی"""
        national_id = self.cleaned_data.get('national_id')
        if national_id:
            # بررسی وجود مشتری با همان کد ملی
            existing = Customer.objects.filter(national_id=national_id)
            if self.instance.pk:
                # در حالت ویرایش، مشتری فعلی را از جستجو حذف کن
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise forms.ValidationError('مشتری با این کد ملی قبلاً ثبت شده است. لطفاً کد ملی دیگری وارد کنید.')
        return national_id

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
