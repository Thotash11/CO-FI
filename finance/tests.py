from django.test import TestCase
from django.contrib.auth.models import User
from decimal import Decimal
import datetime

from .models import Partner, Transaction
from .views import get_financial_summary, get_partners_summary

class FinanceLogicTest(TestCase):
    def setUp(self):
        # Create users
        self.user1 = User.objects.create_user(username='partner1', password='password1')
        self.user2 = User.objects.create_user(username='partner2', password='password2')
        
        # Create partners
        self.partner1 = Partner.objects.create(user=self.user1, name="Partner One", email="p1@example.com")
        self.partner2 = Partner.objects.create(user=self.user2, name="Partner Two", email="p2@example.com")
        
    def test_profit_sharing_calculations(self):
        # 1. Partner 1 invests 100,000, Partner 2 invests 50,000
        Transaction.objects.create(
            date=datetime.date.today(),
            transaction_type='Investment',
            partner=self.partner1,
            amount=Decimal('100000.00'),
            description="P1 initial investment",
            created_by=self.user1
        )
        Transaction.objects.create(
            date=datetime.date.today(),
            transaction_type='Investment',
            partner=self.partner2,
            amount=Decimal('50000.00'),
            description="P2 initial investment",
            created_by=self.user2
        )
        
        # 2. Add income of 30,000 and expense of 10,000
        Transaction.objects.create(
            date=datetime.date.today(),
            transaction_type='Income',
            amount=Decimal('30000.00'),
            description="Sales revenue",
            created_by=self.user1
        )
        Transaction.objects.create(
            date=datetime.date.today(),
            transaction_type='Expense',
            amount=Decimal('10000.00'),
            description="Office rent",
            created_by=self.user2
        )
        
        # Calculate summary
        summary = get_financial_summary()
        self.assertEqual(summary['total_investment'], Decimal('150000.00'))
        self.assertEqual(summary['total_revenue'], Decimal('30000.00'))
        self.assertEqual(summary['total_expenses'], Decimal('10000.00'))
        self.assertEqual(summary['net_profit'], Decimal('20000.00'))
        self.assertEqual(summary['cash_balance'], Decimal('170000.00'))
        
        # Calculate partner balance details
        partners_summary = get_partners_summary()
        
        # Partner 1 share should be 50.00%
        # Partner 2 share should be 50.00%
        # Profit distribution: P1 gets 50% of 20,000 = 10000.00, P2 gets 50% = 10000.00
        
        p1_data = next(p for p in partners_summary if p['partner'] == self.partner1)
        p2_data = next(p for p in partners_summary if p['partner'] == self.partner2)
        
        self.assertAlmostEqual(p1_data['share_pct'], Decimal('50.00'), places=2)
        self.assertAlmostEqual(p2_data['share_pct'], Decimal('50.00'), places=2)
        
        self.assertAlmostEqual(p1_data['profit_share'], Decimal('10000.00'), places=2)
        self.assertAlmostEqual(p2_data['profit_share'], Decimal('10000.00'), places=2)
        
        # Balance = Investment + Profit - Withdrawals
        # P1 = 100000 + 10000.00 - 0 = 110000.00
        # P2 = 50000 + 10000.00 - 0 = 60000.00
        self.assertAlmostEqual(p1_data['net_balance'], Decimal('110000.00'), places=2)
        self.assertAlmostEqual(p2_data['net_balance'], Decimal('60000.00'), places=2)
