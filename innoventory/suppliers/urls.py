from django.urls import path
from . import views

urlpatterns = [
    path('', views.supplier_list, name='supplier_list'),
    path('modal/', views.supplier_modal, name='supplier_modal'),
    path('modal/<int:supplier_id>/', views.supplier_modal, name='supplier_modal'),
    path('delete/<int:supplier_id>/', views.delete_supplier, name='delete_supplier'),
]