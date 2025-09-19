from django.urls import path
from .views import PsyRecordCreateView, PsyRecordDetailView, PsyRecordUpdateView, PsyRecordDeleteView

app_name = "psy_records"

urlpatterns = [
    path('patient/<int:patient_id>/new/', PsyRecordCreateView.as_view(), name='create'),
    path('patient/<int:patient_id>/record/<int:pk>/', PsyRecordDetailView.as_view(), name='detail'),
    path('patient/<int:patient_id>/record/<int:pk>/edit/', PsyRecordUpdateView.as_view(), name='update'),
    path('patient/<int:patient_id>/record/<int:pk>/delete/', PsyRecordDeleteView.as_view(), name='delete'),
]