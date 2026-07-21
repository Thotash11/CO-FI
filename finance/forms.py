from django import forms
from .models import Transaction, Partner, UnitBuyer, UnitBuyerTransaction

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['date', 'transaction_type', 'partner', 'amount', 'description']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'transaction_type': forms.Select(attrs={'class': 'form-select'}),
            'partner': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Enter amount (₹)'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional notes...'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        tx_type = cleaned_data.get('transaction_type')
        partner = cleaned_data.get('partner')
        amount = cleaned_data.get('amount')

        if amount is not None and amount <= 0:
            self.add_error('amount', 'Amount must be greater than zero.')

        if tx_type in ['Investment', 'Withdrawal'] and not partner:
            self.add_error('partner', f'Partner is required for "{tx_type}" transactions.')

        return cleaned_data

class PartnerForm(forms.ModelForm):
    class Meta:
        model = Partner
        fields = ['name', 'email', 'phone']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Partner Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
        }

class UnitBuyerForm(forms.ModelForm):
    class Meta:
        model = UnitBuyer
        fields = ['name']
        widgets = {
            'name': forms.Select(attrs={'class': 'form-select'}),
        }

class UnitBuyerTransactionForm(forms.ModelForm):
    class Meta:
        model = UnitBuyerTransaction
        fields = ['buyer', 'date', 'units_added', 'amount_due', 'amount_paid', 'notes']
        widgets = {
            'buyer': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'units_added': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'amount_due': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Total amount expected'}),
            'amount_paid': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Amount already paid'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Any additional details...'}),
        }
