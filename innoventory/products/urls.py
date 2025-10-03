from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('modal/', views.product_modal, name='product_modal'),
    path('add/', views.add_product, name='add_product'),
    path('delete/<int:pk>/', views.delete_product, name='delete_product'),
]