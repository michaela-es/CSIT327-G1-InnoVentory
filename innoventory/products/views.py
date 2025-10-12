from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse
from .forms import ProductForm, ExcelUploadForm
from .models import Product
from django.core.paginator import Paginator
from django.http import JsonResponse
from .utils import import_products_from_excel

@login_required
def product_list(request):
    products = Product.objects.all()
    paginator = Paginator(products, 10)

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'products/product_list.html', {'page_obj': page_obj})

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
    is_post = request.method == 'POST'
    is_htmx = request.headers.get('Hx-Request') == 'true'

    if pk:
        product = get_object_or_404(Product, pk=pk)
        form = ProductForm(request.POST if is_post else None, instance=product)
        modal_title = 'Edit Product'
        submit_text = 'Save Changes'
        form_action = reverse('product_edit_modal', args=[pk])
    else:
        product = None
        form = ProductForm(request.POST if is_post else None)
        modal_title = 'Add Product'
        submit_text = 'Add Product'
        form_action = reverse('product_add_modal')

    if is_post:
        if form.is_valid():
            form.save()
            return HttpResponse('''
                <script>
                    document.getElementById("modal-container").innerHTML = "";
                    window.location.reload();
                </script>
            ''')

        if is_htmx:
            return render(request, "products/partials/product_form_fields.html", {
                "form": form,
            })

    return render(request, "products/partials/product_modal.html", {
        "form": form,
        "modal_title": modal_title,
        "submit_text": submit_text,
        "form_action": form_action,
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
