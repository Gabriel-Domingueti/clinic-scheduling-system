from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = "appointments"

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='appointments/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('schedule/', views.schedule_appointment, name='schedule_appointment'),
    path('cancel/<int:appointment_id>/', views.cancel_appointment, name='cancel_appointment'),
    path("catalog/", views.catalog, name="catalog"),
    path("history/", views.appointment_history, name="appointment_history"),
]