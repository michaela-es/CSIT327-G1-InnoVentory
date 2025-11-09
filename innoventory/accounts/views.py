from django.contrib.auth import views as auth_views
from django.contrib import messages
from django.shortcuts import render, redirect
from .forms import RegisterForm
from django.db.models import Sum, Count, Q
from products.models import Product
from sales.models import Sale
from stocks.models import Stocks
from django.db.models.functions import TruncDate
from products.models import Product, Category



def root_redirect(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    else:
        return redirect('register')

def dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login')

    role = request.user.role

    if role == 'admin':
        return redirect('admin_dashboard')
    elif role == 'staff':
        return redirect('staff_dashboard')

    else:
        # Fallback for general users or unassigned roles
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
    revenue_data = [float(item['daily_revenue']) for item in sales_trend]

    # 3. Business Insights
    if len(sales_trend) >= 2:
        # Compare last two days
        today = sales_trend[len(sales_trend)-1]
        yesterday = sales_trend[len(sales_trend)-2]
        revenue_change = ((today['daily_revenue'] - yesterday['daily_revenue']) / yesterday['daily_revenue'] * 100
                         if yesterday['daily_revenue'] else 0)
        sales_change = ((today['daily_sales'] - yesterday['daily_sales']) / yesterday['daily_sales'] * 100
                       if yesterday['daily_sales'] else 0)
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
    return render(request, 'accounts/staff_dashboard.html')

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