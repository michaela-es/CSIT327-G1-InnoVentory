from django import forms
from .models import Product, Category, StockTransaction, Supplier

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name',
            'category',
            'price',
            'stock_quantity',
            'supplier',
            'is_tracked',
            'low_threshold',
            'medium_threshold',
        ]
        widgets = {
            'category': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_category'
            }),
            'is_tracked': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'id_is_tracked'
            }),
            'low_threshold': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 100,
                'id': 'id_low_threshold'
            }),
            'medium_threshold': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 100,
                'id': 'id_medium_threshold'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            if name != 'is_tracked':
                field.widget.attrs.setdefault('class', 'form-control')

        category_choices = [('', '---------'), ('__new__', '➕ Add New Category')]
        category_choices.extend(
            (cat.id, cat.name) for cat in Category.objects.all().order_by('name')
        )
        self.fields['category'].choices = category_choices
        self.fields['category'].required = False

        if self.instance and not self.instance.is_tracked:
            self.fields['low_threshold'].widget.attrs['disabled'] = True
            self.fields['medium_threshold'].widget.attrs['disabled'] = True

    def clean(self):
        cleaned = super().clean()

        is_tracked = cleaned.get("is_tracked")
        low = cleaned.get("low_threshold")
        medium = cleaned.get("medium_threshold")

        if is_tracked:
            if low is None:
                self.add_error("low_threshold", "Low threshold is required when tracking is enabled.")
            if medium is None:
                self.add_error("medium_threshold", "Medium threshold is required when tracking is enabled.")
            if low is not None and medium is not None:
                if low <= 0:
                    self.add_error("low_threshold", "Low threshold must be greater than 0.")
                if medium <= low:
                    self.add_error("medium_threshold", "Medium threshold must be greater than low threshold.")
        else:
            cleaned['low_threshold'] = None
            cleaned['medium_threshold'] = None

        return cleaned

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is not None and price <= 0:
            raise forms.ValidationError("Price must be positive.")
        return price

    def clean_stock_quantity(self):
        stock_quantity = self.cleaned_data.get('stock_quantity')
        if stock_quantity is not None and stock_quantity < 0:
            raise forms.ValidationError("Stock quantity must be positive.")
        return stock_quantity

class StockTransactionForm(forms.ModelForm):
    class Meta:
        model = StockTransaction
        fields = ['product', 'transaction_type', 'quantity', 'remarks', 'date']
        widgets = {
            'transaction_type': forms.HiddenInput(),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'style': 'margin-top: 15px;',
                'placeholder': 'Enter quantity',
                'min': 1
            }),
            'remarks': forms.Textarea(attrs={
                'class': 'form-control',
                'style': 'resize: vertical;',
                'rows': 3,
                'placeholder': 'EX. Damaged item removed'
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})    
        if self.instance and self.instance.pk:
            self.fields['product'].disabled = True

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity and quantity <= 0:
            raise forms.ValidationError("Quantity must be positive.")
        return quantity
