from django.contrib.auth import views as auth_views
from django.contrib import messages
from django.shortcuts import render, redirect
from .forms import RegisterForm
from django.db.models import Sum, Count, Q
from products.models import Product
from sales.models import Sale
from stocks.models import Stocks
from django.db.models.functions import TruncDate



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
    # Total Revenue
    total_revenue = Sale.objects.aggregate(total=Sum('total'))['total'] or 0

    # Low Stock Alerts
    low_stock_count = Product.objects.filter(stock_quantity__lte=10).count()

    # Total Sales
    total_sales_count = Sale.objects.count()

    # Pending Credits
    pending_credits = Sale.objects.filter(sales_type="CREDIT").count()

    # Top Selling Products
    top_selling = (
        Sale.objects.values('product_sold__name')
        .annotate(total_qty=Sum('product_qty'))
        .order_by('-total_qty')[:3]
    )

    # --- Sales Chart Data ---
    sales_data = (
        Sale.objects
        .annotate(day=TruncDate('sales_date'))
        .values('day')
        .annotate(total_sales=Sum('total'))
        .order_by('day')
    )
    sales_dates = [item['day'].strftime('%Y-%m-%d') for item in sales_data]
    sales_totals = [float(item['total_sales']) for item in sales_data]

    stock_in_data = (
        Stocks.objects.filter(type=Stocks.IN)
        .annotate(day=TruncDate('date'))
        .values('day')
        .annotate(total_in=Sum('qty'))
        .order_by('day')
    )

    stock_out_data = (
        Stocks.objects.filter(type=Stocks.OUT)
        .annotate(day=TruncDate('date'))
        .values('day')
        .annotate(total_out=Sum('qty'))
        .order_by('day')
    )

    # Merge dates for chart
    all_dates = sorted(list(set(
        [item['day'] for item in stock_in_data] +
        [item['day'] for item in stock_out_data]
    )))

    stock_in_totals_dict = {item['day']: item['total_in'] for item in stock_in_data}
    stock_out_totals_dict = {item['day']: item['total_out'] for item in stock_out_data}

    stock_dates = [d.strftime('%Y-%m-%d') for d in all_dates]
    stock_in_totals = [stock_in_totals_dict.get(d, 0) for d in all_dates]
    stock_out_totals = [stock_out_totals_dict.get(d, 0) for d in all_dates]

    context = {
        'total_revenue': total_revenue,
        'low_stock_count': low_stock_count,
        'total_sales_count': total_sales_count,
        'pending_credits': pending_credits,
        'top_selling': top_selling,
        'sales_dates': sales_dates,
        'sales_totals': sales_totals,
        'stock_dates': stock_dates,
        'stock_in_totals': stock_in_totals,
        'stock_out_totals': stock_out_totals,
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