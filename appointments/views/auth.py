from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from ..forms import PatientRegistrationForm
from ..models import Patient

def register(request):
    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            # Salva o usuário
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])
            user.save()

            # Cria o perfil de Paciente vinculado a esse usuário
            Patient.objects.create(
                user=user,
                phone=form.cleaned_data["phone"],
                cpf=form.cleaned_data["cpf"]
            )
            return redirect("login")
    else:
        form = PatientRegistrationForm()
    return render(request, 'appointments/register.html', {'form': form})