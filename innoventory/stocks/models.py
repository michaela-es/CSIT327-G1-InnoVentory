from django.db import models, transaction

class Stocks(models.Model):
    IN = 'in'
    OUT = 'out'

    STOCK_TYPE_CHOICES = [
        (IN, 'Stock In'),
        (OUT, 'Stock Out'),
    ]

    stock_id = models.AutoField(primary_key=True)
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='stocks')
    qty = models.IntegerField()
    type = models.CharField(max_length=3, choices=STOCK_TYPE_CHOICES)
    date = models.DateTimeField(auto_now=True)
    remarks = models.CharField(max_length=100, blank=True)

    def _adjust_product_stock(self, qty_change):
        self.product.stock_quantity = models.F('stock_quantity') + qty_change
        self.product.save(update_fields=['stock_quantity'])
        self.product.refresh_from_db(fields=['stock_quantity'])

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if self.pk:
                old = Stocks.objects.get(pk=self.pk)
                if old.type == self.IN:
                    self._adjust_product_stock(-old.qty)
                else:
                    self._adjust_product_stock(old.qty)

                super().save(*args, **kwargs)

                if self.type == self.IN:
                    self._adjust_product_stock(self.qty)
                else:
                    self._adjust_product_stock(-self.qty)

            else:
                super().save(*args, **kwargs)
                if self.type == self.IN:
                    self._adjust_product_stock(self.qty)
                else:
                    self._adjust_product_stock(-self.qty)

    def delete(self, *args, **kwargs):
        with transaction.atomic():
            if self.type == self.IN:
                self._adjust_product_stock(-self.qty)
            else:
                self._adjust_product_stock(self.qty)
            super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} ({self.type}) - {self.qty}"
