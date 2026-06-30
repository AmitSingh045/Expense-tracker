from django.contrib import admin
from django.utils.html import format_html
from .models import Goal
from decimal import Decimal

@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'goal_type', 'target_amount', 'current_amount', 'progress_bar', 'status_badge')
    list_filter = ('goal_type', 'target_date', 'user')
    search_fields = ('name', 'user__username', 'target_amount')
    date_hierarchy = 'target_date'
    ordering = ('target_date',)
    list_per_page = 20
    actions = ['add_hundred_dollars', 'complete_selected_goals']

    @admin.display(description='Progress')
    def progress_bar(self, obj):
        percent = obj.progress_percentage
        color = '#10b981' if percent >= 100 else '#0ea5e9'
        return format_html(
            '<div style="width: 100px; background-color: #e2e8f0; border-radius: 4px; overflow: hidden; display: inline-block; vertical-align: middle; margin-right: 8px;">'
            '  <div style="width: {}px; background-color: {}; height: 8px;"></div>'
            '</div>'
            '<span>{}%</span>',
            int(percent), color, percent
        )

    @admin.display(description='Status')
    def status_badge(self, obj):
        if obj.is_completed:
            return format_html('<span style="color: #10b981; font-weight: bold;">&#10004; Achieved</span>')
        return format_html('<span style="color: #64748b;">In Progress</span>')

    # Bulk actions
    @admin.action(description='Allocate +$100 to selected goals')
    def add_hundred_dollars(self, request, queryset):
        for g in queryset:
            g.current_amount += Decimal('100.00')
            g.save()
        self.message_user(request, "Added $100 allocation to selected goals.")

    @admin.action(description='Instantly complete selected goals')
    def complete_selected_goals(self, request, queryset):
        for g in queryset:
            g.current_amount = g.target_amount
            g.save()
        self.message_user(request, "Selected goals completed.")
