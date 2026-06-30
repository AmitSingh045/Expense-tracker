from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.db.models import Q
from django.core.paginator import Paginator
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Currency, PaymentMethod, Category, Transaction, Receipt, Bill
from .serializers import (
    CurrencySerializer, PaymentMethodSerializer, CategorySerializer,
    TransactionSerializer, ReceiptSerializer, BillSerializer
)
import csv
import datetime
import pandas as pd
from decimal import Decimal
import json

# ----------------- HTML VIEWS -----------------

@login_required
def transactions_list_view(request):
    user = request.user
    tx_queryset = Transaction.objects.filter(user=user).select_related('category', 'payment_method', 'currency').order_by('-date', '-created_at')

    # Search
    q = request.GET.get('q', '').strip()
    if q:
        tx_queryset = tx_queryset.filter(
            Q(title__icontains=q) |
            Q(description__icontains=q) |
            Q(tags__icontains=q) |
            Q(location__icontains=q)
        )

    # Filter Category
    category_filter = request.GET.get('category')
    if category_filter and category_filter != 'None' and category_filter != '':
        tx_queryset = tx_queryset.filter(category_id=category_filter)

    # Filter Transaction Type
    type_filter = request.GET.get('type')
    if type_filter and type_filter != 'None' and type_filter != '':
        tx_queryset = tx_queryset.filter(transaction_type=type_filter)

    # Filter Date Range
    date_filter = request.GET.get('date_filter')
    today = datetime.date.today()
    if date_filter == 'today':
        tx_queryset = tx_queryset.filter(date=today)
    elif date_filter == 'yesterday':
        tx_queryset = tx_queryset.filter(date=today - datetime.timedelta(days=1))
    elif date_filter == 'week':
        start_week = today - datetime.timedelta(days=today.weekday())
        tx_queryset = tx_queryset.filter(date__gte=start_week)
    elif date_filter == 'month':
        tx_queryset = tx_queryset.filter(date__year=today.year, date__month=today.month)
    elif date_filter == 'year':
        tx_queryset = tx_queryset.filter(date__year=today.year)
    elif date_filter == 'custom':
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        if start_date:
            tx_queryset = tx_queryset.filter(date__gte=start_date)
        if end_date:
            tx_queryset = tx_queryset.filter(date__lte=end_date)

    # Sort
    sort_by = request.GET.get('sort', 'newest')
    if sort_by == 'oldest':
        tx_queryset = tx_queryset.order_by('date', 'created_at')
    elif sort_by == 'highest':
        tx_queryset = tx_queryset.order_by('-amount')
    elif sort_by == 'lowest':
        tx_queryset = tx_queryset.order_by('amount')

    # Paginate
    paginator = Paginator(tx_queryset, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Context Data
    user_categories = Category.objects.filter(Q(user=user) | Q(user=None))
    user_pms = PaymentMethod.objects.filter(Q(user=user) | Q(user=None))
    user_currencies = Currency.objects.all()

    # Form submissions
    if request.method == 'POST':
        action_type = request.POST.get('action')
        
        if action_type == 'add_transaction':
            title = request.POST.get('title')
            amount = request.POST.get('amount')
            tx_type = request.POST.get('transaction_type')
            date_str = request.POST.get('date') or str(today)
            cat_id = request.POST.get('category')
            pm_id = request.POST.get('payment_method')
            cur_id = request.POST.get('currency')
            tags = request.POST.get('tags', '')
            desc = request.POST.get('description', '')
            location = request.POST.get('location', '')
            
            cat_obj = get_object_or_404(Category, id=cat_id)
            pm_obj = get_object_or_404(PaymentMethod, id=pm_id)
            cur_obj = get_object_or_404(Currency, id=cur_id)
            
            tx = Transaction.objects.create(
                user=user, title=title, amount=Decimal(amount), transaction_type=tx_type,
                date=date_str, category=cat_obj, payment_method=pm_obj, currency=cur_obj,
                tags=tags, description=desc, location=location
            )
            
            # Receipt Upload check
            if 'receipt_file' in request.FILES:
                receipt_file = request.FILES['receipt_file']
                ocr_text = f"Parsed Store: Mock Store\nTotal: {amount}\nDate: {date_str}\nItems: Transaction added via form."
                ocr_data = {
                    'merchant': 'Mock Merchant',
                    'total': float(amount),
                    'date': date_str,
                    'category': cat_obj.name,
                    'items': [{'name': title, 'price': float(amount)}]
                }
                Receipt.objects.create(
                    transaction=tx,
                    file=receipt_file,
                    ocr_raw_text=ocr_text,
                    ocr_parsed_json=ocr_data
                )
            
            # Trigger Budget limit alert check
            check_budget_alerts(user, cat_obj, tx)

            messages.success(request, "Transaction added successfully.")
            return redirect('transactions_list')

        elif action_type == 'edit_transaction':
            tx_id = request.POST.get('transaction_id')
            tx = get_object_or_404(Transaction, id=tx_id, user=user)
            tx.title = request.POST.get('title')
            tx.amount = Decimal(request.POST.get('amount'))
            tx.transaction_type = request.POST.get('transaction_type')
            tx.date = request.POST.get('date') or tx.date
            tx.category = get_object_or_404(Category, id=request.POST.get('category'))
            tx.payment_method = get_object_or_404(PaymentMethod, id=request.POST.get('payment_method'))
            tx.currency = get_object_or_404(Currency, id=request.POST.get('currency'))
            tx.tags = request.POST.get('tags', '')
            tx.description = request.POST.get('description', '')
            tx.location = request.POST.get('location', '')
            tx.save()

            if 'receipt_file' in request.FILES:
                # remove old receipt
                if hasattr(tx, 'receipt'):
                    tx.receipt.file.delete()
                    tx.receipt.delete()
                Receipt.objects.create(
                    transaction=tx,
                    file=request.FILES['receipt_file'],
                    ocr_raw_text="Mock Receipt text.",
                    ocr_parsed_json={'merchant': 'Edited Merchant', 'total': float(tx.amount)}
                )

            messages.success(request, "Transaction updated successfully.")
            return redirect('transactions_list')

        elif action_type == 'delete_transaction':
            tx_id = request.POST.get('transaction_id')
            tx = get_object_or_404(Transaction, id=tx_id, user=user)
            tx.delete()
            messages.success(request, "Transaction deleted successfully.")
            return redirect('transactions_list')

        elif action_type == 'add_category':
            name = request.POST.get('name')
            color = request.POST.get('color', '#0d6efd')
            icon = request.POST.get('icon', 'bi-tags')
            
            # Check unique name for user
            if Category.objects.filter(Q(user=user) | Q(user=None), name__iexact=name).exists():
                messages.error(request, "Category with this name already exists.")
            else:
                Category.objects.create(user=user, name=name, color=color, icon=icon)
                messages.success(request, f"Category '{name}' created successfully.")
            return redirect('transactions_list')

    return render(request, 'transactions/transactions.html', {
        'page_obj': page_obj,
        'categories': user_categories,
        'payment_methods': user_pms,
        'currencies': user_currencies,
        'q': q,
        'selected_category': category_filter,
        'selected_type': type_filter,
        'date_filter': date_filter,
        'start_date': request.GET.get('start_date', ''),
        'end_date': request.GET.get('end_date', ''),
        'sort': sort_by
    })

@login_required
def bills_list_view(request):
    user = request.user
    bills = Bill.objects.filter(user=user).order_by('due_date')

    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_bill':
            name = request.POST.get('name')
            category = request.POST.get('category')
            amount = Decimal(request.POST.get('amount'))
            due_date = request.POST.get('due_date')
            recurring = request.POST.get('recurring') == 'true'
            remind = int(request.POST.get('reminder_days_before', 3))
            
            Bill.objects.create(
                user=user, name=name, category=category, amount=amount,
                due_date=due_date, recurring=recurring, reminder_days_before=remind
            )
            messages.success(request, "Bill added successfully.")
            return redirect('bills_list')

        elif action == 'pay_bill':
            bill_id = request.POST.get('bill_id')
            bill = get_object_or_404(Bill, id=bill_id, user=user)
            bill.paid = True
            bill.save()
            
            # Optionally convert Bill payment to a Transaction automatically!
            cat_obj, _ = Category.objects.get_or_create(
                user=user, name='Utilities',
                defaults={'color': '#d63384', 'icon': 'bi-lightning-charge'}
            )
            pm_obj = PaymentMethod.objects.filter(Q(user=user) | Q(user=None)).first()
            cur_obj = Currency.objects.filter(code=user.profile.preferred_currency).first() \
                or Currency.objects.filter(code='USD').first()

            Transaction.objects.create(
                user=user,
                title=f"Paid Bill: {bill.name}",
                amount=bill.amount,
                transaction_type='Expense',
                date=datetime.date.today(),
                category=cat_obj,
                payment_method=pm_obj,
                currency=cur_obj,
                tags='bill,paid'
            )

            # If recurring, set next due date automatically (e.g. 1 month later)
            if bill.recurring:
                # Add 30 days or 1 month
                next_due = bill.due_date + datetime.timedelta(days=30)
                Bill.objects.create(
                    user=user, name=bill.name, category=bill.category,
                    amount=bill.amount, due_date=next_due, recurring=True,
                    reminder_days_before=bill.reminder_days_before
                )
            
            messages.success(request, f"Bill '{bill.name}' marked as paid. Record added to Transactions.")
            return redirect('bills_list')

        elif action == 'delete_bill':
            bill_id = request.POST.get('bill_id')
            bill = get_object_or_404(Bill, id=bill_id, user=user)
            bill.delete()
            messages.success(request, "Bill deleted successfully.")
            return redirect('bills_list')

    return render(request, 'transactions/bills.html', {
        'bills': bills,
        'bill_categories': Bill.BILL_CATEGORIES
    })


# Helper function to trigger notification when budget is exceeded
def check_budget_alerts(user, category, tx):
    # Import inside function to prevent circular import
    from budgets.models import Budget
    from notifications.models import Notification

    # 1. Check category budget
    budgets = Budget.objects.filter(user=user, category=category)
    # 2. Check overall budget
    overall_budgets = Budget.objects.filter(user=user, category=None)

    all_budgets = list(budgets) + list(overall_budgets)
    for b in all_budgets:
        # Calculate spending in the budget period
        txs = Transaction.objects.filter(
            user=user,
            date__range=[b.start_date, b.end_date],
            transaction_type='Expense'
        )
        if b.category:
            txs = txs.filter(category=b.category)
        
        # Aggregate total spending in USD (for simplicity we can convert using rates)
        total_spent = Decimal('0.00')
        for t in txs:
            # simple exchange rate division to get value in USD/base
            # If t.currency code matches user base, else convert
            # For simplicity, we convert to USD base
            rate = t.currency.exchange_rate_to_usd if t.currency else Decimal('1.0')
            usd_amt = t.amount / rate
            total_spent += usd_amt

        # Exceed threshold check
        threshold_val = b.amount * (b.alert_threshold / Decimal('100.0'))
        if total_spent >= threshold_val and not b.is_alerted:
            Notification.objects.create(
                user=user,
                title=f"Budget Alert: {category.name if b.category else 'Overall'}",
                message=f"You have spent ${total_spent:.2f} of your ${b.amount:.2f} budget ({b.alert_threshold}% threshold reached).",
                notification_type='Budget Alert'
            )
            b.is_alerted = True
            b.save()


# ----------------- REST API VIEWSETS -----------------

class CurrencyViewSet(viewsets.ModelViewSet):
    queryset = Currency.objects.all()
    serializer_class = CurrencySerializer
    permission_classes = [permissions.IsAuthenticated]

class PaymentMethodViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentMethodSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return PaymentMethod.objects.filter(Q(user=self.request.user) | Q(user=None))

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Category.objects.filter(Q(user=self.request.user) | Q(user=None))

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user).order_by('-date')

    @action(detail=False, methods=['post'], url_path='bulk-delete')
    def bulk_delete(self, request):
        ids = request.data.get('ids', [])
        if not ids:
            return Response({'error': 'No ids provided.'}, status=status.HTTP_400_BAD_REQUEST)
        
        deleted, _ = Transaction.objects.filter(user=request.user, id__in=ids).delete()
        return Response({'deleted_count': deleted}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='export')
    def export_data(self, request):
        # CSV Export
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="transactions_{timezone.now().strftime("%Y%m%d")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['ID', 'Title', 'Amount', 'Type', 'Date', 'Category', 'Payment Method', 'Currency', 'Tags', 'Location'])
        
        txs = Transaction.objects.filter(user=request.user).select_related('category', 'payment_method', 'currency')
        for t in txs:
            writer.writerow([
                t.id, t.title, t.amount, t.transaction_type, t.date,
                t.category.name,
                t.payment_method.name if t.payment_method else '',
                t.currency.code if t.currency else '',
                t.tags or '',
                t.location or ''
            ])
        return response

    @action(detail=False, methods=['post'], url_path='import')
    def import_data(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'No file uploaded.'}, status=status.HTTP_400_BAD_REQUEST)

        # Parse CSV
        try:
            decoded_file = file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded_file)
            imported_count = 0
            
            # Default payment method and currency
            default_pm = PaymentMethod.objects.filter(Q(user=request.user) | Q(user=None)).first()
            default_cur = Currency.objects.filter(code='USD').first() or Currency.objects.first()

            for row in reader:
                title = row.get('Title', 'Imported Transaction')
                amount = Decimal(row.get('Amount', '0.00'))
                tx_type = row.get('Type', 'Expense')
                date_str = row.get('Date')
                date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else datetime.date.today()
                
                cat_name = row.get('Category', 'Others')
                # Find or create Category
                cat, _ = Category.objects.get_or_create(
                    user=request.user, name=cat_name,
                    defaults={'color': '#6c757d', 'icon': 'bi-tags'}
                )

                Transaction.objects.create(
                    user=request.user,
                    title=title,
                    amount=amount,
                    transaction_type=tx_type,
                    date=date,
                    category=cat,
                    payment_method=default_pm,
                    currency=default_cur,
                    tags=row.get('Tags', ''),
                    location=row.get('Location', '')
                )
                imported_count += 1

            return Response({'status': f'Successfully imported {imported_count} transactions.'}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': f'Failed to parse file: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

class BillViewSet(viewsets.ModelViewSet):
    serializer_class = BillSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Bill.objects.filter(user=self.request.user)
