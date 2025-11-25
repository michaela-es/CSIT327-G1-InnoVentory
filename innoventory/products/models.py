from django.db import models
from django.core.validators import MinValueValidator, MinLengthValidator, MaxValueValidator
from django.utils import timezone
from django.db.models import Case, When, Value, F, ExpressionWrapper, FloatField, IntegerField
    
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name
class ProductQuerySet(models.QuerySet):
    def low_stock(self):
        settings = InventorySettings.objects.first()
        global_low_pct = settings.low_percentage if settings else 10

        return self.annotate(
            low_pct_calc=Case(
                When(low_threshold__isnull=False, then=F('low_threshold')),
                default=Value(global_low_pct),
                output_field=FloatField()
            ),
            base_stock=Case(
                When(max_stock_recorded__gt=0, then=F('max_stock_recorded')),
                default=F('stock_quantity'),
                output_field=IntegerField()
            ),
            low_threshold_calc=ExpressionWrapper(
                F('low_pct_calc') / 100.0 * F('base_stock'),
                output_field=FloatField()
            )
        ).filter(stock_quantity__lte=F('low_threshold_calc'))

class ProductManager(models.Manager):
    def get_queryset(self):
        return ProductQuerySet(self.model, using=self._db)

    def low_stock(self):
        return self.get_queryset().low_stock()

class InventorySettings(models.Model):
    low_percentage = models.PositiveIntegerField(default=20)
    medium_percentage = models.PositiveIntegerField(default=50)

    def __str__(self):
        return "Inventory Threshold Settings"

    class Meta:
        verbose_name = "Inventory Setting"
        verbose_name_plural = "Inventory Settings"

class Product(models.Model):
    product_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    price = models.FloatField()
    stock_quantity = models.IntegerField()
    date_modified = models.DateTimeField(auto_now=True)
    supplier = models.ForeignKey('suppliers.Supplier', on_delete=models.CASCADE, related_name='products')

    is_tracked = models.BooleanField(default=False)
    max_stock_recorded = models.PositiveIntegerField(default=0)
    low_threshold = models.PositiveIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(100)]
    )
    medium_threshold = models.PositiveIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(100)]
    )

    objects = ProductManager()

    def save(self, *args, **kwargs):
        if self.stock_quantity > self.max_stock_recorded:
            self.max_stock_recorded = self.stock_quantity
        super().save(*args, **kwargs)

    def stock_status(self):
        if self.is_tracked and self.low_threshold and self.medium_threshold:
            if self.stock_quantity > self.medium_threshold:
                return "high"
            elif self.stock_quantity > self.low_threshold:
                return "medium"
            else:
                return "low"

        settings = InventorySettings.objects.first()
        if not settings:
            return "unknown"

        low = (settings.low_percentage / 100) * self.max_stock_recorded
        medium = (settings.medium_percentage / 100) * self.max_stock_recorded

        if self.stock_quantity > medium:
            return "high"
        elif self.stock_quantity > low:
            return "medium"
        else:
            return "low"

    def get_thresholds(self):
        settings = InventorySettings.objects.first()
        if not settings:
            low_pct, med_pct = 10, 50
        else:
            low_pct = self.low_threshold if self.low_threshold is not None else settings.low_percentage
            med_pct = self.medium_threshold if self.medium_threshold is not None else settings.medium_percentage

        base = self.max_stock_recorded if self.max_stock_recorded > 0 else max(self.stock_quantity, 1)

        low = max(1, int((low_pct / 100) * base))
        medium = max(low + 1, int((med_pct / 100) * base))

        return low, medium

    @property
    def display_color(self):
        low, medium = self.get_thresholds()
        if self.stock_quantity <= low:
            return "danger"  # red
        elif self.stock_quantity <= medium:
            return "warning" # orange
        else:
            return "info"

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
    updated_at = models.DateTimeField(auto_now=True)
    
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

