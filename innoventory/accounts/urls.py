from django.contrib.auth.views import LogoutView
from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.custom_login, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('staff-dashboard/', views.staff_dashboard, name='staff_dashboard'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('users/', views.user_list, name='user_list'),
    path('users/delete/<int:user_id>/', views.delete_user, name='delete_user'),
    path('users/toggle-status/<int:user_id>/', views.toggle_user_status, name='toggle_user_status'),
]