from django.urls import path
from . import views

urlpatterns = [
    path('', views.creditors_list, name='creditors_list'),
    path('link-sale/<int:sale_id>/', views.link_sale_to_creditor, name='link_sale_to_creditor'),
    path('mark-paid/<int:credit_id>/', views.mark_credit_paid, name='mark_credit_paid'),
    path('payment-modal/<int:credit_id>/', views.payment_modal, name='payment_modal'),
    path('make-payment/<int:credit_id>/', views.make_payment, name='make_payment'),
    path('link-sale-modal/<int:sale_id>/', views.link_sale_modal, name='link_sale_modal')

]
