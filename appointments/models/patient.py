from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
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