from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from datetime import datetime
from ..forms import AppointmentForm
from ..models import Appointment

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

@login_required
def appointment_history(request):
    patient = request.user.patient
    appointments = Appointment.objects.filter(
        patient=patient,
        status__in=["DONE", "NO_SHOW"]
    ).order_by("-date_time")

    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    if start_date:
        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            appointments = appointments.filter(date_time__date__gte=start_date)
        except ValueError:
            start_date = None

    if end_date:
        try:
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
            appointments = appointments.filter(date_time__date__lte=end_date)
        except ValueError:
            end_date = None
    
    return render(request, "appointment/history.html", {
        "appointments": appointments,
        "start_date": start_date,
        "end_date": end_date
    })
