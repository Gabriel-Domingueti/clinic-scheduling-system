from django.contrib import admin
from .models import Patient, Procedure, Appointment

admin.site.register(Patient)
admin.site.register(Procedure)
admin.site.register(Appointment)
