from django import forms
from django.core.validators import MinValueValidator
from .models import Product, Category


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

class ExcelUploadForm(forms.Form):
    excel_file = forms.FileField(
        label="Select Excel (.xlsx) file",
        required=True,
        widget=forms.ClearableFileInput(attrs={"accept": ".xlsx"})
    )