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

    def appointment_history(self):
        return self.appointments.filter(
            date_time__lt=timezone.now(),
            status__in=["DONE", "NO_SHOW"]
        ).order_by('date_time')

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"
    
    def clean(self):
        self.cpf = re.sub(r'[^0-9]', '', self.cpf)
    
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

class WorkingDay(models.Model):
    WEEKDAY_CHOICES = [
        (0, "Segunda"),
        (1, "Terça"),
        (2, "Quarta"),
        (3, "Quinta"),
        (4, "Sexta"),
        (5, "Sábado"),
        (6, "Domingo"),
    ]

    weekday = models.IntegerField(choices=WEEKDAY_CHOICES, unique=True)
    opening_time = models.TimeField()
    closing_time = models.TimeField()
    is_open = models.BooleanField(default=True)

    def __str__(self):
        return dict(self.WEEKDAY_CHOICES)[self.weekday]
    
# Feriado
class SpecialDay(models.Model):
    date = models.DateField(unique=True)
    opening_time = models.TimeField(null=True, blank=True)
    closing_time = models.TimeField(null=True, blank=True)
    is_open = models.BooleanField(default=False)

    def __str__(self):
        return str(self.date)

class Appointment(models.Model):
    STATUS_CHOICES = [
        ("SCHEDULED", "Agendado"),
        ("CANCELED", "Cancelado"),
        ("DONE", "Concluído"),
        ("NO_SHOW", "Não compareceu"),
    ]

    patient = models.ForeignKey(Patient, related_name="appointments", on_delete=models.CASCADE)
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
        # Trava alteração depois que aconteceu
        if self.pk:
            old = Appointment.objects.get(pk=self.pk)

            if old.date_time < timezone.now():
                if self.date_time != old.date_time or self.procedure != old.procedure:
                    raise ValidationError("Não é permitido alterar consultas passadas.")
                
            if old.status in ["DONE", "NO_SHOW"]:
                raise ValidationError("Não é permitido alterar consultas concluídas ou faltas.")

        # Trava para data no passado
        if self.date_time and self.date_time < timezone.now():
            raise ValidationError("Não é possível agendar uma consulta para uma data que já passou.")
                
        date = self.date_time.date()
        time_ = self.date_time.time()

        # 🔎 verifica exceção primeiro
        special = SpecialDay.objects.filter(date=date).first()

        if special:
            if not special.is_open:
                raise ValidationError("A clínica não funciona neste dia.")
            if not special.opening_time or not special.closing_time:
                raise ValidationError("Horário especial não configurado.")
            if not (special.opening_time <= time_ < special.closing_time):
                raise ValidationError("Fora do horário especial.")
        else:
            weekday = self.date_time.weekday()
            working_day = WorkingDay.objects.filter(weekday=weekday, is_open=True).first()

            if not working_day:
                raise ValidationError("A clínica não funciona neste dia da semana.")

            if not (working_day.opening_time <= time_ < working_day.closing_time):
                raise ValidationError("Fora do horário de funcionamento.")

        # ⚠ conflito de horário
        start_time = self.date_time
        end_time = start_time + timedelta(minutes=self.procedure.duration_minutes)

        conflict = Appointment.objects.filter(
            date_time__date=start_time.date(),
            status="SCHEDULED"
        ).exclude(pk=self.pk)

        for existing in conflict:
            existing_start = existing.date_time
            existing_end = existing_start + timedelta(minutes=existing.procedure.duration_minutes)

            if start_time < existing_end and end_time > existing_start:
                raise ValidationError(
                    f"Conflito: já existe agendamento das {existing_start.strftime('%H:%M')} "
                    f"às {existing_end.strftime('%H:%M')}."
                )

    def cancel(self):
        if self.status != "SCHEDULED":
            raise ValidationError("Este agendamento não pode ser cancelado.")
        if self.date_time < timezone.now():
            raise ValidationError("Não é possível cancelar uma consulta que já ocorreu.")
        self.status = 'CANCELED'
        self.save(update_fields=["status"])

    def mark_done(self):
        if self.status != "SCHEDULED":
            raise ValidationError("Só é possível concluir consultas agendadas.")
        if self.date_time > timezone.now():
            raise ValidationError("Não é possível concluir antes do horário.")
        self.status = "DONE"
        self.save(update_fields=["status"])

    def mark_no_show(self):
        if self.status != "SCHEDULED":
            raise ValidationError("Só é possível marcar falta em consultas agendadas.")
        if self.date_time > timezone.now():
            raise ValidationError("Não é possível marcar falta antes do horário.")
        self.status = "NO_SHOW"
        self.save(update_fields=["status"])
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)