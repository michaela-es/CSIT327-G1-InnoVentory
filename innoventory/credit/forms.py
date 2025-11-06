from django import forms
from .models import Creditor, Credit


class CreditModelForm(forms.ModelForm):
    due_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
        }),
        required=True,
        label="Due Date"
    )

    class Meta:
        model = Credit
        fields = ['creditor', 'due_date']
        widgets = {
            'creditor': forms.Select(attrs={
                'class': 'form-select',
                'style': 'color: inherit;'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['creditor'].queryset = Creditor.objects.only('creditor_id', 'name').order_by('name')
        self.fields['creditor'].empty_label = "Select a creditor..."