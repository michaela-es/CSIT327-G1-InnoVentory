from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse
from .forms import ProductForm
from .models import Product


@login_required
def product_list(request):
    products = Product.objects.all()
    return render(request, 'products/product_list.html', {'products': products})

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
        if pk:
            product = get_object_or_404(Product, pk=pk)
            form = ProductForm(request.POST, instance=product)
        else:
            form = ProductForm(request.POST)

        if form.is_valid():
            form.save()
            return HttpResponse('''
                <script>
                    document.getElementById("modal-container").innerHTML = "";
                    window.location.reload();
                </script>
            ''')

    return render(request, 'products/partials/product_form_modal.html', {
        'form': form,
        'modal_title': modal_title,
        'submit_text': submit_text,
        'form_action': form_action,
    })

#
# @login_required
# def add_product(request):
#     if request.method == 'POST':
#         form = ProductForm(request.POST)
#         if form.is_valid():
#             form.save()
#             return HttpResponse('''
#                                 <script>
#                                     document.getElementById("modal-container").innerHTML = "";
#                                     window.location.reload();
#                                 </script>
#                             ''')
#     else:
#         form = ProductForm()
#
#     return render(request, 'products/partials/product_form_modal.html', {
#         'form': form,
#         'modal_title': 'Add Product',
#         'submit_text': 'Add Product',
#     })
# @login_required
# def edit_product(request, pk):
#     product = get_object_or_404(Product, pk=pk)
#
#     if request.method == 'POST':
#         form = ProductForm(request.POST, instance=product)
#         if form.is_valid():
#             form.save()
#             return HttpResponse('''
#                     <script>
#                         document.getElementById("modal-container").innerHTML = "";
#                         window.location.reload();
#                     </script>
#                 ''')
#     else:
#         form = ProductForm(instance=product)
#
#     return render(request, 'products/partials/product_form_modal.html', {
#         'form': form,
#         'modal_title': 'Edit Product',
#         'submit_text': 'Save Changes',
#     })
#
