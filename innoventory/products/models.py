from django.db import models

class Supplier(models.Model):
    supplier_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    contact_info = models.CharField(max_length=255)
    address = models.TextField()

    def __str__(self):
        return self.name

class Product(models.Model):
    product_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=100)
    description = models.TextField()
    price = models.FloatField()
    stock_quantity = models.IntegerField()
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.name
