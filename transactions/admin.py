from django.contrib import admin
from django.utils.html import format_html
from django.http import HttpResponse
from django import forms
from .models import Currency, PaymentMethod, Category, Transaction, Receipt, Bill, Tag, RecurringTransaction
import csv
import pandas as pd
import io
import datetime

class ReceiptInline(admin.TabularInline):
    model = Receipt
    extra = 0
    readonly_fields = ['uploaded_at', 'ocr_raw_text', 'ocr_parsed_json']

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'user')
    list_filter = ('user',)
    search_fields = ('name', 'user__username')

@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ('code', 'symbol', 'exchange_rate_to_usd')
    search_fields = ('code', 'symbol')
    list_per_page = 20

@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon', 'user')
    list_filter = ('user',)
    search_fields = ('name',)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'color_badge', 'icon', 'user', 'created_at')
    list_filter = ('user', 'created_at')
    search_fields = ('name', 'user__username')
    list_per_page = 30

    @admin.display(description='Color')
    def color_badge(self, obj):
        return format_html('<span style="background-color: {}; width: 12px; height: 12px; display: inline-block; border-radius: 50%; border: 1px solid #ccc; margin-right: 5px;"></span> {}', obj.color, obj.color)

class TransactionAdminForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = '__all__'

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount <= 0:
            raise forms.ValidationError("Transaction amount must be positive.")
        return amount

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    form = TransactionAdminForm
    inlines = [ReceiptInline]
    list_display = ('title', 'user', 'formatted_amount', 'type_badge', 'date', 'category', 'payment_method', 'currency')
    list_filter = ('transaction_type', 'date', 'category', 'currency', 'payment_method', 'user')
    search_fields = ('title', 'description', 'amount', 'tags', 'location', 'user__username', 'category__name')
    date_hierarchy = 'date'
    ordering = ('-date', '-created_at')
    list_per_page = 30
    list_select_related = ('user', 'category', 'payment_method', 'currency')
    autocomplete_fields = ['category', 'payment_method', 'currency']
    filter_horizontal = ('tags_m2m',)
    actions = ['mark_as_income', 'mark_as_expense', 'export_selected_csv', 'export_selected_excel']

    @admin.display(description='Amount')
    def formatted_amount(self, obj):
        symbol = obj.currency.symbol if obj.currency else '$'
        return f"{symbol}{obj.amount}"

    @admin.display(description='Type')
    def type_badge(self, obj):
        if obj.transaction_type == 'Income':
            return format_html('<span style="color: #10b981; font-weight: bold;">+ Income</span>')
        elif obj.transaction_type == 'Expense':
            return format_html('<span style="color: #ef4444; font-weight: bold;">- Expense</span>')
        return format_html('<span style="color: #0ea5e9; font-weight: bold;">{}</span>', obj.transaction_type)

    # Bulk Actions
    @admin.action(description='Mark selected as Income')
    def mark_as_income(self, request, queryset):
        rows = queryset.update(transaction_type='Income')
        self.message_user(request, f"{rows} transactions marked as Income.")

    @admin.action(description='Mark selected as Expense')
    def mark_as_expense(self, request, queryset):
        rows = queryset.update(transaction_type='Expense')
        self.message_user(request, f"{rows} transactions marked as Expense.")

    @admin.action(description='Export selected to CSV')
    def export_selected_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="transactions_export.csv"'
        writer = csv.writer(response)
        writer.writerow(['ID', 'Title', 'Amount', 'Type', 'Date', 'Category', 'User'])
        for tx in queryset:
            writer.writerow([tx.id, tx.title, tx.amount, tx.transaction_type, tx.date, tx.category.name, tx.user.username])
        return response

    @admin.action(description='Export selected to Excel')
    def export_selected_excel(self, request, queryset):
        data = [{
            'ID': tx.id, 'Title': tx.title, 'Amount': float(tx.amount), 'Type': tx.transaction_type,
            'Date': str(tx.date), 'Category': tx.category.name, 'User': tx.user.username
        } for tx in queryset]
        df = pd.DataFrame(data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Transactions')
        
        response = HttpResponse(output.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="transactions_export.xlsx"'
        return response

@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'category', 'amount', 'due_date', 'paid_status', 'recurring')
    list_filter = ('paid', 'recurring', 'due_date', 'category', 'user')
    search_fields = ('name', 'user__username', 'amount')
    date_hierarchy = 'due_date'
    ordering = ('due_date',)
    list_per_page = 25
    actions = ['mark_bill_paid', 'mark_bill_unpaid', 'send_reminder']

    @admin.display(description='Paid Status')
    def paid_status(self, obj):
        if obj.paid:
            return format_html('<span style="color: #10b981; font-weight: bold;">Paid</span>')
        return format_html('<span style="color: #ef4444; font-weight: bold;">Unpaid</span>')

    # Bulk Actions
    @admin.action(description='Mark selected bills as Paid')
    def mark_bill_paid(self, request, queryset):
        for b in queryset:
            # Mark paid using custom handler which creates transaction records too
            if not b.paid:
                b.paid = True
                b.save()
                
                # Create corresponding transaction log
                cat_obj, _ = Category.objects.get_or_create(user=b.user, name='Utilities')
                pm_obj = PaymentMethod.objects.filter(user=b.user).first()
                cur_obj = Currency.objects.get(code='USD')
                
                Transaction.objects.create(
                    user=b.user, title=f"Paid Bill: {b.name}", amount=b.amount,
                    transaction_type='Expense', date=datetime.date.today(),
                    category=cat_obj, payment_method=pm_obj, currency=cur_obj,
                    tags='bill,paid'
                )
        self.message_user(request, f"{queryset.count()} bills marked as Paid. Transaction logs created.")

    @admin.action(description='Mark selected bills as Unpaid')
    def mark_bill_unpaid(self, request, queryset):
        rows = queryset.update(paid=False)
        self.message_user(request, f"{rows} bills reverted to Unpaid.")

    @admin.action(description='Mock: Send Reminder notifications')
    def send_reminder(self, request, queryset):
        from notifications.models import Notification
        for b in queryset:
            Notification.objects.create(
                user=b.user, title=f"Bill Reminder: {b.name}",
                message=f"Reminder: your bill '{b.name}' of ${b.amount} is due on {b.due_date}.",
                notification_type='Bill Reminder'
            )
        self.message_user(request, f"Reminder alerts sent for {queryset.count()} bills.")

@admin.register(RecurringTransaction)
class RecurringTransactionAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'amount', 'transaction_type', 'frequency', 'next_run', 'is_active')
    list_filter = ('frequency', 'is_active', 'transaction_type', 'user')
    search_fields = ('title', 'user__username', 'amount')
    date_hierarchy = 'next_run'
    ordering = ('next_run',)
    list_per_page = 20
    actions = ['activate_schedules', 'deactivate_schedules']

    @admin.action(description='Activate selected schedules')
    def activate_schedules(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, "Selected recurring schedules activated.")

    @admin.action(description='Deactivate selected schedules')
    def deactivate_schedules(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, "Selected recurring schedules deactivated.")
