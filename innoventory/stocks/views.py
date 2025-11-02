from django.shortcuts import render
from .models import Stocks

def stock_management(request):
    stocks = Stocks.objects.filter(product__isnull=False).order_by('-date')[:5]
    return render(request, 'stocks/stock_management.html', {'stocks': stocks})
