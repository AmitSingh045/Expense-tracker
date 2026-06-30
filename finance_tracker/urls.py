"""
URL configuration for finance_tracker project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.db.models import Sum
from decimal import Decimal
import datetime

# Dynamically patch Django Admin Index to pass statistics context variables
original_index = admin.site.index

def custom_admin_index(request, extra_context=None):
    if extra_context is None:
        extra_context = {}
        
    # Lazy imports to avoid import loops
    from accounts.models import User
    from transactions.models import Transaction, Bill
    from budgets.models import Budget
    from goals.models import Goal
    
    today = datetime.date.today()
    start_of_month = today.replace(day=1)
    
    # 1. Total and Active Users
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    
    # 2. Total and Today's Transactions count
    total_transactions = Transaction.objects.count()
    today_transactions = Transaction.objects.filter(date=today).count()
    
    # 3. Monthly Income vs Expenses (converted to USD)
    monthly_incomes = Transaction.objects.filter(date__gte=start_of_month, transaction_type='Income')
    monthly_expenses = Transaction.objects.filter(date__gte=start_of_month, transaction_type='Expense')
    
    m_inc = sum(t.amount / (t.currency.exchange_rate_to_usd if t.currency else Decimal('1.0')) for t in monthly_incomes)
    m_exp = sum(t.amount / (t.currency.exchange_rate_to_usd if t.currency else Decimal('1.0')) for t in monthly_expenses)
    
    # 4. Goal Savings
    total_savings = Goal.objects.aggregate(total=Sum('current_amount'))['total'] or Decimal('0.00')
    
    # 5. Goal Completion Rate
    total_goals = Goal.objects.count()
    completed_goals = 0
    for g in Goal.objects.all():
        if g.is_completed:
            completed_goals += 1
            
    goal_completion_rate = 0.0
    if total_goals > 0:
        goal_completion_rate = round((completed_goals / total_goals) * 100, 1)
        
    # 6. Active Budgets & Pending Bills
    active_budgets = Budget.objects.count()
    pending_bills = Bill.objects.filter(paid=False).count()
    
    extra_context.update({
        'total_users': total_users,
        'active_users': active_users,
        'total_transactions': total_transactions,
        'today_transactions': today_transactions,
        'monthly_income': m_inc,
        'monthly_expense': m_exp,
        'total_savings': total_savings,
        'active_budgets': active_budgets,
        'pending_bills': pending_bills,
        'goal_completion_rate': goal_completion_rate,
    })
    
    return original_index(request, extra_context=extra_context)

admin.site.index = custom_admin_index

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('', include('transactions.urls')),
    path('', include('budgets.urls')),
    path('', include('goals.urls')),
    path('', include('notifications.urls')),
    path('', include('reports.urls')),
    path('', include('analytics.urls')), # root dashboard
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

