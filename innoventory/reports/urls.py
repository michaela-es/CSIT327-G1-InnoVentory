from django.urls import path
from . import views
from accounts.decorators import admin_required

app_name = 'reports'

urlpatterns = [
    path('', admin_required(views.report_dashboard), name='dashboard'),
    path('export-excel/', admin_required(views.export_excel), name='export_excel'),
]
