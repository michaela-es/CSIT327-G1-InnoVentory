from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('modal/', views.product_modal, name='product_modal'),  # Add product
    path('modal/<int:pk>/', views.product_modal, name='product_modal'),  # Edit product
    path('delete/<int:pk>/', views.delete_product, name='delete_product'),
]