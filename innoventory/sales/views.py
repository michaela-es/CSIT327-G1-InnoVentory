from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.views.decorators.http import require_POST
from products.models import Product
from .forms import SaleForm
from .models import Sale
from stocks.models import Stocks


@login_required
def create_sale(request):
    if request.method == "POST":
        form = SaleForm(request.POST)
        if form.is_valid():
            product = form.cleaned_data['product']
            qty = form.cleaned_data['quantity']
            sales_type = form.cleaned_data['sales_type']
            total = product.price * qty

            sale = Sale.objects.create(
                product_sold=product,
                product_qty=qty,
                total=total,
                sales_type=sales_type,
                sold_by=request.user
            )

            Stocks.objects.create(
                product=product,
                qty=qty,
                type=Stocks.OUT,
                remarks=f"SOLD"
            )

            return redirect('sales_record')
    else:
        form = SaleForm()

    context = {
        'form': form,
        'modal_title': 'Record New Sale - Fix Errors',
        'form_action': reverse('create_sale'),
        'submit_text': 'Submit',
    }
    return render(request, 'sales/partials/record_sale_modal.html', context)

@login_required
def sales_record(request):
    sales = Sale.objects.order_by('-sales_date')[:5]
    products = Product.objects.all().order_by('name')
    context = {
        'sales': sales,
        'products': products,
        'page_title': 'Transactions',
    }
    return render(request, 'sales/sales_record.html', context)

@login_required
def record_sale_modal(request):
    form = SaleForm()
    context = {
        'form': form,
        'modal_title': 'Record New Sale',
        'form_action': reverse('create_sale'),
        'submit_text': 'Submit',
    }
    return render(request, 'sales/partials/record_sale_modal.html', context)

@require_POST
@login_required
def calculate_total(request):
    form = SaleForm(request.POST)
    product_id = request.POST.get('product')
    quantity_str = request.POST.get('quantity', '').strip()

    price = 0
    total = 0

    if product_id:
        try:
            product = Product.objects.get(pk=product_id)
            qty = int(quantity_str) if quantity_str else 1
            price = float(product.price)
            total = price * qty
        except (Product.DoesNotExist, ValueError, TypeError):
            form.add_error('quantity', "Invalid input")

    context = {
        'price': price,
        'total': total,
        'form': form,
    }

    return render(request, 'sales/partials/_combined_total_and_errors.html', context)