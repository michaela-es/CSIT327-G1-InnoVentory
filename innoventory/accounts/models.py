from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        STAFF = 'staff', 'Staff'

    role = models.CharField(max_length=10, choices=Role.choices, default=Role.STAFF)
    phone_number = models.CharField(max_length=15, unique=True)
    email = models.EmailField(unique=True)

    def can_be_deleted(self):
        from sales.models import Sale
        return not Sale.objects.filter(sold_by=self).exists()
    
    def get_sales_count(self):
        from sales.models import Sale
        return Sale.objects.filter(sold_by=self).count()

    def __str__(self):
        return self.username
