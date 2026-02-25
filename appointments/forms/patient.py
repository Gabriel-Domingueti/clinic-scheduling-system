from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from ..models import Patient

class PatientRegistrationForm(UserCreationForm):
    first_name = forms.CharField(
        label="Nome",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Seu nome"})
    )
    last_name = forms.CharField(
        label="Sobrenome",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholer": "Seu sobrenome"})
    )
    email = forms.EmailField(
        required=True,
        label="E-mail",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "exemplo@email.com"})
    )
    phone = forms.CharField(
        max_length=20,
        label="Telefone",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "(00) 00000-0000"})
    )
    cpf = forms.CharField(
        max_length=14,
        label="CPF",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "000.000.000-00"})
    )

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
        ]

        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control", "placeholder": "Escolha um usuário"}),
        }

    def clean_email(self):
        email = self.cleaned_data.get("email")

        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Esye e-mail já está em uso.")
        return email

    def save(self, commit=True):
        user = super().save(commit)

        # Faz o username ser igual ao email
        user.username = self.cleaned_data["email"]
        user.email = self.cleaned_data["email"].lower()
        if commit:
            user.save()
            Patient.objects.create(
                user=user,
                phone=self.cleaned_data["phone"],
                cpf=self.cleaned_data["cpf"]
            )

        return user