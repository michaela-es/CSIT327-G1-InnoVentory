from .models import Supplier
import pandas as pd

def import_suppliers_from_excel(excel_file):
    try:
        if excel_file.name.endswith('.xlsx'):
            df = pd.read_excel(excel_file, engine='openpyxl')
        else:
            df = pd.read_excel(excel_file)
        
        created = 0
        updated = 0
        total = 0
        
        for index, row in df.iterrows():
            total += 1
            try:
                supplier, created_flag = Supplier.objects.get_or_create(
                    name=row['name'],
                    defaults={
                        'contact': row.get('contact', ''),
                        'email': row.get('email', ''),
                        'address': row.get('address', ''),
                        'notes': row.get('notes', ''),
                    }
                )
                
                if created_flag:
                    created += 1
                else:
                    supplier.contact = row.get('contact', supplier.contact)
                    supplier.email = row.get('email', supplier.email)
                    supplier.address = row.get('address', supplier.address)
                    supplier.notes = row.get('notes', supplier.notes)
                    supplier.save()
                    updated += 1
                    
            except Exception as e:
                raise Exception(f"Row {index + 2}: {str(e)}")
        
        return {
            'created': created,
            'updated': updated,
            'total': total
        }
        
    except Exception as e:
        raise Exception(f"Error processing Excel file: {str(e)}")