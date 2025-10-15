from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse
from .forms import ProductForm,  ExcelUploadForm
from .models import Product
from django.db.models import Q 
from .models import Product, Category
from .utils import import_products_from_excel



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
    
    return render(request, 'products/product_list.html', {
        'products': products,
        'categories': categories,
        'search_query': search_query,
        'selected_category': category_filter,
    })


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