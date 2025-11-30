from django.urls import path
from . import views
from accounts.decorators import admin_required

urlpatterns = [
    path('', admin_required(views.supplier_list), name='supplier_list'),
    path('modal/', admin_required(views.supplier_modal), name='supplier_modal'),
    path('modal/<int:supplier_id>/', admin_required(views.supplier_modal), name='supplier_modal'),
    path('delete/<int:supplier_id>/', admin_required(views.delete_supplier), name='delete_supplier'),
]
