from django.views.generic import (
    ListView,
    CreateView,
    DetailView,
    UpdateView,
    DeleteView,
)
from django.core.paginator import Paginator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import Patient
from .forms import PatientForm, PatientSummaryForm


class PatientListView(LoginRequiredMixin, ListView):
    model = Patient
    template_name = "patients/patient_list.html"
    context_object_name = "patients"
    paginate_by = 10

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
    form_class = PatientSummaryForm
    context_object_name = "patient"
    paginate_by = 5

    def get_queryset(self):
        return Patient.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        patient = self.object

        records = patient.psy_records.all().order_by('-record_number')

        paginator = Paginator(records, self.paginate_by)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context['records_page'] = page_obj
        context['is_paginated'] = page_obj.has_other_pages()
        context['page_obj'] = page_obj
        context['paginator'] = paginator
        
        return context

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
