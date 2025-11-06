from django import forms
from .models import Creditor

class LinkSaleForm(forms.Form):
    creditor = forms.ModelChoiceField(
        queryset=Creditor.objects.none(),
        empty_label="Select a creditor...",
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'style': 'color: inherit;'
        })
    )
    due_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'style': 'color: inherit;'
        }),
        required=True,
        label="Due Date"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['creditor'].queryset = Creditor.objects.all().order_by('name')
