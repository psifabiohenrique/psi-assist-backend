from django import forms
from .models import PsyRecord

class PsyRecordForm(forms.ModelForm):
    class Meta:
        model = PsyRecord
        fields = ['content', 'date']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 6})
        }