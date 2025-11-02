from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from products.models import Product


class Creditor(models.Model):
    creditor_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    contact_info = models.TextField(blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    @property
    def total_balance(self):
        return sum(credit.remaining_balance for credit in self.credits.filter(is_settled=False))

    @property
    def active_credits(self):
        return self.credits.filter(is_settled=False)


class Credit(models.Model):
    CREDIT_STATUS_CHOICES = [
        ('unpaid', 'Unpaid'),
        ('partial', 'Partially Paid'),
        ('paid', 'Fully Paid'),
    ]

    credit_id = models.AutoField(primary_key=True)
    creditor = models.ForeignKey(
        Creditor,
        on_delete=models.CASCADE,
        related_name='credits'
    )

    original_sale = models.OneToOneField(
        'sales.Sale',
        on_delete=models.CASCADE,
        related_name='credit_record'
    )

    original_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    amount_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )

    credit_status = models.CharField(
        max_length=10,
        choices=CREDIT_STATUS_CHOICES,
        default='unpaid'
    )
    due_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_settled = models.BooleanField(default=False)
    settled_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Credit {self.credit_id} - {self.creditor.name} - ${self.original_amount}"

    @property
    def remaining_balance(self):
        return self.original_amount - self.amount_paid

    @property
    def is_overdue(self):
        from django.utils import timezone
        return not self.is_settled and self.due_date < timezone.now().date()

    def make_payment(self, amount):
        # Convert to Decimal if it's a float
        if isinstance(amount, float):
            amount = Decimal(str(amount))

        if amount <= 0:
            raise ValueError("Payment amount must be positive")

        if amount > self.remaining_balance:
            raise ValueError("Payment amount exceeds remaining balance")

        self.amount_paid += amount

        if self.remaining_balance <= 0:
            self.amount_paid = self.original_amount
            self.credit_status = 'paid'
            self.is_settled = True
            self.settled_date = timezone.now().date()
            self.original_sale.sales_type = 'CASH'
            self.original_sale.save()
        elif self.amount_paid > 0:
            self.credit_status = 'partial'

        self.save()

    def mark_as_paid(self):
        if not self.is_settled:
            self.amount_paid = self.original_amount
            self.credit_status = 'paid'
            self.is_settled = True
            self.settled_date = timezone.now().date()

            self.original_sale.sales_type = 'CASH'
            self.original_sale.save()

            self.save()
            return True
        return False
