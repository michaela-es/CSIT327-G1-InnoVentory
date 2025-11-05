from django.db import models

class Supplier(models.Model):
    name = models.CharField(max_length=255)
    contact = models.CharField(max_length=255)
    email = models.EmailField()
    address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @property
    def products_count(self):
        return self.products.count()

    class Meta:
        ordering = ['name']