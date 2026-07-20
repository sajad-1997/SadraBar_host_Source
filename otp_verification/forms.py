from django import forms
import re

class PhoneNumberForm(forms.Form):
    phone_number = forms.CharField(
        max_length=11,
        label="شماره موبایل",
        widget=forms.TextInput(attrs={'placeholder': '09xxxxxxxxx'})
    )

    def clean_phone_number(self):
        phone = self.cleaned_data['phone_number']
        if not re.match(r'^09[0-9]{9}$', phone):
            raise forms.ValidationError("شماره موبایل باید با 09 شروع و 11 رقم باشد")
        return phone

class OTPVerificationForm(forms.Form):
    phone_number = forms.CharField(max_length=11)
    code = forms.CharField(max_length=6, label="کد تأیید")

    def clean_code(self):
        code = self.cleaned_data['code']
        if not code.isdigit() or len(code) != 6:
            raise forms.ValidationError("کد باید ۶ رقم باشد")
        return code