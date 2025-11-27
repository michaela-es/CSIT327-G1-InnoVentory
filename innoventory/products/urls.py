from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('modal/', views.product_modal_threshold, name='product_modal_threshold'),
    path('modal/<int:pk>/', views.product_modal_threshold, name='product_modal_threshold'),
    # path('modal/', views.product_modal, name='product_modal'),
    # path('modal/<int:pk>/', views.product_modal, name='product_modal'),
    path('delete/<int:pk>/', views.delete_product, name='delete_product'),
    path('upload-excel/', views.upload_excel_modal, name='upload_excel_modal'),
    path('transactions/', views.stock_transactions, name='stock_transactions'),
    path('transactions/delete/<int:transaction_id>/', views.delete_transaction, name='delete_transaction'),
    path('transactions/edit/<int:transaction_id>/', views.edit_transaction_modal, name='edit_transaction_modal'),
]