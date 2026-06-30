from django.contrib import admin
from django.utils.html import format_html
from .models import Report

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'report_type', 'start_date', 'end_date', 'download_link', 'generated_at')
    list_filter = ('report_type', 'generated_at', 'user')
    search_fields = ('title', 'user__username')
    ordering = ('-generated_at',)
    list_per_page = 20

    @admin.display(description='Document')
    def download_link(self, obj):
        if obj.file:
            return format_html('<a href="{}" download style="font-weight: bold; text-decoration: none; color: #3b82f6;"><i class="bi bi-file-earmark-pdf"></i> Download PDF</a>', obj.file.url)
        return "No File"
