from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta

class Patient(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20)
    cpf = models.CharField(max_length=14, unique=True)
    birth_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"
    
class Procedure(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nome do Procedimento")
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    duration_minutes = models.IntegerField()

    class Meta:
        verbose_name = "Procedimento"
        verbose_name_plural = "Procedimentos"

    def __str__(self):
        return self.name

class Appointment(models.Model):
    STATUS_CHOICES = [
        ("SCHEDULED", "Agendado"),
        ("CANCELED", "Cancelado"),
    ]
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    procedure = models.ForeignKey(Procedure, on_delete=models.CASCADE, verbose_name="Procedimento")
    date_time = models.DateTimeField(verbose_name="Data e Horário")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="SCHEDULED",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Agendamento"
        verbose_name_plural = "Agendamentos"

    def __str__(self):
        return f"{self.patient.user.username} - {self.date_time}"
    
    def clean(self):
        # Trava para data no passado
        if self.date_time and self.date_time < timezone.now():
            raise ValidationError("Não é possível agendar uma consulta para uma data que já passou.")
        
        # Lógica de conflito de horários
        if self.date_time and self.procedure:
            start_time = self.date_time
            end_time = start_time + timedelta(minutes=self.procedure.duration_minutes)

            conflict = Appointment.objects.filter(
                date_time__date=start_time.date(),
                status='SCHEDULED'
            ).exclude(pk=self.pk)

            for existing_appt in conflict:
                existing_start = existing_appt.date_time
                existing_end = existing_start + timedelta(minutes=existing_appt.procedure.duration_minutes)

                if start_time < existing_end and end_time > existing_start:
                    raise ValidationError(
                        f"Conflito: Já existe um agendamento das {existing_start.strftime('%H:%M')} às {existing_end.strftime('%H:%M')}."
                    )

    def cancel(self):
        if self.status == 'CANCELED':
            raise ValidationError("ESte agendamento já foi cancelado.")
        if self.date_time < timezone.now():
            raise ValidationError("Não é possível cancelar uma consulta que já ocorreu.")
        self.status = 'CANCELED'
        self.save()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)