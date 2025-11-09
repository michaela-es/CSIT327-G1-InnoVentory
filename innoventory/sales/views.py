from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator
from django.db.models import Sum, Q
from django.utils import timezone
import json

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
            
            sale_data = {
                'product_sold': product,
                'product_qty': qty,
                'total': total,
                'sales_type': sales_type,
                'sold_by': request.user,
            }
            
            # setting initial balance
            if sales_type == 'credit':
                sale_data['balance'] = total
                sale_data['amount_paid'] = 0
                sale_data['payment_status'] = 'pending'
            
            sale = Sale.objects.create(**sale_data)

            Stocks.objects.create(
                product=product,
                qty=qty,
                type=Stocks.OUT,
                remarks=f"SOLD"
            )

            return HttpResponse(
                status=204,
                headers={
                    'HX-Trigger': json.dumps({
                        "showMessage": "Sale recorded successfully!",
                        "reloadPage": True
                    })
                }
            )
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
    sales_list = Sale.objects.order_by('-sales_date')
    products_list = Product.objects.all().order_by('name')

    prod_page_number = request.GET.get('prod_page', 1)
    sale_page_number = request.GET.get('sale_page', 1)

    product_paginator = Paginator(products_list, 10)
    products_page_obj = product_paginator.get_page(prod_page_number)

    sales_paginator = Paginator(sales_list, 10)  # 10 items per page
    sales_page_obj = sales_paginator.get_page(sale_page_number)

    context = {
        'products_page_obj': products_page_obj,
        'sales_page_obj': sales_page_obj,
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

@login_required
def credit_management(request):
    try:
        credit_sales = Sale.objects.filter(sales_type='credit').select_related('product_sold').order_by('-sales_date')
        
        status_filter = request.GET.get('status', 'all')
        due_date_filter = request.GET.get('due_date', '')
        search_query = request.GET.get('search', '')
        
        if status_filter == 'active':
            credit_sales = credit_sales.filter(
                Q(payment_status__in=['pending', 'partial']) | 
                Q(payment_status__isnull=True)
            )
        elif status_filter == 'overdue':
            credit_sales = credit_sales.filter(payment_status='overdue')
        elif status_filter != 'all':
            credit_sales = credit_sales.filter(payment_status=status_filter)
        
        today = timezone.now().date()
        if due_date_filter:
            if due_date_filter == 'today':
                credit_sales = credit_sales.filter(due_date=today)
            elif due_date_filter == 'week':
                end_date = today + timezone.timedelta(days=7)
                credit_sales = credit_sales.filter(due_date__range=[today, end_date])
            elif due_date_filter == 'month':
                end_date = today + timezone.timedelta(days=30)
                credit_sales = credit_sales.filter(due_date__range=[today, end_date])
            elif due_date_filter == 'overdue':
                credit_sales = credit_sales.filter(
                    Q(due_date__lt=today) & 
                    (Q(balance__gt=0) | Q(balance__isnull=True))
                )
        
        if search_query:
            credit_sales = credit_sales.filter(
                Q(customer_name__icontains=search_query) |
                Q(product_sold__name__icontains=search_query)
            )
        
        overdue_sales = credit_sales.filter(
            Q(due_date__lt=today) & 
            (Q(balance__gt=0) | Q(balance__isnull=True))
        ).exclude(payment_status='overdue')
        
        for sale in overdue_sales:
            sale.payment_status = 'overdue'
            sale.save()
        
        total_balance = 0
        total_receivable = 0
        
        for sale in credit_sales:
            total_receivable += sale.total
            # Handle None balance values
            balance = sale.balance if sale.balance is not None else sale.total
            total_balance += balance
        
        paginator = Paginator(credit_sales, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'page_obj': page_obj,
            'status_filter': status_filter,
            'due_date_filter': due_date_filter,
            'search_query': search_query,
            'total_balance': total_balance,
            'total_receivable': total_receivable,
            'today': today,
        }
        return render(request, 'sales/credit_management.html', context)
        
    except Exception as e:
        print(f"Error in credit_management: {str(e)}")
        credit_sales = Sale.objects.filter(sales_type='credit')[:50]  # Limit to prevent huge queries
        
        context = {
            'credit_sales': credit_sales,
            'total_balance': sum(sale.balance or sale.total for sale in credit_sales),
            'total_receivable': sum(sale.total for sale in credit_sales),
            'today': timezone.now().date(),
            'error_occurred': True,
        }
        return render(request, 'sales/credit_management.html', context)

@login_required
def record_payment(request, sale_id):
    sale = get_object_or_404(Sale, sale_id=sale_id)
    
    if request.method == 'POST':
        payment_amount = float(request.POST.get('payment_amount', 0))
        payment_date = request.POST.get('payment_date')
        payment_notes = request.POST.get('payment_notes', '')
        
        if payment_amount > 0 and payment_amount <= sale.balance:
            sale.amount_paid += payment_amount
            sale.balance = sale.total - sale.amount_paid
            
            if payment_notes:
                note_entry = f"{payment_date} - Payment: ₱{payment_amount} - {payment_notes}"
                if sale.payment_notes:
                    sale.payment_notes += f"\n{note_entry}"
                else:
                    sale.payment_notes = note_entry
            
            sale.save()
            
            return HttpResponse(
                status=204,
                headers={
                    'HX-Trigger': json.dumps({
                        "creditListChanged": None,
                        "showMessage": f"Payment of ₱{payment_amount} recorded successfully"
                    })
                }
            )
        else:
            return JsonResponse({
                'success': False,
                'message': 'Invalid payment amount'
            })
    
    return render(request, 'sales/partials/payment_modal.html', {
        'sale': sale,
        'today': timezone.now().date()
    })

@login_required
def sale_modal(request, sale_id=None):
    sale = None
    if sale_id:
        sale = get_object_or_404(Sale, sale_id=sale_id)
    
    if request.method == 'POST':
        form = SaleForm(request.POST, instance=sale)
        if form.is_valid():
            sale = form.save(commit=False)
            if not sale.sold_by:
                sale.sold_by = request.user
            sale.save()
            
            # Update stock
            if not sale_id:
                Stocks.objects.create(
                    product=sale.product_sold,
                    qty=sale.product_qty,
                    type=Stocks.OUT,
                    remarks=f"SOLD"
                )
            
            return HttpResponse(
                status=204,
                headers={
                    'HX-Trigger': json.dumps({
                        "saleListChanged": None,
                        "showMessage": f"Sale {'updated' if sale_id else 'created'} successfully"
                    })
                }
            )
    else:
        form = SaleForm(instance=sale)
    
    context = {
        'form': form,
        'sale': sale,
        'modal_title': 'Edit Sale' if sale else 'Record New Sale',
        'submit_text': 'Update Sale' if sale else 'Submit Sale',
    }
    return render(request, 'sales/partials/sale_modal.html', context)