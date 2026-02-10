from django.shortcuts import render, redirect, get_object_or_404
from .forms import PatientRegistrationForm, AppointmentForm
from .models import Patient, Appointment
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import timedelta
from django.utils import timezone
from django.core.exceptions import ValidationError

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

@login_required
def home(request):
    patient_profile = request.user.patient
    appointments = Appointment.objects.filter(patient=patient_profile).order_by('date_time')

    return render(request, 'appointments/home.html',{
        'appointments': appointments
    })

@login_required
def schedule_appointment(request):
    if request.method == "POST":
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.patient = request.user.patient # Vincula ao paciente logado

            try:
                appointment.save()
                messages.success(request, "Consulta agendada com sucesso!")
                return redirect('home')
            except ValidationError as e:
                for error in e.messages:
                    form.add_error(None, error)

    else:
        form = AppointmentForm()

    return render(request, 'appointments/schedule.html', {'form': form})

@login_required
def cancel_appointment(request, appointment_id):
    # Garante que só o paciente cancele os próprios agendamentos
    appointment = get_object_or_404(Appointment, id=appointment_id, patient__user=request.user)

    if request.method == 'POST':
        try:
            appointment.cancel()
            messages.success(request, "Agendamento cancelado.")
        except ValidationError as e:
            for error in e.messages:
                messages.error(request, error)

    return redirect('home')
