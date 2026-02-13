from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from datetime import time
import re

# Validador de CPF
def validate_cpf(value):
    cpf = re.sub(r'[^0-9]', '', value)

    if len(cpf) != 11:
        raise ValidationError("O CPF deve conter 11 números.")
    
    if cpf == cpf[0] * 11:
        raise ValidationError("CPF inválido.")
    
    sum1 = sum(int(cpf[i]) * (10 - i) for i in range(9))
    digit1 = (sum1 * 10) % 11
    if digit1 == 10:
        digit1 = 0

    sum2 = sum(int(cpf[i]) * (11 - i) for i in range(10))
    digit2 = (sum2 * 10) % 11
    if digit2 == 10:
        digit2 = 0

    if digit1 != int(cpf[9]) or digit2 != int(cpf[10]):
        raise ValidationError("CPF inválido.")

class Patient(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20)
    cpf = models.CharField(
        max_length=14, 
        unique=True, 
        validators=[validate_cpf]
        )
    birth_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"
    
    def clean(self):
        self.cpf = self.cpf.strip()
    
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
        ("DONE", "Concluído"),
        ("NO_SHOW", "Não compareceu"),
    ]

    OPENING_TIME = time(8, 0) # Abre as 8:00
    CLOSING_TIME = time(18, 0) # Fecha as 18:00
    WORKING_DAYS = [0, 1, 2, 3, 4] # Abre segunda(0) e fecha na sexta(4)

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
        
        # Lógica de dia de semana
        weekday = self.date_time.weekday() # segunda(0) domingo(6)
        if weekday not in self.WORKING_DAYS:
            raise ValidationError("A clínica não funciona nesse dia.")
        
        # Lógica horário de funcionamento
        appointment_time = self.date_time.time()
        if not (self.OPENING_TIME <= appointment_time < self.CLOSING_TIME):
            raise ValidationError("Fora do horário de funcionamento da clínica.")

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
        if self.status != "SCHEDULED":
            raise ValidationError("Este agendamento não pode ser cancelado.")
        if self.date_time < timezone.now():
            raise ValidationError("Não é possível cancelar uma consulta que já ocorreu.")
        self.status = 'CANCELED'
        self.save(update_fields=["status"])

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def mark_done(self):
        if self.status != "SCHEDULED":
            raise ValidationError("Só é possível concluir consultas agendadas.")
        if self.date_time > timezone.now():
            raise ValidationError("Não é possível concluir uma consulta que ainda não aconteceu.")
        self.status = "DONE"
        self.save(update_fields=["status"])

    def mark_no_show(self):
        if self.status != "SCHEDULED":
            raise ValidationError("Só é possível marcar falta em consultas agendadas.")
        if self.date_time > timezone.now():
            raise ValidationError("Não é possível marcar falta antes do horário.")
        self.status = "NO_SHOW"
        self.save(update_fields=["status"])