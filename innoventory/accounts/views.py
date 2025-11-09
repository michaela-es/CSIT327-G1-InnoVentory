from django.contrib.auth import views as auth_views
from django.contrib import messages
from django.shortcuts import render, redirect
from .forms import RegisterForm
from django.db.models import Sum, Count, Q
from products.models import Product
from sales.models import Sale
from stocks.models import Stocks
from django.db.models.functions import TruncDate, TruncHour
from django.utils import timezone
from datetime import timedelta, datetime, time
from products.models import Product, Category



def root_redirect(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    else:
        return redirect('register')

def dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login')

    role = getattr(request.user, 'role', None)

    if role == 'admin':
        return redirect('admin_dashboard')
    elif role == 'staff':
        return redirect('staff_dashboard')

    # Fallback for other users
    return render(request, 'accounts/generic_user_dashboard.html', {})


def admin_dashboard(request):
    # Get date filters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    product_q = request.GET.get('product', '').strip()
    category_q = request.GET.get('category', '').strip()

    # Base queryset with filters
    sales_qs = Sale.objects.select_related('product_sold', 'product_sold__category')
    if start_date:
        sales_qs = sales_qs.filter(sales_date__date__gte=start_date)
    if end_date:
        sales_qs = sales_qs.filter(sales_date__date__lte=end_date)
    if product_q:
        sales_qs = sales_qs.filter(product_sold__name__icontains=product_q)
    if category_q:
        sales_qs = sales_qs.filter(product_sold__category__name__icontains=category_q)

    # 1. High-Level KPIs
    total_revenue = sales_qs.aggregate(total=Sum('total'))['total'] or 0
    total_sales = sales_qs.count()
    unique_products = sales_qs.values('product_sold').distinct().count()
    low_stock_count = Product.objects.filter(stock_quantity__lte=10).count()
    pending_credits = sales_qs.filter(sales_type='credit').count()

    # Top selling products overall
    top_selling = (
        sales_qs
        .values('product_sold__name', 'product_sold__category__name')
        .annotate(
            total_qty=Sum('product_qty'),
            total_revenue=Sum('total')
        )
        .order_by('-total_qty')[:3]
    )

    # Top performing category
    top_category = (
        sales_qs
        .values('product_sold__category__name')
        .annotate(
            total_revenue=Sum('total'),
            total_sales=Count('sale_id')
        )
        .order_by('-total_revenue')
        .first()
    )

    # 2. Chart Data - Daily Sales & Revenue Trends
    sales_trend = (
        sales_qs
        .annotate(date=TruncDate('sales_date'))
        .values('date')
        .annotate(
            daily_sales=Count('sale_id'),
            daily_revenue=Sum('total')
        )
        .order_by('date')
    )

    # Prepare chart data
    chart_dates = [item['date'].strftime('%Y-%m-%d') for item in sales_trend]
    sales_data = [item['daily_sales'] for item in sales_trend]
    revenue_data = [float(item['daily_revenue'] or 0) for item in sales_trend]

    # 3. Business Insights
    if len(sales_trend) >= 2:
        # Compare last two days
        today_item = sales_trend[-1]
        yesterday_item = sales_trend[-2]
        revenue_change = ((today_item['daily_revenue'] - yesterday_item['daily_revenue']) / yesterday_item['daily_revenue'] * 100
                         if yesterday_item['daily_revenue'] else 0)
        sales_change = ((today_item['daily_sales'] - yesterday_item['daily_sales']) / yesterday_item['daily_sales'] * 100
                       if yesterday_item['daily_sales'] else 0)
    else:
        revenue_change = 0
        sales_change = 0

    # Low performing products (no sales in period)
    low_performing = (
        Product.objects
        .exclude(sales__in=sales_qs)
        .values('name', 'category__name', 'stock_quantity')
        .order_by('name')[:5]
    )

    context = {
        # KPIs
        'total_revenue': total_revenue,
        'total_sales': total_sales,
        'unique_products': unique_products,
        'low_stock_count': low_stock_count,
        'pending_credits': pending_credits,
        
        # Top performers
        'top_selling': top_selling,
        'top_category': top_category,
        
        # Chart data
        'chart_dates': chart_dates,
        'sales_data': sales_data,
        'revenue_data': revenue_data,
        
        # Insights
        'revenue_change': revenue_change,
        'sales_change': sales_change,
        'low_performing': low_performing,
        
        # Filters
        'filters': {
            'start_date': start_date,
            'end_date': end_date,
            'product': product_q,
            'category': category_q,
        },
        
        # Filter choices
        'categories': Category.objects.order_by('name'),
        'products': Product.objects.order_by('name')[:100],
    }

    return render(request, 'accounts/admin_dashboard.html', context)


def staff_dashboard(request):
    # Get today's date (in local timezone)
    now = timezone.localtime()
    today = now.date()
    yesterday = today - timedelta(days=1)

    # Today's sales and revenue
    today_sales = Sale.objects.filter(sales_date__date=today)
    today_sales_count = today_sales.count()
    today_revenue = today_sales.aggregate(total=Sum('total'))['total'] or 0

    # Yesterday's sales and revenue for comparison
    yesterday_sales = Sale.objects.filter(sales_date__date=yesterday)
    yesterday_sales_count = yesterday_sales.count()
    yesterday_revenue = yesterday_sales.aggregate(total=Sum('total'))['total'] or 0

    # Calculate percentage changes (guard divide-by-zero)
    sales_change = ((today_sales_count - yesterday_sales_count) / yesterday_sales_count * 100
                    if yesterday_sales_count else 0)
    revenue_change = ((today_revenue - yesterday_revenue) / yesterday_revenue * 100
                      if yesterday_revenue else 0)

    # Stock alerts
    low_stock_products = Product.objects.filter(stock_quantity__lte=10).order_by('stock_quantity')
    low_stock_count = low_stock_products.count()
    out_of_stock = low_stock_products.filter(stock_quantity=0).count()

    # Pending credits
    pending_credits = Sale.objects.filter(sales_type='credit')

    # Recent activity
    recent_sales = Sale.objects.select_related('product_sold').order_by('-sales_date')[:5]
    recent_stocks = Stocks.objects.select_related('product').order_by('-date')[:5]

    # Chart data - today's hourly trends (use TruncHour and the correct PK 'sale_id')
    today_start = timezone.make_aware(datetime.combine(today, time.min))
    today_end = timezone.make_aware(datetime.combine(today, time.max))

    hourly_sales = (
        Sale.objects
        .filter(sales_date__range=(today_start, today_end))
        .annotate(hour=TruncHour('sales_date'))
        .values('hour')
        .annotate(
            sales_count=Count('sale_id'),
            revenue=Sum('total')
        )
        .order_by('hour')
    )

    # Prepare chart data
    chart_dates = [h['hour'].strftime('%H:00') for h in hourly_sales]
    sales_data = [h['sales_count'] for h in hourly_sales]
    revenue_data = [float(h['revenue'] or 0) for h in hourly_sales]

    context = {
        'today_sales_count': today_sales_count,
        'today_revenue': today_revenue,
        'sales_change': sales_change,
        'revenue_change': revenue_change,
        'low_stock_count': low_stock_count,
        'out_of_stock': out_of_stock,
        'low_stock_products': low_stock_products,
        'pending_credits': pending_credits,
        'recent_sales': recent_sales,
        'recent_stocks': recent_stocks,
        'chart_dates': chart_dates,
        'sales_data': sales_data,
        'revenue_data': revenue_data,
    }

    return render(request, 'accounts/staff_dashboard.html', context)


def custom_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return auth_views.LoginView.as_view(template_name='accounts/login.html')(request)


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Registration successful! You can now log in.')
                return redirect('login')
            except Exception as e:
                messages.error(request, f'Error during registration: {str(e)}')
        else:
            print("Form errors:", form.errors)
            messages.error(request, 'Please correct the errors below.')
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})