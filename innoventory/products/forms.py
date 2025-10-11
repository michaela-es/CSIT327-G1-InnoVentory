from django import forms
from django.core.validators import MinValueValidator
from .models import Product


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'category', 'description', 'price', 'stock_quantity', 'supplier']

    widgets = {
        'description': forms.Textarea(attrs={
            'rows': 2,
            'class': 'form-control',
            'placeholder': 'Enter a brief description...'
        }),
    }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

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

class ExcelUploadForm(forms.Form):
    excel_file = forms.FileField(
        label="Select Excel (.xlsx) file",
        required=True,
        widget=forms.ClearableFileInput(attrs={"accept": ".xlsx"})
    )