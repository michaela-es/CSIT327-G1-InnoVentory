from django.urls import path
from . import views

urlpatterns = [
    path('', views.sales_record, name='sales_record'),
    path('create/', views.create_sale, name='create_sale'),
    path('record-sale-modal/', views.record_sale_modal, name='record_sale_modal'),
    path('calculate-total/', views.calculate_total, name='calculate_total')
]
