from django.urls import path
from . import views
from accounts.decorators import admin_required

app_name = 'reports'

urlpatterns = [
    path('', views.report_dashboard, name='dashboard'),
    path('export-excel/', is_admin(views.export_excel), name='export_excel'),
]
