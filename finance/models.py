from django.db import models
from django.contrib.auth.models import User

class Partner(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='partner_profile')
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    joined_date = models.DateField(auto_now_add=True)
    profit_share_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=50.00)

    def __str__(self):
        return self.name

class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('Investment', 'Investment'),
        ('Expense', 'Expense'),
        ('Income', 'Income/Sale'),
        ('Withdrawal', 'Withdrawal'),
    ]

    date = models.DateField()
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    partner = models.ForeignKey(Partner, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_transactions')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        partner_str = f" - {self.partner.name}" if self.partner else ""
        return f"{self.transaction_type}{partner_str}: ₹{self.amount} on {self.date}"

class AuditLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=50)  # CREATE, UPDATE, DELETE
    details = models.TextField()

    def __str__(self):
        user_str = self.user.username if self.user else "System"
        return f"{self.action} by {user_str} at {self.timestamp}"

class Report(models.Model):
    name = models.CharField(max_length=100)
    report_type = models.CharField(max_length=50)  # Daily, Monthly, Yearly, P&L, Partner Contribution
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    summary_data = models.JSONField(default=dict, blank=True)  # Store calculations as JSON for reference

    def __str__(self):
        return f"{self.name} ({self.report_type}) - {self.generated_at}"

class UnitBuyer(models.Model):
    BUYER_CHOICES = [
        ('Raju', 'Raju'),
        ('Ramesh', 'Ramesh'),
        ('Govindha Raju', 'Govindha Raju'),
    ]
    name = models.CharField(max_length=150, choices=BUYER_CHOICES, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    @property
    def total_units(self):
        return sum(t.units_added for t in self.transactions.all())
        
    @property
    def amount_due(self):
        return sum(t.amount_due for t in self.transactions.all())

    @property
    def amount_paid(self):
        return sum(t.amount_paid for t in self.transactions.all())

    @property
    def balance_remaining(self):
        return self.amount_due - self.amount_paid

    def __str__(self):
        return self.name

class UnitBuyerTransaction(models.Model):
    buyer = models.ForeignKey(UnitBuyer, on_delete=models.CASCADE, related_name='transactions')
    date = models.DateField()
    units_added = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Units added in this transaction")
    amount_due = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text="Amount owed for this transaction")
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text="Amount paid in this transaction")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def transaction_balance(self):
        return self.amount_due - self.amount_paid

    def __str__(self):
        return f"{self.buyer.name} - {self.date}"
