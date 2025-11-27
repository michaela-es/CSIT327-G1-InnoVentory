from django import forms
from .models import Sale
from products.models import Product


class CreateSaleForm(forms.Form):
    product = forms.ModelChoiceField(queryset=Product.objects.all(), label="Product")
    quantity = forms.IntegerField(min_value=1, label="Quantity")
    sales_type = forms.ChoiceField(choices=Sale.SALES_TYPE_CHOICES, label="Sales Type")
    price = forms.FloatField(label="Price", required=False, disabled=True)
    total = forms.FloatField(label="Total", required=False, disabled=True)

    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        product = self.cleaned_data.get('product')

        if product and quantity > product.stock_quantity:
            raise forms.ValidationError(f"Only {product.stock_quantity} items available in stock")
        return quantity

    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get("product")
        qty = cleaned_data.get("quantity")
        if product and qty:
            cleaned_data['price'] = product.price
            cleaned_data['total'] = product.price * qty
        return cleaned_data


class SaleForm(forms.ModelForm):
    product = forms.ModelChoiceField(queryset=Product.objects.all(), label="Product", required=False)
    quantity = forms.IntegerField(min_value=1, label="Quantity", required=False)
    sales_type = forms.ChoiceField(choices=Sale.SALES_TYPE_CHOICES, label="Sales Type", required=False)
    price = forms.FloatField(label="Price", required=False, disabled=True)
    total = forms.FloatField(label="Total", required=False, disabled=True)

    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        product = self.cleaned_data.get('product')

        if product and quantity > product.stock_quantity:
            raise forms.ValidationError(f"Only {product.stock_quantity} item(s) available in stock")
        return quantity

    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get("product")
        qty = cleaned_data.get("quantity")
        if product and qty:
            cleaned_data['price'] = product.price
            cleaned_data['total'] = product.price * qty
        return cleaned_data