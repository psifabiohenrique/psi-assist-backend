from django.db import models
from django.utils import timezone

class PsyRecord(models.Model):
    patient = models.ForeignKey(
        'patients.Patient',
        on_delete=models.CASCADE,
        related_name="psy_records"
    )
    
    record_number = models.PositiveIntegerField(editable=False)
    date = models.DateField(default=timezone.now)
    content = models.TextField(blank=True)
    
    class Meta:
        unique_together = ('patient', 'record_number')
        ordering = ['patient', 'record_number']
    
    def save(self, *args, **kwargs):
        if not self.record_number:
            last_record = PsyRecord.objects.filter(patient=self.patient).order_by('-record_number').first()
            if last_record:
                self.record_number = last_record.record_number + 1
            else:
                self.record_number = 1
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Prontuário #{self.record_number} - {self.patient.full_name}"