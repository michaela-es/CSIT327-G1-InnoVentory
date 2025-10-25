from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone

class Supplier(models.Model):
    supplier_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    contact_info = models.CharField(max_length=255)
    address = models.TextField()

    def __str__(self):
        return self.name
    
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Product(models.Model):
    product_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    price = models.FloatField()
    stock_quantity = models.IntegerField()
    date_modified = models.DateTimeField(auto_now=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.name


class StockTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('IN', 'Stock In'),
        ('OUT', 'Stock Out'),
    ]
    
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=3, choices=TRANSACTION_TYPES)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    remarks = models.TextField(blank=True)
    date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date', '-created_at']
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.product.name} - {self.quantity}"
    
    def save(self, *args, **kwargs):
        is_new = not self.pk
        
        if is_new:
            if self.transaction_type == 'IN':
                self.product.stock_quantity += self.quantity
            else:  
                if self.product.stock_quantity < self.quantity:
                    raise ValueError(f"Insufficient stock for {self.product.name}. Available: {self.product.stock_quantity}, Requested: {self.quantity}")
                self.product.stock_quantity -= self.quantity
            self.product.save()
        
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        if self.transaction_type == 'IN':
            self.product.stock_quantity -= self.quantity
        else:  
            self.product.stock_quantity += self.quantity
        self.product.save()
        super().delete(*args, **kwargs)