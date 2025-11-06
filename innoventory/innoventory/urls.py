from django.contrib import admin
from django.urls import path, include
from accounts.views import root_redirect

urlpatterns = [
    path('', root_redirect, name='root'),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('products/', include('products.urls')),
    path('sales/', include('sales.urls')),
    path('credit/', include('credit.urls'))
    path('suppliers/', include('suppliers.urls'))
]
