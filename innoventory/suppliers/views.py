from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.contrib import messages
from .models import Supplier
from .forms import SupplierForm
import json

def supplier_list(request):
    suppliers = Supplier.objects.annotate(products_count_annotation=Count('products'))
    
    search_query = request.GET.get('search', '')
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
    
    suppliers = suppliers.order_by('name')
    
    paginator = Paginator(suppliers, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'selected_products_range': products_range,
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
    if request.method == 'POST':
        supplier_name = supplier.name
        supplier.delete()
        return HttpResponse(
            status=204,
            headers={
                'HX-Trigger': json.dumps({
                    "supplierListChanged": None,
                    "showMessage": f"Supplier {supplier_name} deleted successfully."
                })
            }
        )
    return redirect('supplier_list')