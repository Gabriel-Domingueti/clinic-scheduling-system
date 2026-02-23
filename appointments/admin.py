from django.contrib import admin
from .models import Patient, Procedure, Appointment, WorkingDay, SpecialDay
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.utils import timezone

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("user", "cpf", "phone")
    search_fields = ("user__username", "cpf")

@admin.register(Procedure)
class ProcedureAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "duration_minutes")
    search_fields = ("name",)

@admin.register(WorkingDay)
class WorkingDayAdmin(admin.ModelAdmin):
    list_display = ("weekday", "opening_time", "closing_time", "is_open")
    list_editable = ("opening_time", "closing_time", "is_open")

@admin.register(SpecialDay)
class SpecialDayAdmin(admin.ModelAdmin):
    list_display = ("date", "opening_time", "closing_time", "is_open")
    list_editable = ("opening_time", "closing_time", "is_open")
    search_fields = ("date",)

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("patient", "procedure", "date_time", "status")
    list_filter = ("status", "date_time")
    search_fields = ("patient__user__username",)
    ordering = ("-date_time",)

    actions = ["mark_done", "mark_no_show", "mark_canceled"]

    def has_change_permission(self, request, obj =None):
        if obj:
            if obj.date_time < timezone.now():
                return False
            if obj.status in ["DONE", "NO_SHOW"]:
                return False
        return super().has_change_permission(request, obj)

    def mark_done(self, request, queryset):
        update = 0
        for appointment in queryset:
            try:
                appointment.mark_done()
                update += 1
            except ValidationError as e:
                self.message_user(request, str(e), level=messages.ERROR)
        self.message_user(request, "Consulta(s) marcadas como CONCLUÍDAS.")

    mark_done.short_description = "Marcar como concluída"

    def mark_no_show(self, request, queryset):
        update = 0
        for appointment in queryset:
            try:
                appointment.mark_no_show()
                update += 1
            except ValidationError as e:
                self.message_user(request, str(e), level=messages.ERROR)
        self.message_user(request, "Consulta(s) marcadas como FALTA.")

    mark_no_show.short_description = "Marcar como não compareceu"

    def mark_canceled(self, request, queryset):
        for appointment in queryset:
            try:
                appointment.cancel()
            except ValidationError as e:
                self.message_user(request, str(e), level=messages.ERROR)
        self.message_user(request, "Consultas canceladas.")

    mark_canceled.short_description = "Cancelar consultas"