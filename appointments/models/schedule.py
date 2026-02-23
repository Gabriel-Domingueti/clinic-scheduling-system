from django.db import models

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