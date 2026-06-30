from django.contrib import admin
from django.utils.html import format_html
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'notification_type', 'is_read_badge', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at', 'user')
    search_fields = ('title', 'message', 'user__username')
    ordering = ('-created_at',)
    list_per_page = 30
    actions = ['mark_as_read', 'mark_as_unread']

    @admin.display(description='Read Status')
    def is_read_badge(self, obj):
        if obj.is_read:
            return format_html('<span style="color: #94a3b8;">Read</span>')
        return format_html('<span style="background-color: #dbeafe; color: #1e40af; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: bold;">Unread</span>')

    @admin.action(description='Mark selected notifications as read')
    def mark_as_read(self, request, queryset):
        rows = queryset.update(is_read=True)
        self.message_user(request, f"{rows} notifications marked as read.")

    @admin.action(description='Mark selected notifications as unread')
    def mark_as_unread(self, request, queryset):
        rows = queryset.update(is_read=False)
        self.message_user(request, f"{rows} notifications marked as unread.")
