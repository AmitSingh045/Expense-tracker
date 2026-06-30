from django.db import models
from django.conf import settings

class Currency(models.Model):
    code = models.CharField(max_length=3, unique=True)
    symbol = models.CharField(max_length=5)
    exchange_rate_to_usd = models.DecimalField(max_digits=12, decimal_places=4, default=1.0)

    def __str__(self):
        return f"{self.code} ({self.symbol})"

class PaymentMethod(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payment_methods', null=True, blank=True)
    name = models.CharField(max_length=50)
    icon = models.CharField(max_length=50, default='bi-wallet2') # Bootstrap icon class

    def __str__(self):
        return self.name

class Category(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='categories', null=True, blank=True)
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default='#0d6efd') # Hex color (e.g. #0d6efd)
    icon = models.CharField(max_length=50, default='bi-tags') # Bootstrap icon class
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Categories'
        unique_together = ('user', 'name')

    def __str__(self):
        return self.name

class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('Income', 'Income'),
        ('Expense', 'Expense'),
        ('Transfer', 'Transfer'),
        ('Refund', 'Refund'),
        ('Investment', 'Investment'),
        ('Loan', 'Loan'),
    ]

    RECURRING_CHOICES = [
        ('Daily', 'Daily'),
        ('Weekly', 'Weekly'),
        ('Monthly', 'Monthly'),
        ('Quarterly', 'Quarterly'),
        ('Yearly', 'Yearly'),
        ('None', 'None'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions')
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(max_length=15, choices=TRANSACTION_TYPES)
    date = models.DateField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='transactions')
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True, related_name='transactions')
    currency = models.ForeignKey(Currency, on_delete=models.SET_NULL, null=True, related_name='transactions')
    tags = models.CharField(max_length=255, blank=True, null=True) # Comma-separated tags
    tags_m2m = models.ManyToManyField('Tag', blank=True, related_name='transactions')
    location = models.CharField(max_length=100, blank=True, null=True)
    is_recurring = models.BooleanField(default=False)
    recurring_period = models.CharField(max_length=15, choices=RECURRING_CHOICES, default='None')
    reminder = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.amount} {self.currency.code if self.currency else ''}"

class Receipt(models.Model):
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, related_name='receipt')
    file = models.FileField(upload_to='receipts/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    ocr_raw_text = models.TextField(blank=True, null=True)
    ocr_parsed_json = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"Receipt for {self.transaction.title}"

class Bill(models.Model):
    BILL_CATEGORIES = [
        ('Electricity', 'Electricity'),
        ('Internet', 'Internet'),
        ('Mobile', 'Mobile'),
        ('Gas', 'Gas'),
        ('Water', 'Water'),
        ('Rent', 'Rent'),
        ('EMI', 'EMI'),
        ('Insurance', 'Insurance'),
        ('Subscription', 'Subscription'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bills')
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50, choices=BILL_CATEGORIES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    due_date = models.DateField()
    paid = models.BooleanField(default=False)
    recurring = models.BooleanField(default=False)
    reminder_days_before = models.IntegerField(default=3)

    def __str__(self):
        return f"{self.name} - {self.amount} (Due: {self.due_date})"

class Tag(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='custom_tags', null=True, blank=True)
    name = models.CharField(max_length=50)

    class Meta:
        unique_together = ('user', 'name')

    def __str__(self):
        return self.name

class RecurringTransaction(models.Model):
    FREQUENCY_CHOICES = [
        ('Daily', 'Daily'),
        ('Weekly', 'Weekly'),
        ('Monthly', 'Monthly'),
        ('Quarterly', 'Quarterly'),
        ('Yearly', 'Yearly'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='recurring_transactions')
    title = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(max_length=15, choices=Transaction.TRANSACTION_TYPES)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='recurring_transactions')
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True, related_name='recurring_transactions')
    currency = models.ForeignKey(Currency, on_delete=models.SET_NULL, null=True, related_name='recurring_transactions')
    frequency = models.CharField(max_length=15, choices=FREQUENCY_CHOICES, default='Monthly')
    start_date = models.DateField()
    end_date = models.DateField()
    last_run = models.DateField(blank=True, null=True)
    next_run = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Recurring: {self.title} ({self.frequency}) - {self.amount}"

