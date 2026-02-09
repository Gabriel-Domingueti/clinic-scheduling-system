from django import forms
from django.contrib.auth.models import User
from .models import Patient, Appointment

class PatientRegistrationForm(forms.ModelForm):
    phone = forms.CharField(
    max_length=20, 
    label="Telefone", 
    widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(00) 00000-0000'})
    )
    cpf = forms.CharField(
        max_length=14, 
        label="CPF", 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '000.000.000-00'})
    )
    password = forms.CharField(widget=forms.PasswordInput, label="Senha")

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "password"]

        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Escolha um usuário'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Seu nome'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Seu sobrenome'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'exemplo@email.com'}),
            'password': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Crie uma senha forte'}),
        }

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