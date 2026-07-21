from django.contrib import admin
from .models import Partner, Transaction, AuditLog, Report, UnitBuyer, UnitBuyerTransaction

@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'joined_date', 'user', 'profit_share_percentage')
    search_fields = ('name', 'email')
    list_editable = ('profit_share_percentage',)

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('date', 'transaction_type', 'partner', 'amount', 'created_by', 'timestamp')
    list_filter = ('transaction_type', 'partner', 'date')
    search_fields = ('description', 'partner__name')
    date_hierarchy = 'date'

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action', 'details')
    list_filter = ('action', 'timestamp')
    search_fields = ('details', 'user__username')

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('name', 'report_type', 'generated_at', 'generated_by')
    list_filter = ('report_type', 'generated_at')

@admin.register(UnitBuyer)
class UnitBuyerAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'total_units', 'amount_due', 'amount_paid', 'balance_remaining')
    search_fields = ('name',)

@admin.register(UnitBuyerTransaction)
class UnitBuyerTransactionAdmin(admin.ModelAdmin):
    list_display = ('buyer', 'date', 'units_added', 'amount_due', 'amount_paid', 'transaction_balance')
    list_filter = ('buyer', 'date')
    search_fields = ('buyer__name', 'notes')
    date_hierarchy = 'date'
