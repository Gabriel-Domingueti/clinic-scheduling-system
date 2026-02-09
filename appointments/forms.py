from django import forms
from django.contrib.auth.models import User
from .models import Patient

class PatientRegistrationForm(forms.ModelForm):
    phone = forms.CharField(max_length=20, label="Telefone")
    cpf = forms.CharField(max_length=14, label="CPF")
    password = forms.CharField(widget=forms.PasswordInput, label="Senha")

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "password"]