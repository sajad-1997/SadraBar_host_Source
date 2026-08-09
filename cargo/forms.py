from django import forms
from .models import Cargo


class CargoForm(forms.ModelForm):
    class Meta:
        model = Cargo
        fields = '__all__'
        exclude = ['created_by', 'created_by_role', 'updated_by', 'updated_by_role']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام محموله'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'وزن/حجم'}),
            'package_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نوع بسته بندی'}),
            'number_of_packaging': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'تعداد بسته بندی'}),
            'origin': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'مبدأ بارگیری'}),
            'destination': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'مقصد تخلیه'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].required = True
        self.fields['weight'].required = True
        self.fields['origin'].required = True
        self.fields['destination'].required = True
