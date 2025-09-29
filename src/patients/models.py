from django.db import models
from django.conf import settings

class Patient(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name="patients"
    )

    first_name = models.CharField('Priemiro nome', max_length=100)
    second_name = models.CharField('Segundo nome', max_length=100, blank=True, null=True)
    full_name = models.CharField('Nome completo', max_length=255, blank=True)
    birth_date = models.DateField('Data de nascimento')

    objectives = models.TextField('Objetivos', blank=True, null=True)
    clinical_demand = models.TextField('Demanda', blank=True, null=True)
    clinical_procedures = models.TextField('Procedimentos', blank=True, null=True)
    clinical_analysis = models.TextField('Análise', blank=True, null=True)
    clinical_conclusion = models.TextField('Conclusões', blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.full_name:
            if self.second_name:
                self.full_name = f'{self.first_name} {self.second_name}'
            else:
                self.full_name = self.first_name
        super().save(*args, **kwargs)

    @property
    def records_count(self):
        return self.psy_records.count()

    def __str__(self):
        return self.full_name