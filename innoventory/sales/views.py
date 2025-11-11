from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator
from django.db.models import Sum, Q
from django.utils import timezone
import json
from django.contrib import messages


from products.models import Product
from .forms import SaleForm
from .models import Sale
from products.models import StockTransaction
from django.core.paginator import Paginator
from django.db.models import Sum, Avg, Count, F


@login_required
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

            if sales_type == 'credit':
                sale_data['balance'] = total
                sale_data['amount_paid'] = 0
                sale_data['payment_status'] = 'pending'

                due_date_str = request.POST.get('due_date')
                if due_date_str:
                    try:
                        from datetime import datetime
                        sale_data['due_date'] = datetime.strptime(due_date_str, '%Y-%m-%d').date()
                    except (ValueError, TypeError):
                        sale_data['due_date'] = None

                sale_data['customer_name'] = request.POST.get('customer_name', '')

            sale = Sale.objects.create(**sale_data)

            StockTransaction.objects.create(
                product=product,
                quantity=qty,
                transaction_type='OUT',
                remarks=f"SALE - {sales_type.upper()} - Sale ID: {sale.sale_id}"
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

    sales_paginator = Paginator(sales_list, 10)
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
        credit_sales = Sale.objects.filter(sales_type='credit').select_related('product_sold')

        status_filter = request.GET.get('status', 'all')
        due_date_filter = request.GET.get('due_date', '')
        search_query = request.GET.get('search', '')
        today = timezone.now().date()

        status_filters = {
            'active': Q(payment_status__in=['pending', 'partial']) | Q(payment_status__isnull=True),
            'overdue': Q(payment_status='overdue'),
        }
        if status_filter in status_filters:
            credit_sales = credit_sales.filter(status_filters[status_filter])
        elif status_filter != 'all':
            credit_sales = credit_sales.filter(payment_status=status_filter)

        due_date_ranges = {
            'today': [today, today],
            'week': [today, today + timezone.timedelta(days=7)],
            'month': [today, today + timezone.timedelta(days=30)],
            'overdue': Q(due_date__lt=today) & (Q(balance__gt=0) | Q(balance__isnull=True))
        }
        if due_date_filter in due_date_ranges:
            if due_date_filter == 'overdue':
                credit_sales = credit_sales.filter(due_date_ranges[due_date_filter])
            else:
                credit_sales = credit_sales.filter(due_date__range=due_date_ranges[due_date_filter])

        if search_query:
            credit_sales = credit_sales.filter(
                Q(customer_name__icontains=search_query) | Q(product_sold__name__icontains=search_query)
            )

        overdue_sales_to_update = Sale.objects.filter(
            sales_type='credit',
            due_date__lt=today,
            balance__gt=0
        ).exclude(payment_status='overdue')
        overdue_sales_to_update.update(payment_status='overdue')

        overdue_summary = credit_sales.filter(
            Q(due_date__lt=today) & (Q(balance__gt=0) | Q(balance__isnull=True))
        )[:6]

        for sale in overdue_summary:
            sale.days_overdue = (today - sale.due_date).days

        total_balance = sum(sale.balance or sale.total for sale in credit_sales)
        total_receivable = sum(sale.total for sale in credit_sales)

        paginator = Paginator(credit_sales.order_by('-sales_date'), 10)
        page_obj = paginator.get_page(request.GET.get('page'))

        context = {
            'page_obj': page_obj,
            'status_filter': status_filter,
            'due_date_filter': due_date_filter,
            'search_query': search_query,
            'total_balance': total_balance,
            'total_receivable': total_receivable,
            'overdue_summary': overdue_summary,
            'today': today,
        }
        return render(request, 'sales/credit_management.html', context)

    except Exception as e:
        print(f"Error in credit_management: {str(e)}")
        today = timezone.now().date()
        credit_sales_error = Sale.objects.filter(sales_type='credit')

        overdue_summary = credit_sales_error.filter(
            Q(due_date__lt=today) & (Q(balance__gt=0) | Q(balance__isnull=True))
        )[:6]

        for sale in overdue_summary:
            sale.days_overdue = (today - sale.due_date).days

        credit_sales_error = credit_sales_error[:50]

        context = {
            'credit_sales': credit_sales_error,
            'total_balance': sum(sale.balance or sale.total for sale in credit_sales_error),
            'total_receivable': sum(sale.total for sale in credit_sales_error),
            'overdue_summary': overdue_summary,
            'today': today,
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

        if 0 < payment_amount <= sale.balance:
            sale.amount_paid += payment_amount
            sale.balance = sale.total - sale.amount_paid

            note_entry = f"{payment_date} - Payment: ₱{payment_amount} - {payment_notes}"
            sale.payment_notes = f"{sale.payment_notes}\n{note_entry}".strip() if sale.payment_notes else note_entry

            sale.save()

            return HttpResponse(status=204, headers={
                'HX-Trigger': json.dumps({
                    "creditListChanged": None,
                    "showMessage": f"Payment of ₱{payment_amount} recorded successfully"
                })
            })

        return JsonResponse({'success': False, 'message': 'Invalid payment amount'})

    return render(request, 'sales/partials/payment_modal.html', {'sale': sale, 'today': timezone.now().date()})

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

@login_required
def delete_credit_sale(request, sale_id):
    sale = get_object_or_404(Sale, sale_id=sale_id, sales_type='credit')

    if request.method == 'POST':
        customer_name = sale.customer_name or "Unknown Customer"

        StockTransaction.objects.create(
            product=sale.product_sold,
            quantity=sale.product_qty,
            transaction_type='IN',
            remarks=f"CREDIT SALE DELETED - Sale ID: {sale.sale_id} - Customer: {customer_name}"
        )

        sale.delete()
        messages.success(request, f'Credit sale for {customer_name} deleted successfully!')
        return redirect('credit_management')

    messages.error(request, 'Invalid request method.')
    return redirect('credit_management')

@login_required
def edit_credit_sale_modal(request, sale_id):
    sale = get_object_or_404(Sale, sale_id=sale_id, sales_type='credit')

    if request.method == 'POST':
        form = SaleForm(request.POST, instance=sale)
        if form.is_valid():
            updated_sale = form.save(commit=False)

            if 'amount_paid' in form.changed_data:
                updated_sale.balance = updated_sale.total - updated_sale.amount_paid

            updated_sale.save()

            return HttpResponse('''
                <script>
                    document.getElementById("modal-container").innerHTML = "";
                    window.location.reload();
                </script>
            ''')
        else:
            print("Form errors:", form.errors)
    else:
        form = SaleForm(instance=sale)

    context = {
        'form': form,
        'sale': sale,
        'modal_title': 'Edit Credit Sale',
        'form_action': f'/sales/credits/edit/{sale.sale_id}/',
        'submit_text': 'Update Credit Sale'
    }
    return render(request, 'sales/partials/credit_sale_edit_modal.html', context)