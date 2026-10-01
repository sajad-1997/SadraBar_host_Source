from django import forms


class RequestPrintForm(forms.Form):
    waybill_number = forms.CharField(max_length=50, label='شماره بارنامه')


class VerifyOTPForm(forms.Form):
    waybill_number = forms.CharField(max_length=50, widget=forms.HiddenInput)
    otp_code = forms.CharField(max_length=6, label='کد تأیید')
