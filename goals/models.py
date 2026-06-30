from django.db import models
from django.conf import settings

class Goal(models.Model):
    GOAL_TYPES = [
        ('Savings', 'Savings Goal'),
        ('Emergency', 'Emergency Fund'),
        ('Vacation', 'Vacation Goal'),
        ('Car', 'Car Goal'),
        ('House', 'House Goal'),
        ('Education', 'Education Goal'),
        ('Custom', 'Custom Goal'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='goals')
    name = models.CharField(max_length=100)
    goal_type = models.CharField(max_length=20, choices=GOAL_TYPES, default='Savings')
    target_amount = models.DecimalField(max_digits=12, decimal_places=2)
    current_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    target_date = models.DateField()
    completed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def progress_percentage(self):
        if self.target_amount <= 0:
            return 0
        percentage = (self.current_amount / self.target_amount) * 100
        return min(round(percentage, 2), 100)

    @property
    def is_completed(self):
        return self.current_amount >= self.target_amount

    def save(self, *args, **kwargs):
        from django.utils import timezone
        if self.is_completed and not self.completed_at:
            self.completed_at = timezone.now()
        elif not self.is_completed:
            self.completed_at = None
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.progress_percentage}%)"
