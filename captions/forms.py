from django import forms
from .models import Caption


class CaptionForm(forms.ModelForm):
    class Meta:
        model = Caption
        fields = '__all__'
        exclude = ['created_by', 'created_by_role', 'updated_by', 'updated_by_role']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام توضیح'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'محتوای توضیح', 'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['content'].required = True
