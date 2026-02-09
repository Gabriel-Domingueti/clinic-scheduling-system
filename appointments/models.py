from django.db import models
from django.contrib.auth.models import User

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
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    procedure = models.ForeignKey(Procedure, on_delete=models.CASCADE, verbose_name="Procedimento")
    date_time = models.DateTimeField(verbose_name="Data e Horário")
    is_confirmed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Agendamento"
        verbose_name_plural = "Agendamentos"

    def __str__(self):
        return f"{self.patient.user.username} - {self.date_time}"