from django import forms
from .models import Product, Category, StockTransaction, Supplier


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'category', 'price', 'stock_quantity', 'supplier']
        widgets = {
            'category': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_category'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        
        category_choices = [('', '---------'), ('__new__', '➕ Add New Category')]
        category_choices.extend([(cat.id, cat.name) for cat in Category.objects.all().order_by('name')])
        self.fields['category'].choices = category_choices
        self.fields['category'].required = False

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price and price <= 0:
            raise forms.ValidationError("Price must be positive.")
        return price

    def clean_stock_quantity(self):
        stock_quantity = self.cleaned_data.get('stock_quantity')
        if stock_quantity and stock_quantity < 0:
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
