from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from ..models import Procedure


@login_required
def catalog(request):
    procedures = Procedure.objects.all()
    return render(request, "appointments/catalog.html", {
        "procedures": procedures
    })