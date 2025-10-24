from django.contrib import admin
from django.urls import path, include
from accounts.views import root_redirect

urlpatterns = [
    path('', root_redirect, name='root'),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('products/', include('products.urls')),
    path('stocks/', include('stocks.urls')),
    path('sales/', include('sales.urls'))
]
