from django.shortcuts import render
from django.db.models import Sum
from django.utils.dateparse import parse_date
from sales.models import Sale
from products.models import Product, Category
from stocks.models import Stocks
from datetime import datetime, timedelta


def _parse_date_or_none(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except Exception:
        return None


def report_dashboard(request):
    # Filters
    start_date = _parse_date_or_none(request.GET.get('start_date'))
    end_date = _parse_date_or_none(request.GET.get('end_date'))
    product_q = request.GET.get('product', '').strip()
    category_q = request.GET.get('category', '').strip()
    stock_type = request.GET.get('stock_type', '').strip()

    sales_qs = Sale.objects.select_related('product_sold')

    if start_date:
        sales_qs = sales_qs.filter(sales_date__date__gte=start_date)
    if end_date:
        sales_qs = sales_qs.filter(sales_date__date__lte=end_date)
    if product_q:
        sales_qs = sales_qs.filter(product_sold__name__icontains=product_q)
    if category_q:
        sales_qs = sales_qs.filter(product_sold__category__name__icontains=category_q)

    # Aggregate per-date summary
    # Collect the distinct dates in the queryset (by date)
    date_list = (
        sales_qs
        .values_list('sales_date__date', flat=True)
        .distinct()
        .order_by('sales_date__date')
    )

    summaries = []
    for d in date_list:
        day_qs = sales_qs.filter(sales_date__date=d)
        total_sales = day_qs.count()
        total_revenue = day_qs.aggregate(total=Sum('total'))['total'] or 0

        # top product for the date
        top = (
            day_qs.values('product_sold__name')
            .annotate(qty=Sum('product_qty'))
            .order_by('-qty')
            .first()
        )
        top_product = top['product_sold__name'] if top else ''

        summaries.append({
            'date': d,
            'total_sales': total_sales,
            'total_revenue': total_revenue,
            'top_product': top_product,
        })

    # Provide choices for filters
    products = Product.objects.order_by('name')[:200]
    categories = Category.objects.order_by('name')

    context = {
        'summaries': summaries,
        'products': products,
        'categories': categories,
        'filters': {
            'start_date': start_date,
            'end_date': end_date,
            'product': product_q,
            'category': category_q,
            'stock_type': stock_type,
        }
    }

    return render(request, 'reports/report_dashboard.html', context)
