from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, timedelta
from ..forms import AppointmentForm
from ..models import Appointment, WorkingDay, SpecialDay

@login_required
def home(request):
    patient_profile = request.user.patient
    appointments = Appointment.objects.filter(patient=patient_profile).order_by('date_time')

    return render(request, 'appointments/home.html',{
        'appointments': appointments
    })

def generate_available_slots(date, procedure):
    slots = []

    # verifica se tem dia especial
    special = SpecialDay.objects.filter(date=date).first()

    if special:
        if not special.is_open:
            return []  # Clínica fechada nesse dia
        opening = special.opening_time
        closing = special.closing_time
    else:
        weekday = date.weekday()
        working_day = WorkingDay.objects.filter(
            weekday=weekday,
            is_open=True
        ).first()

        if not working_day:
            return []  # Clínica fechada nesse dia
        
        opening = working_day.opening_time
        closing = working_day.closing_time

    current = timezone.make_aware(datetime.combine(date, opening))
    end = timezone.make_aware(datetime.combine(date, closing))

    duration = timedelta(minutes=procedure.duration_minutes)

    # Buscar todos agendamentos do dia uma vez
    appointments = Appointment.objects.filter(
        date_time__date = date,
        status="SCHEDULED"
    ).select_related("procedure")

    while current + duration <= end:
        has_conflict = False

        for existing in appointments:
            existing_start = existing.date_time
            existing_end = existing_start + timedelta(
                minutes=existing.procedure.duration_minutes
            )

            if current < existing_end and (current + duration) > existing_start:
                has_conflict = True
                break

        if not has_conflict and current >= timezone.now():
            slots.append(current.time())

        current += timedelta(minutes=30)

    return slots

@login_required
def schedule_appointment(request):
    slots = None

    if request.method == "POST":
        form = AppointmentForm(request.POST)

        if form.is_valid():
            procedure = form.cleaned_data["procedure"]
            date = form.cleaned_data["date"]
            time = form.cleaned_data["time"]

            # Já escolheu o horário
            if time:
                date_time = datetime.combine(date, time)
                date_time = timezone.make_aware(date_time)

                appointment = Appointment(
                    patient = request.user.patient,
                    procedure = procedure,
                    date_time = date_time
                )

                try:
                    appointment.save()
                    messages.success(request, "Consulta agendada com sucesso!")
                    return redirect('appointments:home')
                except ValidationError as e:
                    for error in e.messages:
                        form.add_error(None, error)
            
            # Gerar horário
            else:
                slots = generate_available_slots(date, procedure)

    else:
        form = AppointmentForm()

    return render(request, 'appointments/schedule.html', {
            'form': form,
            'slots': slots
        })

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
