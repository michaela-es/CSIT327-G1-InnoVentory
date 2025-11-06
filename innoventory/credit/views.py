from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from .forms import LinkSaleForm
from .models import Creditor, Credit
from sales.models import Sale


@login_required
def creditors_list(request):
    creditors = Creditor.objects.all().prefetch_related('credits')
    unlinked_credit_sales = Sale.objects.filter(
        sales_type='credit'
    ).exclude(
        credit_record__isnull=False
    )
    return render(request, 'creditors_list.html', {
        'creditors': creditors,
        'unlinked_credit_sales': unlinked_credit_sales
    })


@login_required
def link_sale_modal(request, sale_id):
    sale = get_object_or_404(Sale, pk=sale_id, sales_type='credit')

    if hasattr(sale, 'credit_record'):
        return render(request, 'partials/error_modal.html', {
            'error_message': 'This sale is already linked to a creditor'
        })

    default_due_date = (timezone.now() + timedelta(days=30)).strftime('%Y-%m-%d')
    form = LinkSaleForm(initial={'due_date': default_due_date})

    return render(request, 'partials/link_sale_modal.html', {
        'sale': sale,
        'form': form
    })


@require_POST
@login_required
def link_sale_to_creditor(request, sale_id):
    sale = get_object_or_404(Sale, pk=sale_id, sales_type='credit')

    if hasattr(sale, 'credit_record'):
        messages.error(request, 'This sale is already linked to a creditor')
        return redirect('creditors_list')

    form = LinkSaleForm(request.POST)
    if form.is_valid():
        creditor = form.cleaned_data['creditor']
        due_date = form.cleaned_data['due_date']

        Credit.objects.create(
            creditor=creditor,
            original_sale=sale,
            original_amount=sale.total,
            due_date=due_date
        )

        messages.success(request, f'Sale #{sale.sale_id} linked to {creditor.name}')
        return redirect('creditors_list')

    for field, errors in form.errors.items():
        for error in errors:
            messages.error(request, f"{form.fields[field].label}: {error}")

    return redirect('creditors_list')


@require_POST
@login_required
def mark_credit_paid(request, credit_id):
    credit = get_object_or_404(Credit, pk=credit_id)

    if credit.mark_as_paid():
        messages.success(request, f'Credit #{credit.credit_id} marked as paid')
    else:
        messages.warning(request, f'Credit #{credit.credit_id} is already paid')

    return redirect('creditors_list')


@require_POST
@login_required
def make_payment(request, credit_id):
    credit = get_object_or_404(Credit, pk=credit_id)

    try:
        payment_amount = float(request.POST.get('payment_amount', 0))
        payment_method = request.POST.get('payment_method', 'cash')
        payment_notes = request.POST.get('payment_notes', '')

        if payment_amount <= 0:
            messages.error(request, 'Payment amount must be greater than 0')
        elif payment_amount > credit.remaining_balance:
            messages.error(request,
                           f'Payment amount cannot exceed remaining balance of ₱{credit.remaining_balance:,.2f}')
        else:
            credit.make_payment(payment_amount)
            messages.success(request, f'Payment of ₱{payment_amount:,.2f} applied to credit #{credit.credit_id}')

    except ValueError:
        messages.error(request, 'Invalid payment amount')

    return redirect('creditors_list')


@login_required
def payment_modal(request, credit_id):
    credit = get_object_or_404(Credit, pk=credit_id)
    return render(request, "partials/payment_modal.html", {'credit': credit})