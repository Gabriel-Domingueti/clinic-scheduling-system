from django import forms
from ..models import Appointment

class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ["procedure", "date_time"]
        labels = {
            "procedure": "Procedimento Desejado",
            "date_time": "Dia e Hora da Consulta",
        }
        help_text = {
            "date_time": "Formato: DD/MM/AAAA HH:MM",
        }
        widgets = {
            # Isso cria um calendário com seletor de hora no navegador
            "date_time": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }