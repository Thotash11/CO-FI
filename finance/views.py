from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncMonth, TruncDate, TruncYear
from django.http import HttpResponse
from django.utils import timezone
import csv
from decimal import Decimal
from datetime import datetime, timedelta
import threading
from django.core.mail import send_mail
from django.conf import settings

from .models import Partner, Transaction, AuditLog, Report, UnitBuyer, UnitBuyerTransaction
from .forms import TransactionForm, PartnerForm, UnitBuyerForm, UnitBuyerTransactionForm

def send_transaction_email(action, tx, user):
    def send():
        subject = f"Co-Fi Update: Transaction {action}"
        partner_name = tx.partner.name if tx.partner else 'General Business'
        user_name = user.username if user and user.is_authenticated else 'System'
        message = (
            f"A transaction has been {action.lower()} by {user_name}.\n\n"
            f"Details:\n"
            f"- Date: {tx.date}\n"
            f"- Type: {tx.transaction_type}\n"
            f"- Partner: {partner_name}\n"
            f"- Amount: ₹{tx.amount}\n"
            f"- Notes: {tx.description}\n\n"
            f"Please check your Co-Fi dashboard for full details."
        )
        recipient_list = [p.email for p in Partner.objects.filter(user=request.user) if p.email]
        # Always send to the requested admin email
        import os
        admin_email = os.getenv('ADMIN_EMAIL', 'ashishpatel11aca@gmail.com')
        if admin_email not in recipient_list:
            recipient_list.append(admin_email)
            
        if recipient_list:
            try:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@cofi.local',
                    recipient_list=recipient_list,
                    fail_silently=True,
                )
            except Exception as e:
                print(f"Error sending email: {e}")
                
    threading.Thread(target=send).start()

def get_financial_summary(transactions=None):
    if transactions is None:
        transactions = Transaction.objects.filter(created_by=request.user)
    
    total_investment = transactions.filter(transaction_type='Investment').aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
    total_revenue = transactions.filter(transaction_type='Income').aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
    total_expenses = transactions.filter(transaction_type='Expense').aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
    total_withdrawals = transactions.filter(transaction_type='Withdrawal').aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
    
    net_profit = total_revenue - total_expenses
    cash_balance = total_investment + total_revenue - total_expenses - total_withdrawals
    
    return {
        'total_investment': total_investment,
        'total_revenue': total_revenue,
        'total_expenses': total_expenses,
        'total_withdrawals': total_withdrawals,
        'net_profit': net_profit,
        'cash_balance': cash_balance,
    }

def get_partners_summary(all_transactions=None):
    if all_transactions is None:
        all_transactions = Transaction.objects.filter(created_by=request.user)
    
    partners = Partner.objects.filter(user=request.user)
    summary = get_financial_summary(all_transactions)
    net_profit = summary['net_profit']
    
    total_invested_all = all_transactions.filter(transaction_type='Investment').aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
    
    partner_data = []
    for partner in partners:
        p_invested = all_transactions.filter(partner=partner, transaction_type='Investment').aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
        p_withdrawn = all_transactions.filter(partner=partner, transaction_type='Withdrawal').aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
        p_expenses = all_transactions.filter(partner=partner, transaction_type='Expense').aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
        
        share_pct = partner.profit_share_percentage
            
        profit_share = (share_pct / Decimal('100.00')) * net_profit
        capital_contribution = p_invested + p_expenses - p_withdrawn
        net_balance = capital_contribution + profit_share
        
        partner_data.append({
            'partner': partner,
            'total_invested': p_invested,
            'total_withdrawn': p_withdrawn,
            'total_expenses': p_expenses,
            'capital_contribution': capital_contribution,
            'share_pct': share_pct.quantize(Decimal('0.01')),
            'profit_share': profit_share.quantize(Decimal('0.01')),
            'net_balance': net_balance.quantize(Decimal('0.01')),
        })
        
    return partner_data

# Dashboard View
@login_required
def dashboard_view(request):
    transactions = Transaction.objects.filter(created_by=request.user).order_by('-date', '-timestamp')
    summary = get_financial_summary(transactions)
    partners = get_partners_summary(transactions)
    
    # Chart Data (monthly trends)
    monthly_data = Transaction.objects.filter(created_by=request.user).annotate(
        month=TruncMonth('date')
    ).values('month', 'transaction_type').annotate(
        total_amount=Sum('amount')
    ).order_by('month')
    
    chart_months = []
    chart_revenue = []
    chart_expenses = []
    chart_profit = []
    
    # Build chart datasets
    month_map = {}
    for entry in monthly_data:
        m_str = entry['month'].strftime('%b %Y') if entry['month'] else 'Unknown'
        if m_str not in month_map:
            month_map[m_str] = {'revenue': 0, 'expense': 0}
        if entry['transaction_type'] == 'Income':
            month_map[m_str]['revenue'] = float(entry['total_amount'])
        elif entry['transaction_type'] == 'Expense':
            month_map[m_str]['expense'] = float(entry['total_amount'])
            
    for m, vals in month_map.items():
        chart_months.append(m)
        chart_revenue.append(vals['revenue'])
        chart_expenses.append(vals['expense'])
        chart_profit.append(vals['revenue'] - vals['expense'])
        
    # Get recent audit logs
    audit_logs = AuditLog.objects.filter(user=request.user).order_by('-timestamp')[:5]
    
    context = {
        'summary': summary,
        'partners': partners,
        'recent_transactions': transactions[:5],
        'audit_logs': audit_logs,
        'chart_months': chart_months,
        'chart_revenue': chart_revenue,
        'chart_expenses': chart_expenses,
        'chart_profit': chart_profit,
    }
    return render(request, 'finance/dashboard.html', context)

