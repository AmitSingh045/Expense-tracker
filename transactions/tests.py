from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from accounts.models import User
from transactions.models import Currency, Category, PaymentMethod, Transaction
from decimal import Decimal
import datetime

class TransactionAPITests(APITestCase):
    def setUp(self):
        # Create user
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='Password123')
        self.client.force_authenticate(user=self.user)
        
        # Create prerequisite models
        self.currency = Currency.objects.create(code='USD', symbol='$', exchange_rate_to_usd=Decimal('1.0000'))
        self.category = Category.objects.create(user=self.user, name='Food', color='#ffc107', icon='bi-egg-fried')
        self.pm = PaymentMethod.objects.create(user=self.user, name='Cash', icon='bi-cash')

    def test_create_transaction_api(self):
        url = '/api/transactions/'
        data = {
            'title': 'Lunch expense',
            'amount': '15.50',
            'transaction_type': 'Expense',
            'date': '2026-06-30',
            'category': self.category.id,
            'payment_method': self.pm.id,
            'currency': self.currency.id,
            'tags': 'lunch,restaurant'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Transaction.objects.filter(user=self.user).count(), 1)
        self.assertEqual(Transaction.objects.first().title, 'Lunch expense')

    def test_bulk_delete_api(self):
        # Create multiple transactions
        t1 = Transaction.objects.create(
            user=self.user, title='Tx 1', amount=Decimal('10.00'), transaction_type='Expense',
            date=datetime.date.today(), category=self.category, payment_method=self.pm, currency=self.currency
        )
        t2 = Transaction.objects.create(
            user=self.user, title='Tx 2', amount=Decimal('20.00'), transaction_type='Expense',
            date=datetime.date.today(), category=self.category, payment_method=self.pm, currency=self.currency
        )
        
        url = '/api/transactions/bulk-delete/'
        data = {'ids': [t1.id, t2.id]}
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['deleted_count'], 2)
        self.assertEqual(Transaction.objects.filter(user=self.user).count(), 0)

    def test_csv_export_api(self):
        Transaction.objects.create(
            user=self.user, title='Lunch', amount=Decimal('15.50'), transaction_type='Expense',
            date=datetime.date.today(), category=self.category, payment_method=self.pm, currency=self.currency
        )
        
        url = '/api/transactions/export/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertTrue('Lunch' in response.content.decode('utf-8'))
