from django.test import TestCase
from accounts.models import User
from transactions.models import Currency, Category, PaymentMethod, Transaction
from budgets.models import Budget
from budgets.views import get_budget_spent
from decimal import Decimal
import datetime

class BudgetLogicTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='budgetuser', email='budget@example.com', password='Password123')
        self.currency = Currency.objects.create(code='USD', symbol='$', exchange_rate_to_usd=Decimal('1.0000'))
        self.category = Category.objects.create(user=self.user, name='Food', color='#ffc107', icon='bi-egg-fried')
        self.pm = PaymentMethod.objects.create(user=self.user, name='Cash', icon='bi-cash')

    def test_budget_spent_calculation(self):
        # Create budget for food: $100
        budget = Budget.objects.create(
            user=self.user, category=self.category, amount=Decimal('100.00'),
            period='Monthly', start_date=datetime.date(2026, 6, 1), end_date=datetime.date(2026, 6, 30)
        )
        
        # Create transaction within budget period
        Transaction.objects.create(
            user=self.user, title='Lunch', amount=Decimal('25.50'), transaction_type='Expense',
            date=datetime.date(2026, 6, 15), category=self.category, payment_method=self.pm, currency=self.currency
        )
        
        # Create transaction outside budget period
        Transaction.objects.create(
            user=self.user, title='Dinner', amount=Decimal('30.00'), transaction_type='Expense',
            date=datetime.date(2026, 7, 10), category=self.category, payment_method=self.pm, currency=self.currency
        )

        spent = get_budget_spent(budget)
        self.assertEqual(spent, Decimal('25.50'))
        
        # Verify budget is not exceeded
        self.assertFalse(spent > budget.amount)