# Transaction Views
@login_required
def transaction_list(request):
    transactions = Transaction.objects.filter(created_by=request.user).order_by('-date', '-timestamp')
    
    # Filtering
    search_query = request.GET.get('search', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    tx_type = request.GET.get('type', '')
    partner_id = request.GET.get('partner', '')
    
    if search_query:
        transactions = transactions.filter(
            Q(description__icontains=search_query) | Q(partner__name__icontains=search_query)
        )
    if start_date:
        transactions = transactions.filter(date__gte=start_date)
    if end_date:
        transactions = transactions.filter(date__lte=end_date)
    if tx_type:
        transactions = transactions.filter(transaction_type=tx_type)
    if partner_id:
        transactions = transactions.filter(partner_id=partner_id)
        
    partners = Partner.objects.filter(user=request.user)
    
    from django.db.models import Q
    context = {
        'transactions': transactions,
        'partners': partners,
        'search_query': search_query,
        'start_date': start_date,
        'end_date': end_date,
        'tx_type': tx_type,
        'partner_id': partner_id,
    }
    return render(request, 'finance/transaction_list.html', context)

@login_required
def transaction_create(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        form.fields['partner'].queryset = Partner.objects.filter(user=request.user)
        if form.is_valid():
            tx = form.save(commit=False)
            tx.created_by = request.user if request.user.is_authenticated else None
            tx.save()
            
            # Log action
            AuditLog.objects.create(
                user=request.user if request.user.is_authenticated else None,
                action='CREATE',
                details=f"Created Transaction: {tx}"
            )
            send_transaction_email('CREATED', tx, request.user)
            messages.success(request, "Transaction added successfully.")
            return redirect('transactions')
    else:
        form = TransactionForm()
        form.fields['partner'].queryset = Partner.objects.filter(user=request.user)
    return render(request, 'finance/transaction_form.html', {'form': form, 'title': 'Add Transaction'})

@login_required
def transaction_update(request, pk):
    tx = get_object_or_404(Transaction, pk=pk, created_by=request.user)
    old_val = str(tx)
    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=tx)
        form.fields['partner'].queryset = Partner.objects.filter(user=request.user)
        if form.is_valid():
            form.save()
            # Log action
            AuditLog.objects.create(
                user=request.user if request.user.is_authenticated else None,
                action='UPDATE',
                details=f"Updated Transaction from '{old_val}' to '{tx}'"
            )
            send_transaction_email('UPDATED', tx, request.user)
            messages.success(request, "Transaction updated successfully.")
            return redirect('transactions')
    else:
        form = TransactionForm(instance=tx)
        form.fields['partner'].queryset = Partner.objects.filter(user=request.user)
    return render(request, 'finance/transaction_form.html', {'form': form, 'title': 'Edit Transaction'})

@login_required
def transaction_delete(request, pk):
    tx = get_object_or_404(Transaction, pk=pk, created_by=request.user)
    if request.method == 'POST':
        details = f"Deleted Transaction: {tx}"
        tx.delete()
        # Log action
        AuditLog.objects.create(
            user=request.user if request.user.is_authenticated else None,
            action='DELETE',
            details=details
        )
        send_transaction_email('DELETED', tx, request.user)
        messages.success(request, "Transaction deleted successfully.")
    return redirect('transactions')

# Reports Page
@login_required
def reports_view(request):
    # Daily, Monthly, Yearly summaries
    daily_summaries = Transaction.objects.filter(created_by=request.user).values('date').annotate(
        income=Sum('amount', filter=Q(transaction_type='Income')),
        expense=Sum('amount', filter=Q(transaction_type='Expense')),
        count=Count('id')
    ).order_by('-date')[:30]
    
    monthly_summaries = Transaction.objects.filter(created_by=request.user).annotate(
        month=TruncMonth('date')
    ).values('month').annotate(
        income=Sum('amount', filter=Q(transaction_type='Income')),
        expense=Sum('amount', filter=Q(transaction_type='Expense')),
        count=Count('id')
    ).order_by('-month')
    
    yearly_summaries = Transaction.objects.filter(created_by=request.user).annotate(
        year=TruncYear('date')
    ).values('year').annotate(
        income=Sum('amount', filter=Q(transaction_type='Income')),
        expense=Sum('amount', filter=Q(transaction_type='Expense')),
        count=Count('id')
    ).order_by('-year')
    
    summary = get_financial_summary(Transaction.objects.filter(created_by=request.user))
    partners = get_partners_summary(Transaction.objects.filter(created_by=request.user))
    
    context = {
        'daily_summaries': daily_summaries,
        'monthly_summaries': monthly_summaries,
        'yearly_summaries': yearly_summaries,
        'summary': summary,
        'partners': partners,
    }
    return render(request, 'finance/reports.html', context)

# CSV Export Views
@login_required
def export_transactions_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="transactions_{timezone.now().strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Date', 'Type', 'Partner', 'Amount (₹)', 'Description', 'Created By', 'Timestamp'])
    
    for tx in Transaction.objects.filter(created_by=request.user).order_by('-date'):
        partner_name = tx.partner.name if tx.partner else 'General Business'
        created_by = tx.created_by.username if tx.created_by else 'System'
        writer.writerow([tx.date, tx.transaction_type, partner_name, tx.amount, tx.description, created_by, tx.timestamp])
        
    return response
# Unit Buyer Views
@login_required
def unit_buyer_list(request):
    buyers = UnitBuyer.objects.filter(user=request.user).order_by('name')
    return render(request, 'finance/unit_buyers_list.html', {'buyers': buyers})

@login_required
def unit_buyer_create(request):
    if request.method == 'POST':
        form = UnitBuyerForm(request.POST)
        if form.is_valid():
            buyer = form.save(commit=False)
            buyer.user = request.user
            buyer.save()
            messages.success(request, f"Successfully added {buyer.name}.")
            return redirect('unit_buyers')
    else:
        form = UnitBuyerForm()
    return render(request, 'finance/unit_buyer_form.html', {'form': form, 'title': 'Add Unit Buyer'})

@login_required
def unit_buyer_update(request, pk):
    buyer = get_object_or_404(UnitBuyer, pk=pk, user=request.user)
    if request.method == 'POST':
        form = UnitBuyerForm(request.POST, instance=buyer)
        if form.is_valid():
            form.save()
            messages.success(request, f"Successfully updated {buyer.name}.")
            return redirect('unit_buyers')
    else:
        form = UnitBuyerForm(instance=buyer)
    return render(request, 'finance/unit_buyer_form.html', {'form': form, 'title': 'Edit Unit Buyer'})

@login_required
def unit_buyer_delete(request, pk):
    buyer = get_object_or_404(UnitBuyer, pk=pk, user=request.user)
    if request.method == 'POST':
        name = buyer.name
        buyer.delete()
        messages.success(request, f"Successfully deleted {name}.")
    return redirect('unit_buyers')

@login_required
def unit_buyer_detail(request, pk):
    buyer = get_object_or_404(UnitBuyer, pk=pk, user=request.user)
    transactions = buyer.transactions.all().order_by('-date', '-created_at')
    return render(request, 'finance/unit_buyer_detail.html', {'buyer': buyer, 'transactions': transactions})

@login_required
def unit_buyer_add_transaction(request, pk):
    buyer = get_object_or_404(UnitBuyer, pk=pk, user=request.user)
    if request.method == 'POST':
        form = UnitBuyerTransactionForm(request.POST)
        form.fields['buyer'].queryset = UnitBuyer.objects.filter(user=request.user)
        if form.is_valid():
            tx = form.save(commit=False)
            tx.buyer = buyer
            tx.save()
            messages.success(request, f"Transaction added for {buyer.name}.")
            return redirect('unit_buyer_detail', pk=buyer.pk)
    else:
        form = UnitBuyerTransactionForm(initial={'buyer': buyer})
        form.fields['buyer'].queryset = UnitBuyer.objects.filter(user=request.user)
    return render(request, 'finance/unit_buyer_transaction_form.html', {'form': form, 'buyer': buyer, 'title': f'Add Transaction for {buyer.name}'})

@login_required
def unit_buyer_transaction_update(request, pk):
    tx = get_object_or_404(UnitBuyerTransaction, pk=pk, buyer__user=request.user)
    buyer = tx.buyer
    if request.method == 'POST':
        form = UnitBuyerTransactionForm(request.POST, instance=tx)
        form.fields['buyer'].queryset = UnitBuyer.objects.filter(user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f"Transaction updated for {buyer.name}.")
            return redirect('unit_buyer_detail', pk=buyer.pk)
    else:
        form = UnitBuyerTransactionForm(instance=tx)
        form.fields['buyer'].queryset = UnitBuyer.objects.filter(user=request.user)
    return render(request, 'finance/unit_buyer_transaction_form.html', {'form': form, 'buyer': buyer, 'title': f'Edit Transaction for {buyer.name}'})

@login_required
def unit_buyer_transaction_delete(request, pk):
    tx = get_object_or_404(UnitBuyerTransaction, pk=pk, buyer__user=request.user)
    buyer = tx.buyer
    if request.method == 'POST':
        tx.delete()
        messages.success(request, f"Transaction deleted for {buyer.name}.")
    return redirect('unit_buyer_detail', pk=buyer.pk)
@login_required
def export_reports_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="financial_summary_{timezone.now().strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    
    # Financial Overview
    summary = get_financial_summary(Transaction.objects.filter(created_by=request.user))
    writer.writerow(['FINANCIAL OVERVIEW'])
    writer.writerow(['Metric', 'Amount (₹)'])
    writer.writerow(['Total Investment', summary['total_investment']])
    writer.writerow(['Total Revenue', summary['total_revenue']])
    writer.writerow(['Total Expenses', summary['total_expenses']])
    writer.writerow(['Net Profit/Loss', summary['net_profit']])
    writer.writerow(['Cash Balance', summary['cash_balance']])
    writer.writerow(['Total Withdrawals', summary['total_withdrawals']])
    writer.writerow([])
    
    # Partner Summary
    writer.writerow(['PARTNER CAPITAL ACCOUNTS'])
    writer.writerow(['Partner Name', 'Total Invested', 'Total Withdrawn', 'Capital Contribution', 'Profit Share %', 'Profit Share Share', 'Net Balance'])
    for p in get_partners_summary(Transaction.objects.filter(created_by=request.user)):
        writer.writerow([
            p['partner'].name,
            p['total_invested'],
            p['total_withdrawn'],
            p['capital_contribution'],
            f"{p['share_pct']}%",
            p['profit_share'],
            p['net_balance']
        ])
        
    return response
