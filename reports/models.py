from django.db import models
from django.conf import settings

class Report(models.Model):
    REPORT_TYPES = [
        ('Daily', 'Daily Report'),
        ('Weekly', 'Weekly Report'),
        ('Monthly', 'Monthly Report'),
        ('Yearly', 'Yearly Report'),
        ('Custom', 'Custom Report'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reports')
    title = models.CharField(max_length=150)
    report_type = models.CharField(max_length=15, choices=REPORT_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    file = models.FileField(upload_to='reports/', blank=True, null=True)
    generated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.report_type}) - {self.user.username}"
