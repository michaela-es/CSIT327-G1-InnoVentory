from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse
from .forms import ProductForm
from django.db.models import Q
from .models import Product, Category, StockTransaction, Supplier
from .utils import import_products_from_excel
from .forms import StockTransactionForm
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404



@login_required
def product_list(request):
    products = Product.objects.all()
    categories = Category.objects.all().order_by('name')
    
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(category__name__icontains=search_query) |
            Q(supplier__name__icontains=search_query)
        )
    
    if category_filter:
        products = products.filter(category_id=category_filter)
    paginator = Paginator(products, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_title': 'Inventory Management',
        'page_obj': page_obj,
        'categories': categories,
        'search_query': search_query,
        'selected_category': category_filter,
    }

    return render(request, 'products/product_list.html', context)


@login_required
@require_POST
def delete_product(request, pk):
    try:
        product = Product.objects.get(product_id=pk)
        product.delete()
    except Product.DoesNotExist:
        pass
    return HttpResponseRedirect(reverse('product_list'))


@login_required
def product_modal(request, pk=None):
    if pk:
        product = get_object_or_404(Product, pk=pk)
        form = ProductForm(instance=product)
        modal_title = 'Edit Product'
        submit_text = 'Save Changes'
        form_action = reverse('product_modal', args=[pk])
    else:
        product = None
        form = ProductForm()
        modal_title = 'Add Product'
        submit_text = 'Add Product'
        form_action = reverse('product_modal')

    if request.method == 'POST':
        new_category_name = request.POST.get('new_category_name', '').strip()
        
        post_data = request.POST.copy()
        if not post_data.get('category') or post_data.get('category') == '__new__':
            if not new_category_name:
                if pk:
                    product = get_object_or_404(Product, pk=pk)
                    form = ProductForm(post_data, instance=product)
                else:
                    form = ProductForm(post_data)
                form.add_error('category', 'Please select a category or enter a new category name.')
                
                return render(request, 'products/partials/product_modal.html', {
                    'form': form,
                    'modal_title': modal_title,
                    'submit_text': submit_text,
                    'form_action': form_action,
                })
        
        if new_category_name:
            category, created = Category.objects.get_or_create(name=new_category_name)
            post_data['category'] = category.id
        elif post_data.get('category') == '__new__':
            post_data['category'] = ''
        
        if pk:
            product = get_object_or_404(Product, pk=pk)
            form = ProductForm(post_data, instance=product)
        else:
            form = ProductForm(post_data)
        
        category_choices = [('', '---------'), ('__new__', '➕ Add New Category')]
        category_choices.extend([(cat.id, cat.name) for cat in Category.objects.all().order_by('name')])
        form.fields['category'].choices = category_choices

        if form.is_valid():
            form.save()
            return HttpResponse('''
                <script>
                    document.getElementById("modal-container").innerHTML = "";
                    window.location.reload();
                </script>
            ''')

    return render(request, 'products/partials/product_modal.html', {
        'form': form,
        'modal_title': modal_title,
        'submit_text': submit_text,
        'form_action': form_action,
    })

@login_required
def upload_excel_modal(request):
    if request.method == "POST":

        if 'excel_file' not in request.FILES:
            return JsonResponse({
                'success': False,
                'message': 'No file selected'
            })

        excel_file = request.FILES['excel_file']

        if not excel_file.name.endswith(('.xlsx', '.xls')):
            return JsonResponse({
                'success': False,
                'message': 'Please upload a valid Excel file (.xlsx or .xls)'
            })

        try:
            result = import_products_from_excel(excel_file)
            message = (f"Imported {result['created']} new products, "
                       f"updated {result['updated']} products, "
                       f"total processed {result['total']}.")
            return JsonResponse({
                'success': True,
                'message': message,
                'result': result
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })

    else:
        return render(request, "products/partials/excel_upload_modal.html")
    

def stock_transactions(request):
    if request.method == 'POST':
        form = StockTransactionForm(request.POST)
        if form.is_valid():
            try:
                transaction = form.save()
                messages.success(
                    request, 
                    f'Stock {transaction.get_transaction_type_display().lower()} recorded successfully for {transaction.product.name}!'
                )
                return redirect('stock_transactions')
            except ValueError as e:
                messages.error(request, str(e))
    else:
        form = StockTransactionForm()
    
    search_query = request.GET.get('search', '')
    transaction_type = request.GET.get('type', '')
    
    transactions = StockTransaction.objects.all()
    
    if search_query:
        transactions = transactions.filter(
            Q(product__name__icontains=search_query) |
            Q(remarks__icontains=search_query)
        )
    
    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)
    
    recent_transactions = transactions[:50] 
    
    context = {
        'form': form,
        'recent_transactions': recent_transactions,
        'search_query': search_query,
        'selected_type': transaction_type,
        'active_page': 'stock_transactions'
    }
    return render(request, 'products/stock_transactions.html', context)

def delete_transaction(request, transaction_id):
    transaction = get_object_or_404(StockTransaction, id=transaction_id) 
    if request.method == 'POST':
        product_name = transaction.product.name
        transaction.delete()
        messages.success(request, f'Transaction for {product_name} deleted successfully!')
        return redirect('stock_transactions')
    messages.error(request, 'Invalid request method.')
    return redirect('stock_transactions')

@login_required
def edit_transaction_modal(request, transaction_id):
    transaction = get_object_or_404(StockTransaction, id=transaction_id)
    if request.method == 'POST':
        form = StockTransactionForm(request.POST, instance=transaction)
        if form.is_valid():
            form.save()
            return HttpResponse('''
                <script>
                    document.getElementById("modal-container").innerHTML = "";
                    window.location.reload();
                </script>
            ''')
    else:
        form = StockTransactionForm(instance=transaction)
    
    context = {
        'form': form,
        'transaction': transaction,
        'modal_title': 'Edit Transaction',
        'form_action': f'/products/transactions/edit/{transaction.id}/',
        'submit_text': 'Update Transaction'
    }
    return render(request, 'products/partials/transaction_edit_modal.html', context)


def supplier_list(request):
    suppliers = Supplier.objects.annotate(products_count=Count('products'))
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        suppliers = suppliers.filter(
            Q(name__icontains=search_query) |
            Q(contact__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    # Products range filter
    products_range = request.GET.get('products_range', '')
    if products_range == '0-5':
        suppliers = suppliers.filter(products_count__range=(0, 5))
    elif products_range == '6-10':
        suppliers = suppliers.filter(products_count__range=(6, 10))
    elif products_range == '11+':
        suppliers = suppliers.filter(products_count__gte=11)
    
    # Date filter (simplified - you might want to implement proper date filtering)
    date_filter = request.GET.get('date', '')
    # Add date filtering logic here based on your needs
    
    suppliers = suppliers.order_by('name')
    
    paginator = Paginator(suppliers, 10) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'selected_products_range': products_range,
        'selected_date': date_filter,
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
                status=204,
                headers={
                    'HX-Trigger': json.dumps({
                        "supplierListChanged": None,
                        "showMessage": f"Supplier {'updated' if supplier else 'added'} successfully."
                    })
                }
            )
    else:
        form = SupplierForm(instance=supplier)
    
    return render(request, 'suppliers/partials/supplier_modal.html', {
        'form': form,
        'supplier': supplier
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