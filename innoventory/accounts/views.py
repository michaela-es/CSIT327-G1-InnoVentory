from django.contrib.auth import views as auth_views
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from .models import CustomUser
from .forms import RegisterForm
from django.db.models import Sum, Count, Q
from products.models import Product
from sales.models import Sale
from django.db.models.functions import TruncDate, TruncHour
from django.utils import timezone
from datetime import timedelta, datetime, time
from products.models import Product, StockTransaction, Category
from .decorators import admin_required

def unauthorized_view(request, exception=None):
    return render(request, "unauthorized.html", status=403)

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

def get_overdue_summary(limit=5):
    today = timezone.localtime().date()
    overdue = Sale.objects.filter(
        sales_type='credit',
        due_date__lt=today,
        balance__gt=0
    ).select_related('product_sold')[:limit]

    for sale in overdue:
        sale.days_overdue_calculated = (today - sale.due_date).days if sale.due_date else None

    return overdue


@admin_required
def admin_dashboard(request):
    # Get date filters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    product_q = request.GET.get('product', '').strip()
    category_q = request.GET.get('category', '').strip()

    sales_qs = Sale.objects.select_related('product_sold', 'product_sold__category')
    if start_date:
        sales_qs = sales_qs.filter(sales_date__date__gte=start_date)
    if end_date:
        sales_qs = sales_qs.filter(sales_date__date__lte=end_date)
    if product_q:
        sales_qs = sales_qs.filter(product_sold__name__icontains=product_q)
    if category_q:
        sales_qs = sales_qs.filter(product_sold__category__name__icontains=category_q)

    # High-Level KPIs
    total_revenue = sales_qs.aggregate(total=Sum('total'))['total'] or 0
    total_sales = sales_qs.count()
    unique_products = sales_qs.values('product_sold').distinct().count()
    low_stock_products = Product.objects.low_stock().order_by('stock_quantity')
    low_stock_count = low_stock_products.count()
    pending_credits = Sale.objects.filter(
        sales_type='credit'
    ).exclude(
        payment_status='paid'
    ).count()

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

    # Chart Data - Daily Sales & Revenue Trends
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

    chart_dates = [item['date'].strftime('%Y-%m-%d') for item in sales_trend]
    sales_data = [item['daily_sales'] for item in sales_trend]
    revenue_data = [float(item['daily_revenue'] or 0) for item in sales_trend]

    # Business Insights
    if len(sales_trend) >= 2:
        # Compare last two days
        sales_trend = list(sales_trend)
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

    today = timezone.now().date()
    overdue_summary = get_overdue_summary()

    context = {
        'overdue_summary': overdue_summary,
        'total_revenue': total_revenue,
        'total_sales': total_sales,
        'unique_products': unique_products,
        'low_stock_count': low_stock_count,
        'pending_credits': pending_credits,
        
        'top_selling': top_selling,
        'top_category': top_category,
        
        'chart_dates': chart_dates,
        'sales_data': sales_data,
        'revenue_data': revenue_data,
        
        'revenue_change': revenue_change,
        'sales_change': sales_change,
        'low_performing': low_performing,
        
        'filters': {
            'start_date': start_date if start_date else '',
            'end_date': end_date if end_date else '',
            'product': product_q,
            'category': category_q,
        },
        
        'categories': Category.objects.order_by('name'),
        'products': Product.objects.order_by('name')[:100],
    }

    return render(request, 'accounts/admin_dashboard.html', context)


def staff_dashboard(request):
    # Get today's date (in local timezone)
    now = timezone.localtime()
    today = now.date()
    yesterday = today - timedelta(days=1)

    today_sales = Sale.objects.filter(sales_date__date=today)
    today_sales_count = today_sales.count()
    today_revenue = today_sales.aggregate(total=Sum('total'))['total'] or 0

    yesterday_sales = Sale.objects.filter(sales_date__date=yesterday)
    yesterday_sales_count = yesterday_sales.count()
    yesterday_revenue = yesterday_sales.aggregate(total=Sum('total'))['total'] or 0

    sales_change = ((today_sales_count - yesterday_sales_count) / yesterday_sales_count * 100
                    if yesterday_sales_count else 0)
    revenue_change = ((today_revenue - yesterday_revenue) / yesterday_revenue * 100
                      if yesterday_revenue else 0)

    low_stock_products = Product.objects.low_stock().order_by('stock_quantity')
    low_stock_count = low_stock_products.count()
    out_of_stock = low_stock_products.filter(stock_quantity=0).count()
    overdue_summary = get_overdue_summary()

    pending_credits = Sale.objects.filter(
        sales_type='credit'
    ).exclude(
        payment_status='paid'
    ).count()

    recent_sales = Sale.objects.select_related('product_sold').order_by('-sales_date')[:5]
    recent_stocks = StockTransaction.objects.select_related('product').order_by('-date')[:5]

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
        'overdue_summary': overdue_summary
    }

    return render(request, 'accounts/staff_dashboard.html', context)


def custom_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return auth_views.LoginView.as_view(template_name='accounts/login.html')(request)


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        print("=== REGISTRATION DEBUG ===")
        print("Form data:", request.POST)
        print("Form is valid:", form.is_valid())

        if not form.is_valid():
            print("Form errors:", form.errors.as_json())
            for field, errors in form.errors.items():
                print(f"Field '{field}': {errors}")
        else:
            print("Form is valid, attempting to save...")

        if form.is_valid():
            try:
                user = form.save()
                print("=== USER SAVED SUCCESSFULLY ===")
                print(f"User: {user.username}, Email: {user.email}, Phone: {user.phone_number}")
                messages.success(request, 'Registration successful! You can now log in.', extra_tags='registration')
                return redirect('login')
            except Exception as e:
                print(f"=== SAVE ERROR: {e} ===")
                messages.error(request, f'Error during registration: {str(e)}', extra_tags='registration')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


@admin_required
def user_list(request):
    users = CustomUser.objects.all().order_by('-date_joined')

    search_query = request.GET.get('search', '')

    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone_number__icontains=search_query)
        )

    users = users.annotate(sales_count=Count('sale'))
    context = {
        'users': users,
        'search_query': search_query,
        'active_page': 'user_management'
    }
    return render(request, 'accounts/user_list.html', context)

@admin_required
def delete_user(request, user_id):
    user_to_delete = get_object_or_404(CustomUser, id=user_id)

    if user_to_delete == request.user:
        messages.error(request, "You cannot delete your own account.", extra_tags='user_management')
        return redirect('user_list')
    
    if user_to_delete.get_sales_count() == 0:
        user_to_delete.delete()
        messages.success(request, f'User {user_to_delete.username} has been deleted successfully.', extra_tags='user_management')
    
    return redirect('user_list')

@admin_required
def toggle_user_status(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)

    if user == request.user:
        messages.error(request, "You cannot change the status of your own account.", extra_tags='user_management')
        return redirect('user_list')

    user.is_active = not user.is_active
    user.save()
    status = 'activated' if user.is_active else 'deactivated'
    messages.success(request, f'User {user.username} has been {status} successfully.', extra_tags='user_management')
    return redirect('user_list')