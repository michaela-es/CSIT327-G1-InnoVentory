from django.shortcuts import render
from .models import Stocks
def stock_management(request):
    stocks = Stocks.objects.order_by('-date')[:5]
    return render(request, 'stocks/stock_management.html', {'stocks': stocks})
