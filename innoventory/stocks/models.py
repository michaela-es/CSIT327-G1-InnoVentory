from django.db import models, transaction

class Stocks(models.Model):
    IN = 'in'
    OUT = 'out'

    STOCK_TYPE_CHOICES = [
        (IN, 'Stock In'),
        (OUT, 'Stock Out'),
    ]

    stock_id = models.AutoField(primary_key=True)
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.SET_NULL,
        null=True,
        related_name='stocks'
    )
    qty = models.IntegerField()
    type = models.CharField(max_length=3, choices=STOCK_TYPE_CHOICES)
    date = models.DateTimeField(auto_now=True)
    remarks = models.CharField(max_length=100, blank=True)

    def _adjust_product_stock(self, qty_change):
        if self.product is not None:
            self.product.stock_quantity = models.F('stock_quantity') + qty_change
            self.product.save(update_fields=['stock_quantity'])
            self.product.refresh_from_db(fields=['stock_quantity'])

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if self.pk:
                old_stock = Stocks.objects.get(pk=self.pk)

                if old_stock.type == self.IN:
                    adjustment = -old_stock.qty
                else:
                    adjustment = old_stock.qty

                self._adjust_product_stock(adjustment)

            super().save(*args, **kwargs)

            if self.type == self.IN:
                adjustment = self.qty
            else:
                adjustment = -self.qty

            self._adjust_product_stock(adjustment)

    def delete(self, *args, **kwargs):
        with transaction.atomic():
            if self.product is not None:
                if self.type == self.IN:
                    self._adjust_product_stock(-self.qty)
                else:
                    self._adjust_product_stock(self.qty)
            super().delete(*args, **kwargs)

    def __str__(self):
        product_name = self.product.name if self.product else "Deleted Product"
        return f"{product_name} ({self.type}) - {self.qty}"