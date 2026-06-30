from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from accounts.models import User
from transactions.models import Currency, Category, PaymentMethod, Transaction
from decimal import Decimal
import datetime

class AnalyticsAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='analyticsuser', email='analytics@example.com', password='Password123')
        self.client.force_authenticate(user=self.user)
        
        self.currency = Currency.objects.create(code='USD', symbol='$', exchange_rate_to_usd=Decimal('1.0000'))
        self.category = Category.objects.create(user=self.user, name='Food', color='#ffc107', icon='bi-egg-fried')
        self.pm = PaymentMethod.objects.create(user=self.user, name='Cash', icon='bi-cash')

        # Add initial transactions
        # Income $1000
        Transaction.objects.create(
            user=self.user, title='Freelance', amount=Decimal('1000.00'), transaction_type='Income',
            date=datetime.date.today(), category=self.category, payment_method=self.pm, currency=self.currency
        )
        # Expense $300
        Transaction.objects.create(
            user=self.user, title='Grocery', amount=Decimal('300.00'), transaction_type='Expense',
            date=datetime.date.today(), category=self.category, payment_method=self.pm, currency=self.currency
        )

    def test_dashboard_data_api(self):
        url = '/api/analytics/dashboard-data/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Assert KPIs are correct
        self.assertEqual(response.data['kpis']['income'], 1000.0)
        self.assertEqual(response.data['kpis']['expense'], 300.0)
        self.assertEqual(response.data['kpis']['balance'], 700.0)
        # Savings ratio = (700/1000)*100 = 70.0%
        self.assertEqual(response.data['kpis']['savings_ratio'], 70.0)
        # Financial Health score should be calculated
        self.assertTrue('health_score' in response.data['kpis'])
        self.assertTrue(response.data['kpis']['health_score'] > 0)
