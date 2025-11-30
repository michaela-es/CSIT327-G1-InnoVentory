from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from .models import Supplier
from .forms import SupplierForm
import pandas as pd
from django.contrib import messages

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
    if request.method == 'POST':
        supplier_name = supplier.name
        supplier.delete()
        messages.success(request, f"Supplier {supplier_name} deleted successfully.", extra_tags='suppliers')
        return redirect('supplier_list') 
    messages.error(request, 'Invalid request method.', extra_tags='suppliers')
    return render(request, 'suppliers/partials/delete_confirm_modal.html', {'supplier': supplier })

def import_suppliers_from_excel(excel_file):
    try:
        if excel_file.name.endswith('.xlsx'):
            df = pd.read_excel(excel_file, engine='openpyxl')
        else:
            df = pd.read_excel(excel_file)
        
        created = 0
        updated = 0
        total = 0
        
        for index, row in df.iterrows():
            total += 1
            try:
                supplier, created_flag = Supplier.objects.get_or_create(
                    name=row['name'],
                    defaults={
                        'contact': row.get('contact', ''),
                        'email': row.get('email', ''),
                        'address': row.get('address', ''),
                        'notes': row.get('notes', ''),
                    }
                )
                
                if created_flag:
                    created += 1
                else:
                    supplier.contact = row.get('contact', supplier.contact)
                    supplier.email = row.get('email', supplier.email)
                    supplier.address = row.get('address', supplier.address)
                    supplier.notes = row.get('notes', supplier.notes)
                    supplier.save()
                    updated += 1
                    
            except Exception as e:
                raise Exception(f"Row {index + 2}: {str(e)}")
        
        return {
            'created': created,
            'updated': updated,
            'total': total
        }
        
    except Exception as e:
        raise Exception(f"Error processing Excel file: {str(e)}")