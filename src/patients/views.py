from django.views.generic import (
    ListView,
    CreateView,
    DetailView,
    UpdateView,
    DeleteView,
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import Patient
from .forms import PatientForm


class PatientListView(LoginRequiredMixin, ListView):
    model = Patient
    template_name = "patients/patient_list.html"
    context_object_name = "patients"

    def get_queryset(self):
        return Patient.objects.filter(user=self.request.user).order_by('full_name')


class PatientCreateView(LoginRequiredMixin, CreateView):
    model = Patient
    form_class = PatientForm
    template_name = 'patients/patient_form.html'
    success_url = reverse_lazy('patients:list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class PatientDetailView(LoginRequiredMixin, DetailView):
    model = Patient
    template_name = "patients/patient_detail.html"
    context_object_name = "patient"

    def get_queryset(self):
        return Patient.objects.filter(user=self.request.user)


class PatientUpdateView(LoginRequiredMixin, UpdateView):
    model = Patient
    form_class = PatientForm
    template_name = "patients/patient_form.html"
    context_object_name = "patient"
    success_url = reverse_lazy("patients:list")

    def get_queryset(self):
        return Patient.objects.filter(user=self.request.user)


class PatientDeleteView(LoginRequiredMixin, DeleteView):
    model = Patient
    template_name = "patients/patient_confirm_delete.html"
    context_object_name = "patient"
    success_url = reverse_lazy("patients:list")

    def get_queryset(self):
        return Patient.objects.filter(user=self.request.user)
