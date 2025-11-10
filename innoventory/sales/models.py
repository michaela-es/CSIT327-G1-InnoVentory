from django.db import models
from django.conf import settings
from products.models import Product
from django.utils import timezone

class Sale(models.Model):
    SALES_TYPE_CHOICES = [
        ('cash', 'CASH'),
        ('credit', 'CREDIT'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('partial', 'Partial'),
    ]

    sale_id = models.AutoField(primary_key=True)
    product_sold = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='sales')
    product_qty = models.PositiveIntegerField(default=0)
    total = models.FloatField()
    sales_type = models.CharField(max_length=20, choices=SALES_TYPE_CHOICES)
    sales_date = models.DateTimeField(auto_now_add=True)
    sold_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    # for credit tracking
    customer_name = models.CharField(max_length=200, blank=True)
    customer_contact = models.CharField(max_length=200, blank=True)
    due_date = models.DateField(null=True, blank=True)
    amount_paid = models.FloatField(default=0.00)
    balance = models.FloatField(default=0.00)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_notes = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if not self.balance:
            self.balance = self.total
        
        if self.sales_type == 'cash':
            self.payment_status = 'paid'
            self.amount_paid = self.total
            self.balance = 0
        else:  
            if self.amount_paid >= self.total:
                self.payment_status = 'paid'
                self.balance = 0
            elif self.amount_paid > 0:
                self.payment_status = 'partial'
            else:
                self.payment_status = 'pending'
            
            # Check for overdue
            if self.due_date and timezone.now().date() > self.due_date and self.balance > 0:
                self.payment_status = 'overdue'
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Sale {self.sale_id} - {self.product_sold.name} x {self.product_qty}"