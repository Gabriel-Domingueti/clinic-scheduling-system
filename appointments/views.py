from django.shortcuts import render, redirect
from .forms import PatientRegistrationForm, AppointmentForm
from .models import Patient, Appointment
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import timedelta
from django.utils import timezone

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
    my_appointments = Appointment.objects.filter(patient=patient_profile).order_by('date_time')

    return render(request, 'appointments/home.html',{
        'appointments': my_appointments
    })

@login_required
def schedule_appointment(request):
    if request.method == "POST":
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.patient = request.user.patient # Vincula ao paciente logado

            # Verifica se a data escolhida é menor que a data/hora atual
            if appointment.date_time < timezone.now():
                messages.error(request, "Você não pode agendar uma consulta em uma data ou horário que já passou.")
                return render(request, "appointments/schedule.html", {"form": form})

            duration = appointment.procedure.duration_minutes
            start_time = appointment.date_time
            end_time = start_time + timedelta(minutes=duration)

            # Procuramos por qualquer consulta que aconteça no mesmo dia
            potencial_conflicts = Appointment.objects.filter(
                date_time__date=start_time.date()
            )

            conflict_found = False
            for existing_appt in potencial_conflicts:
                # Calcula quando a consulta que já está no banco termina
                existing_start = existing_appt.date_time
                existing_end = existing_start + timedelta(minutes=existing_appt.procedure.duration_minutes)

                # Lógica de Interseção:
                if start_time < existing_end and end_time > existing_start:
                    conflict_found = True
                    break

            if conflict_found:
                messages.error(request, "Desculpe, este horário já está reservado.")
            else:
                appointment.save()
                messages.success(request, "Agendamento realizado com sucesso!")
                return redirect('home')
    else:
        form = AppointmentForm()
    return render(request, 'appointments/schedule.html', {'form': form})