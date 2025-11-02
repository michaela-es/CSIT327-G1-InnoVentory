from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from sales.models import Sale
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
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
def link_sale_to_creditor(request, sale_id):
    sale = get_object_or_404(Sale, pk=sale_id, sales_type='credit')

    if request.method == 'POST':
        creditor_id = request.POST.get('creditor_id')
        due_date = request.POST.get('due_date')

        creditor = get_object_or_404(Creditor, pk=creditor_id)

        if hasattr(sale, 'credit_record'):
            messages.error(request, 'This sale is already linked to a creditor')
            return redirect('creditors_list')

        credit = Credit.objects.create(
            creditor=creditor,
            original_sale=sale,
            original_amount=sale.total,
            due_date=due_date
        )

        messages.success(request, f'Sale #{sale.sale_id} linked to {creditor.name}')
        return redirect('creditors_list')

    creditors = Creditor.objects.all()
    default_due_date = (timezone.now() + timedelta(days=30)).strftime('%Y-%m-%d')

    return render(request, 'link_sale_to_creditor.html', {
        'sale': sale,
        'creditors': creditors,
        'default_due_date': default_due_date
    })


@require_POST
def mark_credit_paid(request, credit_id):
    credit = get_object_or_404(Credit, pk=credit_id)

    if credit.mark_as_paid():
        messages.success(request, f'Credit #{credit.credit_id} marked as paid')
    else:
        messages.warning(request, f'Credit #{credit.credit_id} is already paid')

    return redirect('creditors_list')

@require_POST
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

@login_required
def link_sale_modal(request, sale_id):
    try:
        sale = get_object_or_404(Sale, pk=sale_id, sales_type='credit')
        creditors = Creditor.objects.all()
        default_due_date = (timezone.now() + timedelta(days=30)).strftime('%Y-%m-%d')

        creditor_choices = [('', '---------'), ('__new__', 'Add New Creditor')]
        creditor_choices.extend([(cred.creditor_id, cred.name) for cred in creditors.order_by('name')])

        return render(request, 'partials/link_sale_modal.html', {
            'sale': sale,
            'creditors': creditor_choices,
            'default_due_date': default_due_date,
        })
    except Exception as e:
        from django.http import HttpResponse
        return HttpResponse(f'Error: {str(e)}', status=500)