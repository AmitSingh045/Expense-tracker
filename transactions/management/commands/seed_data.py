from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import User, Profile
from transactions.models import Currency, PaymentMethod, Category, Transaction, Bill, Tag, RecurringTransaction
from budgets.models import Budget
from goals.models import Goal
from notifications.models import Notification
from decimal import Decimal
import datetime
import random

class Command(BaseCommand):
    help = "Seeds the database with default configuration and demo user transactions."

    def handle(self, *args, **options):
        self.stdout.write("Starting database seeding...")

        # 1. Create Currencies
        currencies_data = [
            {'code': 'USD', 'symbol': '$', 'exchange_rate_to_usd': Decimal('1.0000')},
            {'code': 'INR', 'symbol': '₹', 'exchange_rate_to_usd': Decimal('83.5000')},
            {'code': 'EUR', 'symbol': '€', 'exchange_rate_to_usd': Decimal('0.9200')},
            {'code': 'GBP', 'symbol': '£', 'exchange_rate_to_usd': Decimal('0.7900')},
            {'code': 'JPY', 'symbol': '¥', 'exchange_rate_to_usd': Decimal('155.0000')},
        ]
        currencies = {}
        for cur in currencies_data:
            obj, created = Currency.objects.get_or_create(
                code=cur['code'],
                defaults={'symbol': cur['symbol'], 'exchange_rate_to_usd': cur['exchange_rate_to_usd']}
            )
            currencies[cur['code']] = obj
            if created:
                self.stdout.write(f"Created currency: {cur['code']}")

        # 2. Create Default Categories (shared by user=None)
        default_categories = [
            {'name': 'Food', 'color': '#ffc107', 'icon': 'bi-egg-fried'},
            {'name': 'Travel', 'color': '#0dcaf0', 'icon': 'bi-airplane'},
            {'name': 'Shopping', 'color': '#fd7e14', 'icon': 'bi-bag-heart'},
            {'name': 'Medical', 'color': '#dc3545', 'icon': 'bi-heart-pulse'},
            {'name': 'Education', 'color': '#0d6efd', 'icon': 'bi-book'},
            {'name': 'Entertainment', 'color': '#6f42c1', 'icon': 'bi-controller'},
            {'name': 'Salary', 'color': '#198754', 'icon': 'bi-cash-stack'},
            {'name': 'Investment', 'color': '#20c997', 'icon': 'bi-graph-up-arrow'},
            {'name': 'Rent', 'color': '#6610f2', 'icon': 'bi-house'},
            {'name': 'Utilities', 'color': '#d63384', 'icon': 'bi-lightning-charge'},
            {'name': 'Fuel', 'color': '#adb5bd', 'icon': 'bi-fuel-pump'},
            {'name': 'Insurance', 'color': '#0f5132', 'icon': 'bi-shield-check'},
            {'name': 'Tax', 'color': '#842029', 'icon': 'bi-calculator'},
            {'name': 'Loan', 'color': '#084298', 'icon': 'bi-bank2'},
            {'name': 'Business', 'color': '#055160', 'icon': 'bi-briefcase'},
            {'name': 'Others', 'color': '#6c757d', 'icon': 'bi-question-circle'},
        ]
        categories = {}
        for cat in default_categories:
            obj, created = Category.objects.get_or_create(
                user=None,
                name=cat['name'],
                defaults={'color': cat['color'], 'icon': cat['icon']}
            )
            categories[cat['name']] = obj
            if created:
                self.stdout.write(f"Created default category: {cat['name']}")

        # 3. Create Default Payment Methods (shared by user=None)
        default_payment_methods = [
            {'name': 'Cash', 'icon': 'bi-cash'},
            {'name': 'UPI', 'icon': 'bi-phone'},
            {'name': 'Credit Card', 'icon': 'bi-credit-card'},
            {'name': 'Debit Card', 'icon': 'bi-credit-card-2-front'},
            {'name': 'Bank Transfer', 'icon': 'bi-bank'},
            {'name': 'PayPal', 'icon': 'bi-paypal'},
            {'name': 'Wallet', 'icon': 'bi-wallet2'},
            {'name': 'Net Banking', 'icon': 'bi-globe'},
        ]
        payment_methods = {}
        for pm in default_payment_methods:
            obj, created = PaymentMethod.objects.get_or_create(
                user=None,
                name=pm['name'],
                defaults={'icon': pm['icon']}
            )
            payment_methods[pm['name']] = obj
            if created:
                self.stdout.write(f"Created default payment method: {pm['name']}")

        # 4. Create Demo User and Superuser
        demo_user, created = User.objects.get_or_create(
            username='demo',
            defaults={
                'email': 'demo@example.com',
                'is_email_verified': True,
            }
        )
        if created:
            demo_user.set_password('Password123')
            demo_user.save()
            self.stdout.write("Created demo user (demo / Password123)")

        # Create admin user if not exists
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@example.com',
                'is_staff': True,
                'is_superuser': True,
                'is_email_verified': True,
            }
        )
        if created:
            admin_user.set_password('AdminPassword123')
            admin_user.save()
            self.stdout.write("Created admin user (admin / AdminPassword123)")

        # Set demo user preferences
        profile = demo_user.profile
        profile.preferred_currency = 'USD'
        profile.dark_mode = False
        profile.phone_number = '+15550199'
        profile.financial_health_score = 82
        profile.save()

        # Clean existing user data to make seed repeatable
        Transaction.objects.filter(user=demo_user).delete()
        Budget.objects.filter(user=demo_user).delete()
        Goal.objects.filter(user=demo_user).delete()
        Bill.objects.filter(user=demo_user).delete()
        Notification.objects.filter(user=demo_user).delete()

        # 5. Create Budgets
        # Monthly budget for Food: $400
        Budget.objects.create(
            user=demo_user,
            category=categories['Food'],
            amount=Decimal('400.00'),
            period='Monthly',
            start_date=datetime.date(2026, 6, 1),
            end_date=datetime.date(2026, 6, 30),
            alert_threshold=Decimal('90.00')
        )
        # Monthly budget for Travel: $200
        Budget.objects.create(
            user=demo_user,
            category=categories['Travel'],
            amount=Decimal('200.00'),
            period='Monthly',
            start_date=datetime.date(2026, 6, 1),
            end_date=datetime.date(2026, 6, 30),
            alert_threshold=Decimal('90.00')
        )
        # Monthly overall budget: $2000
        Budget.objects.create(
            user=demo_user,
            category=None,
            amount=Decimal('2000.00'),
            period='Monthly',
            start_date=datetime.date(2026, 6, 1),
            end_date=datetime.date(2026, 6, 30),
            alert_threshold=Decimal('85.00')
        )
        self.stdout.write("Created budgets for demo user")

        # 6. Create Goals
        Goal.objects.create(
            user=demo_user,
            name='Emergency Fund',
            goal_type='Emergency',
            target_amount=Decimal('5000.00'),
            current_amount=Decimal('3500.00'),
            target_date=datetime.date(2026, 12, 31)
        )
        Goal.objects.create(
            user=demo_user,
            name='Europe Vacation',
            goal_type='Vacation',
            target_amount=Decimal('3000.00'),
            current_amount=Decimal('1200.00'),
            target_date=datetime.date(2027, 6, 30)
        )
        Goal.objects.create(
            user=demo_user,
            name='New Laptop',
            goal_type='Custom',
            target_amount=Decimal('1500.00'),
            current_amount=Decimal('1500.00'), # Completed goal
            target_date=datetime.date(2026, 6, 15)
        )
        self.stdout.write("Created savings goals for demo user")

        # 7. Create Bills
        Bill.objects.create(
            user=demo_user,
            name='Electric Bill',
            category='Electricity',
            amount=Decimal('85.50'),
            due_date=datetime.date(2026, 7, 5),
            paid=False,
            recurring=True
        )
        Bill.objects.create(
            user=demo_user,
            name='Fiber Internet',
            category='Internet',
            amount=Decimal('59.99'),
            due_date=datetime.date(2026, 7, 10),
            paid=True, # Already paid for current cycle
            recurring=True
        )
        Bill.objects.create(
            user=demo_user,
            name='Appartment Rent',
            category='Rent',
            amount=Decimal('1200.00'),
            due_date=datetime.date(2026, 7, 1),
            paid=False,
            recurring=True
        )
        self.stdout.write("Created bills for demo user")

        # 8. Create Transactions
        # Income
        Transaction.objects.create(
            user=demo_user,
            title='Monthly Salary',
            description='Tech Corp Monthly Net Salary',
            amount=Decimal('4500.00'),
            transaction_type='Income',
            date=datetime.date(2026, 6, 1),
            category=categories['Salary'],
            payment_method=payment_methods['Bank Transfer'],
            currency=currencies['USD'],
            tags='salary,techcorp'
        )

        Transaction.objects.create(
            user=demo_user,
            title='Stock Dividend',
            amount=Decimal('150.00'),
            transaction_type='Income',
            date=datetime.date(2026, 6, 15),
            category=categories['Investment'],
            payment_method=payment_methods['Bank Transfer'],
            currency=currencies['USD'],
            tags='dividend,stocks'
        )

        # Expenses
        expenses_pool = [
            ('Whole Foods Grocery', 'Food', Decimal('84.20'), datetime.date(2026, 6, 3), 'Credit Card', 'groceries,organic'),
            ('Starbucks Coffee', 'Food', Decimal('6.75'), datetime.date(2026, 6, 4), 'UPI', 'coffee,daily'),
            ('Uber Ride to Work', 'Travel', Decimal('18.50'), datetime.date(2026, 6, 5), 'Wallet', 'taxi,commute'),
            ('Gas Station Fuel', 'Fuel', Decimal('45.00'), datetime.date(2026, 6, 8), 'Credit Card', 'car,fuel'),
            ('Amazon Kindle Book', 'Shopping', Decimal('12.99'), datetime.date(2026, 6, 10), 'Debit Card', 'books,education'),
            ('Netflix Subscription', 'Entertainment', Decimal('19.99'), datetime.date(2026, 6, 12), 'Credit Card', 'subscription,movies'),
            ('Sushi Dinner', 'Food', Decimal('58.00'), datetime.date(2026, 6, 14), 'Credit Card', 'dinner,social'),
            ('Cinema Tickets', 'Entertainment', Decimal('28.50'), datetime.date(2026, 6, 15), 'UPI', 'movies'),
            ('Pharmacy Medicines', 'Medical', Decimal('35.40'), datetime.date(2026, 6, 18), 'Cash', 'health,pills'),
            ('Gym Membership', 'Utilities', Decimal('50.00'), datetime.date(2026, 6, 20), 'Credit Card', 'fitness,gym'),
            ('Walmart General', 'Shopping', Decimal('112.10'), datetime.date(2026, 6, 22), 'Debit Card', 'household'),
            ('Coffee and Pastries', 'Food', Decimal('12.50'), datetime.date(2026, 6, 24), 'UPI', 'coffee,snack'),
            ('Local Train Ticket', 'Travel', Decimal('4.50'), datetime.date(2026, 6, 25), 'Cash', 'train,commute'),
            ('Italian Restaurant', 'Food', Decimal('72.00'), datetime.date(2026, 6, 26), 'Credit Card', 'dinner,date'),
            ('Target Shopping', 'Shopping', Decimal('89.45'), datetime.date(2026, 6, 27), 'Credit Card', 'clothes'),
            ('Dentist Checkup', 'Medical', Decimal('120.00'), datetime.date(2026, 6, 28), 'Debit Card', 'dental,health'),
        ]

        for title, cat_name, amt, dt, pm_name, tags in expenses_pool:
            Transaction.objects.create(
                user=demo_user,
                title=title,
                amount=amt,
                transaction_type='Expense',
                date=dt,
                category=categories[cat_name],
                payment_method=payment_methods[pm_name],
                currency=currencies['USD'],
                tags=tags
            )

        # Let's add a couple of international currency transactions to test currency conversion
        Transaction.objects.create(
            user=demo_user,
            title='Souvenir in Mumbai',
            amount=Decimal('4200.00'), # ~50 USD
            transaction_type='Expense',
            date=datetime.date(2026, 6, 10),
            category=categories['Shopping'],
            payment_method=payment_methods['Cash'],
            currency=currencies['INR'],
            tags='souvenir,india'
        )

        Transaction.objects.create(
            user=demo_user,
            title='Dinner in Paris',
            amount=Decimal('65.00'), # ~70 USD
            transaction_type='Expense',
            date=datetime.date(2026, 6, 20),
            category=categories['Food'],
            payment_method=payment_methods['Credit Card'],
            currency=currencies['EUR'],
            tags='dinner,paris,vacation'
        )

        self.stdout.write("Created expense transactions for demo user")

        # 9. Create Tags and associate with Transactions
        tag_names = ['groceries', 'travel', 'leisure', 'utilities', 'income', 'salary', 'household', 'vacation', 'health']
        db_tags = {}
        for tn in tag_names:
            t_obj, _ = Tag.objects.get_or_create(user=demo_user, name=tn)
            db_tags[tn] = t_obj

        # Associate M2M tags for all transactions
        for tx in Transaction.objects.filter(user=demo_user):
            if tx.tags:
                tag_list = [x.strip() for x in tx.tags.split(',') if x.strip()]
                for tg in tag_list:
                    if tg in db_tags:
                        tx.tags_m2m.add(db_tags[tg])

        self.stdout.write("Created tags and associated with transactions")

        # 10. Create Recurring Transactions
        RecurringTransaction.objects.create(
            user=demo_user,
            title='Monthly Apartment Rent',
            amount=Decimal('1200.00'),
            transaction_type='Expense',
            category=categories['Rent'],
            payment_method=payment_methods['Bank Transfer'],
            currency=currencies['USD'],
            frequency='Monthly',
            start_date=datetime.date(2026, 1, 1),
            end_date=datetime.date(2026, 12, 31),
            next_run=datetime.date(2026, 7, 1)
        )
        RecurringTransaction.objects.create(
            user=demo_user,
            title='Monthly Net Salary',
            amount=Decimal('4500.00'),
            transaction_type='Income',
            category=categories['Salary'],
            payment_method=payment_methods['Bank Transfer'],
            currency=currencies['USD'],
            frequency='Monthly',
            start_date=datetime.date(2026, 1, 1),
            end_date=datetime.date(2026, 12, 31),
            next_run=datetime.date(2026, 7, 1)
        )
        self.stdout.write("Created recurring transactions for demo user")

        # 11. Create Notifications
        Notification.objects.create(
            user=demo_user,
            title='Budget Warning',
            message='You have spent 92% of your monthly Food budget.',
            notification_type='Budget Alert'
        )
        Notification.objects.create(
            user=demo_user,
            title='Upcoming Bill Reminder',
            message='Your Appartment Rent bill of $1200.00 is due in 2 days.',
            notification_type='Bill Reminder'
        )
        Notification.objects.create(
            user=demo_user,
            title='Goal Completed!',
            message='Congratulations! You have reached your savings goal "New Laptop".',
            notification_type='Goal Completed'
        )
        self.stdout.write("Created notifications for demo user")

        # 12. Create Activity Logs & Audit Logs
        from accounts.models import ActivityLog, AuditLog
        ActivityLog.objects.create(
            user=demo_user,
            action='User Login',
            ip_address='127.0.0.1',
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        ActivityLog.objects.create(
            user=demo_user,
            action='Modified Profile settings',
            ip_address='127.0.0.1',
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )

        AuditLog.objects.create(
            user=demo_user,
            model_name='Transaction',
            object_id=999,
            action='Create',
            changes={'title': 'Whole Foods Grocery', 'amount': 84.20}
        )
        self.stdout.write("Created activity and audit logs")

        self.stdout.write(self.style.SUCCESS("Database seeding completed successfully!"))

