# patients/forms.py
from django import forms
from .models import Patient

class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ['first_name', 'second_name', 'full_name', 'birth_date']
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
        }

class PatientSummaryForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ['objectives', 'clinical_demand', 'clinical_procedures', 'clinical_analysis', 'clinical_conclusion']
        exclude = ['first_name', 'second_name', 'full_name', 'birth_date']
