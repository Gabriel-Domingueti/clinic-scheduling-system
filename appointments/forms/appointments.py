from django import forms
from ..models import Appointment, Procedure

class AppointmentForm(forms.Form):
    procedure = forms.ModelChoiceField(
        queryset=Procedure.objects.all(),
        label="Procedimento Desejado",
        widget =forms.Select(attrs={"class": "form-select"})
    )

    date = forms.DateField(
        label="Data da Consulta",
        widget=forms.DateInput(attrs={
                    "type": "date",
                    "class": "form-control"
                })
    )

    time = forms.TimeField(
        required=False,
        input_formats=["%H:%M"],
        widget=forms.HiddenInput()
    )