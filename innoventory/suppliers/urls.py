from django.urls import path
from . import views
from accounts.decorators import admin_required
from accounts.views import is_admin

urlpatterns = [
    path('', admin_required(views.supplier_list), name='supplier_list'),
    path('modal/', is_admin(views.supplier_modal), name='supplier_modal'),
    path('modal/<int:supplier_id>/', is_admin(views.supplier_modal), name='supplier_modal'),
    path('delete/<int:supplier_id>/', is_admin(views.delete_supplier), name='delete_supplier'),
]