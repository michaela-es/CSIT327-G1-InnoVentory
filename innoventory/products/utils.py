# utils.py
import pandas as pd
from .models import Product


def import_products_from_excel(file):
    from suppliers.models import Supplier
    from .models import Product

    default_supplier, _ = Supplier.objects.get_or_create(
        name='Unknown Supplier',
        defaults={
            'contact': 'Not provided',
            'address': 'Not provided'
        }
    )

    df = pd.read_excel(file)
    required_columns = ['name', 'price', 'stock_quantity']
    if not all(col in df.columns for col in required_columns):
        raise ValueError(f"Excel file must contain columns: {', '.join(required_columns)}")

    existing_products = Product.objects.all()
    existing_names_lower = {product.name.lower(): product for product in existing_products}

    products_to_create = []
    products_to_update = []

    for _, row in df.iterrows():
        name = str(row['name']).strip()
        name_lower = name.lower()
        price = float(row['price'])
        stock_quantity = int(row['stock_quantity'])

        if name_lower in existing_names_lower:
            existing_product = existing_names_lower[name_lower]
            existing_product.stock_quantity += stock_quantity
            existing_product.price = price

            products_to_update.append(existing_product)
        else:
            product = Product(
                name=name,
                category=None,
                price=price,
                stock_quantity=stock_quantity,
                supplier=default_supplier
            )
            products_to_create.append(product)
            existing_names_lower[name_lower] = product

    if products_to_create:
        Product.objects.bulk_create(products_to_create)

    if products_to_update:
        Product.objects.bulk_update(
            products_to_update,
            ['stock_quantity', 'price']
        )

    return {
        'created': len(products_to_create),
        'updated': len(products_to_update),
        'total': len(products_to_create) + len(products_to_update)
    }