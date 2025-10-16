from django.urls import path
from . import views

urlpatterns = [
    path('', views.stock_management, name='stock_management'),
]