from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from ..forms.patient import PatientRegistrationForm
from ..forms.auth import EmailAuthenticationForm
from ..models import Patient

def register(request):
    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user = authenticate(
                request,
                username=user.email,
                password=form.cleaned_data["password1"]
            )

            if user is not None:
                login(request, user)
                return redirect("appointments:home")
    else:
        form = PatientRegistrationForm()

    return render(request, 'registration/register.html', {'form': form})

def login_view(request):
    if request.method == "POST":
        form = EmailAuthenticationForm(request.POST)

        if form.is_valid():
            login(request, form.get_user())
            return redirect("appointments:home")
    else:
        form = EmailAuthenticationForm()

    return render(request, "registration/login.html", {"form": form})

@login_required
def logout_view(request):
    if request.method == "POST":
        logout(request)
        return redirect("login")
    return redirect("appointments:home")