from django.db import models
from django.conf import settings
from transactions.models import Category

class Budget(models.Model):
    PERIOD_CHOICES = [
        ('Daily', 'Daily'),
        ('Weekly', 'Weekly'),
        ('Monthly', 'Monthly'),
        ('Yearly', 'Yearly'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='budgets')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='budgets', null=True, blank=True) # Null category represents overall budget
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    period = models.CharField(max_length=15, choices=PERIOD_CHOICES, default='Monthly')
    start_date = models.DateField()
    end_date = models.DateField()
    alert_threshold = models.DecimalField(max_digits=5, decimal_places=2, default=90.0) # Percentage (e.g. 90% spent alert)
    is_alerted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        cat_name = self.category.name if self.category else "Overall"
        return f"{self.user.username}'s {self.period} Budget for {cat_name} - {self.amount}"
