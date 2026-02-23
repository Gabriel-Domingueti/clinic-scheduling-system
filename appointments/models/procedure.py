from django.db import models

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
