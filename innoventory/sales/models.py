from django.db import models
from django.conf import settings
from products.models import Product

class Sale(models.Model):
    SALES_TYPE_CHOICES = [
        ('cash', 'CASH'),
        ('credit', 'CREDIT'),
    ]

    sale_id = models.AutoField(primary_key=True)
    product_sold = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        related_name='sales'
    )
    product_qty = models.PositiveIntegerField(default=0)
    total = models.FloatField()
    sales_type = models.CharField(max_length=20, choices=SALES_TYPE_CHOICES)
    sales_date = models.DateTimeField(auto_now_add=True)
    sold_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Sale {self.sale_id} - {self.product_sold.name} x {self.product_qty}"