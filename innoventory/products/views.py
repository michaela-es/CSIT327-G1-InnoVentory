from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse
from .forms import ProductForm
from django.db.models import Q, ProtectedError
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
    product = get_object_or_404(Product, product_id=pk)

    if product.transactions.exists():
        messages.error(request, "Cannot delete this product because it has stock transactions.")
        return redirect('product_list')

    try:
        product.delete()
        messages.success(request, "Product deleted successfully.")
    except ProtectedError:
        messages.error(request, "Cannot delete this product because it has sales.")
    return redirect('product_list')

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
    upload_type = request.GET.get('type', 'product')
    
    if request.method == "POST":
        upload_type = request.POST.get('type', 'product')

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
            if upload_type == 'supplier':
                result = import_suppliers_from_excel(excel_file)
                message = (f"Imported {result['created']} new suppliers, "
                           f"updated {result['updated']} suppliers, "
                           f"total processed {result['total']}.")
            else:
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
        context = {
            'upload_type': upload_type,
            'modal_title': 'Upload Suppliers Excel' if upload_type == 'supplier' else 'Upload Products Excel',
            'required_columns': 'name' if upload_type == 'supplier' else 'name, price, quantity',
            'optional_columns': 'contact, email, address, notes' if upload_type == 'supplier' else 'category, description',
        }
        return render(request, "products/partials/excel_upload_modal.html", context)
    

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


