from django.urls import path
from . import views

urlpatterns = [
    path('', views.sales_record, name='sales_record'),
    path('new/', views.create_sale, name='create_sale'),
    path('record-sale-modal/', views.record_sale_modal, name='record_sale_modal'),
    path('calculate-total/', views.calculate_total, name='calculate_total'),
    path('credits/', views.credit_management, name='credit_management'),
    path('credits/payment/<int:sale_id>/', views.record_payment, name='record_payment'),
    path('credits/delete/<int:sale_id>/', views.delete_credit_sale, name='delete_credit_sale'),
]
