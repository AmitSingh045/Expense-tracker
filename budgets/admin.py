from django.contrib import admin
from django.utils.html import format_html
from .models import Budget

@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('user', 'category_name', 'amount', 'period', 'start_date', 'end_date', 'alert_threshold', 'alerted_badge')
    list_filter = ('period', 'start_date', 'end_date', 'is_alerted', 'category', 'user')
    search_fields = ('user__username', 'category__name', 'amount')
    date_hierarchy = 'start_date'
    ordering = ('-start_date',)
    list_per_page = 20
    actions = ['reset_alert_state', 'trigger_mock_alert']

    @admin.display(description='Category')
    def category_name(self, obj):
        return obj.category.name if obj.category else "Overall Budget"

    @admin.display(description='Threshold Met')
    def alerted_badge(self, obj):
        if obj.is_alerted:
            return format_html('<span style="color: #ef4444; font-weight: bold;">&#9888; Triggered</span>')
        return format_html('<span style="color: #10b981; font-weight: bold;">Under Control</span>')

    @admin.action(description='Reset budget alert states')
    def reset_alert_state(self, request, queryset):
        rows = queryset.update(is_alerted=False)
        self.message_user(request, f"Alert triggers cleared for {rows} budgets.")

    @admin.action(description='Trigger mock overspending alerts')
    def trigger_mock_alert(self, request, queryset):
        from notifications.models import Notification
        for b in queryset:
            Notification.objects.create(
                user=b.user, title='System Mock: Budget Exceeded',
                message=f"Alert: You have reached the {b.alert_threshold}% threshold on your {b.category.name if b.category else 'overall'} budget limit of ${b.amount}.",
                notification_type='Budget Alert'
            )
            b.is_alerted = True
            b.save()
        self.message_user(request, f"Mock overspending alerts triggered for {queryset.count()} budgets.")
