from django.contrib import admin
from django.urls import path, include
from accounts.views import root_redirect
from . import views
from .views import unauthorized_view
handler403 = unauthorized_view

urlpatterns = [
    path('', root_redirect, name='root'),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('products/', include('products.urls')),
    path('sales/', include('sales.urls')),
    path('suppliers/', include('suppliers.urls')),
    path('reports/', include('reports.urls')),
    path('settings/', views.settings_view, name='settings')
]

