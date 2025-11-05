from django.contrib import admin
from .models import Supplier

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact', 'email', 'products_count', 'created_at']
    search_fields = ['name', 'contact', 'email']
    list_filter = ['created_at']
    ordering = ['name']