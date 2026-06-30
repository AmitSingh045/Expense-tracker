from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from rest_framework import viewsets, permissions
from .models import Budget
from .serializers import BudgetSerializer
from transactions.models import Transaction, Category
from decimal import Decimal
import datetime

# Helper to calculate spending for a budget
def get_budget_spent(budget):
    txs = Transaction.objects.filter(
        user=budget.user,
        date__range=[budget.start_date, budget.end_date],
        transaction_type='Expense'
    )
    if budget.category:
        txs = txs.filter(category=budget.category)
    
    total = Decimal('0.00')
    for t in txs:
        rate = t.currency.exchange_rate_to_usd if t.currency else Decimal('1.0')
        usd_amt = t.amount / rate
        total += usd_amt
    return total

# ----------------- HTML VIEWS -----------------

@login_required
def budgets_list_view(request):
    user = request.user
    budgets = Budget.objects.filter(user=user)

    # Prepare budgets with current spent calculation
    enriched_budgets = []
    for b in budgets:
        spent = get_budget_spent(b)
        remaining = b.amount - spent
        percent = (spent / b.amount) * 100 if b.amount > 0 else 0
        enriched_budgets.append({
            'budget': b,
            'spent': spent,
            'remaining': max(remaining, Decimal('0.00')),
            'percent': min(round(percent, 1), 100.0),
            'overspent': spent > b.amount
        })

    # Form handling
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_budget':
            cat_id = request.POST.get('category')
            amount = Decimal(request.POST.get('amount'))
            period = request.POST.get('period', 'Monthly')
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            alert_threshold = Decimal(request.POST.get('alert_threshold', 90.0))

            cat_obj = Category.objects.get(id=cat_id) if cat_id else None

            Budget.objects.create(
                user=user, category=cat_obj, amount=amount, period=period,
                start_date=start_date, end_date=end_date, alert_threshold=alert_threshold
            )
            messages.success(request, "Budget created successfully.")
            return redirect('budgets_list')

        elif action == 'delete_budget':
            b_id = request.POST.get('budget_id')
            b = get_object_or_404(Budget, id=b_id, user=user)
            b.delete()
            messages.success(request, "Budget deleted successfully.")
            return redirect('budgets_list')

    categories = Category.objects.filter(Q(user=user) | Q(user=None))
    return render(request, 'budgets/budgets.html', {
        'budgets': enriched_budgets,
        'categories': categories
    })


# ----------------- REST API VIEWS -----------------

class BudgetViewSet(viewsets.ModelViewSet):
    serializer_class = BudgetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Budget.objects.filter(user=self.request.user)
