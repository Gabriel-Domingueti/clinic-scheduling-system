from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from .patient import Patient
from .procedure import Procedure
from .schedule import WorkingDay, SpecialDay

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