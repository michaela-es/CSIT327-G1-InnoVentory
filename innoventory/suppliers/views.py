from django.shortcuts import render, get_object_or_404, redirect
from datetime import timedelta
from django.utils import timezone
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from .models import Supplier
from .forms import SupplierForm
from django.contrib import messages

def supplier_list(request):
    suppliers = Supplier.objects.annotate(products_count_annotation=Count('products'))
    
    search_query = request.GET.get('search', '')
    date_filter = request.GET.get('date', '')
    
    if search_query:
        suppliers = suppliers.filter(
            Q(name__icontains=search_query) |
            Q(contact__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    products_range = request.GET.get('products_range', '')
    if products_range == '0-5':
        suppliers = suppliers.filter(products_count_annotation__range=(0, 5))
    elif products_range == '6-10':
        suppliers = suppliers.filter(products_count_annotation__range=(6, 10))
    elif products_range == '11+':
        suppliers = suppliers.filter(products_count_annotation__gte=11)
    
    if date_filter:
        today = timezone.now().date()
        if date_filter == 'today':
            suppliers = suppliers.filter(created_at__date=today)
        elif date_filter == 'week':
            start_of_week = today - timedelta(days=today.weekday())
            suppliers = suppliers.filter(created_at__date__gte=start_of_week)
        elif date_filter == 'month':
            suppliers = suppliers.filter(created_at__month=today.month, created_at__year=today.year)

    suppliers = suppliers.order_by('name')
    
    paginator = Paginator(suppliers, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'selected_date': date_filter,
        'selected_products_range': products_range,
        'page_title': 'Supplier Management',
    }
    
    return render(request, 'suppliers/supplier_list.html', context)

def supplier_modal(request, supplier_id=None):
    supplier = None
    if supplier_id:
        supplier = get_object_or_404(Supplier, id=supplier_id)
    
    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()
            return HttpResponse(
                '<script>'
                'document.getElementById("modal-container").innerHTML = "";'
                'window.location.reload();'
                '</script>'
            )
    else:
        form = SupplierForm(instance=supplier)
    
    return render(request, 'suppliers/partials/supplier_modal.html', {
        'form': form,
        'supplier': supplier,
        'modal_title': 'Edit Supplier' if supplier else 'Add Supplier',
        'submit_text': 'Update Supplier' if supplier else 'Save Supplier',
        'form_action': request.path,
    })

def delete_supplier(request, supplier_id):
    supplier = get_object_or_404(Supplier, id=supplier_id)
    supplier_name = supplier.name
    if supplier.products.exists():
            messages.error(request, f"Cannot delete supplier {supplier_name} because it is associated with existing product/s.", extra_tags='suppliers')
            return redirect('supplier_list')
    if request.method == 'POST':
        supplier.delete()
        messages.success(request, f"Supplier {supplier_name} deleted successfully.", extra_tags='suppliers')
        return redirect('supplier_list') 
    messages.error(request, 'Invalid request method.', extra_tags='suppliers')
    return redirect('supplier_list')
