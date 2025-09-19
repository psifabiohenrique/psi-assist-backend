from django.views.generic import CreateView, DetailView, UpdateView, DeleteView
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import PsyRecord
from patients.models import Patient
from .forms import PsyRecordForm


class PsyRecordCreateView(LoginRequiredMixin, CreateView):
    model = PsyRecord
    form_class = PsyRecordForm
    template_name = "psy_records/psyrecord_form.html"
    context_object_name = "record"

    def dispatch(self, request, *args, **kwargs):
        self.patient = get_object_or_404(
            Patient, id=kwargs["patient_id"], user=request.user
        )
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['patient'] = self.patient
        return context

    def form_valid(self, form):
        form.instance.patient = self.patient
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("patients:detail", args=[self.patient.id])


class PsyRecordDetailView(LoginRequiredMixin, DetailView):
    model = PsyRecord
    template_name = "psy_records/psyrecord_detail.html"
    context_object_name = "record"

    def get_queryset(self):
        return PsyRecord.objects.filter(
            patient__user=self.request.user, patient_id=self.kwargs["patient_id"]
        )


class PsyRecordUpdateView(LoginRequiredMixin, UpdateView):
    model = PsyRecord
    form_class = PsyRecordForm
    template_name = "psy_records/psyrecord_form.html"
    context_object_name = "record"

    def get_queryset(self):
        return PsyRecord.objects.filter(
            patient__user=self.request.user, patient_id=self.kwargs["patient_id"]
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['patient'] = self.object.patient
        return context

    def get_success_url(self):
        return reverse("patients:detail", args=[self.kwargs["patient_id"]])


class PsyRecordDeleteView(LoginRequiredMixin, DeleteView):
    model = PsyRecord
    template_name = "psy_records/psyrecord_confirm_delete.html"
    context_object_name = "record"

    def get_queryset(self):
        return PsyRecord.objects.filter(
            patient__user=self.request.user, patient_id=self.kwargs["patient_id"]
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['patient'] = self.object.patient
        return context

    def get_success_url(self):
        return reverse("patients:detail", args=[self.kwargs["patient_id"]])
