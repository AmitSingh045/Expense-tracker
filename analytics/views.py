from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Sum, Q
from transactions.models import Transaction, Category, Bill
from budgets.models import Budget
from goals.models import Goal
from decimal import Decimal
import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions

# ----------------- HTML VIEWS -----------------

@login_required
def dashboard_view(request):
    from transactions.models import Category, PaymentMethod, Currency
    from django.db.models import Q
    user = request.user

    # Provide context for the "New Transaction" modal dropdowns
    context = {
        'categories': Category.objects.filter(Q(user=user) | Q(user=None)),
        'payment_methods': PaymentMethod.objects.filter(Q(user=user) | Q(user=None)),
        'currencies': Currency.objects.all(),
    }
    return render(request, 'analytics/dashboard.html', context)


# ----------------- REST API VIEWS -----------------

class DashboardDataAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        today = datetime.date.today()
        start_of_month = today.replace(day=1)
        start_of_week = today - datetime.timedelta(days=today.weekday())
        start_of_year = today.replace(month=1, day=1)

        # Base querysets
        txs = Transaction.objects.filter(user=user)
        expenses = txs.filter(transaction_type='Expense')
        incomes = txs.filter(transaction_type='Income')

        # Helper to convert to USD
        def convert_to_usd(tx_list):
            total = Decimal('0.00')
            for t in tx_list:
                rate = t.currency.exchange_rate_to_usd if t.currency else Decimal('1.0')
                total += t.amount / rate
            return total

        # Calculations
        total_income = convert_to_usd(incomes)
        total_expense = convert_to_usd(expenses)
        balance = total_income - total_expense
        
        # Today, Week, Month Expense
        today_expense = convert_to_usd(expenses.filter(date=today))
        week_expense = convert_to_usd(expenses.filter(date__gte=start_of_week))
        month_expense = convert_to_usd(expenses.filter(date__gte=start_of_month))

        # Savings Ratio
        savings_ratio = 0.0
        if total_income > 0:
            savings_ratio = float(round(((total_income - total_expense) / total_income) * 100, 1))
            savings_ratio = max(0.0, savings_ratio)

        # Net Worth = Balance + Total Savings in Goals
        goals_saved = Goal.objects.filter(user=user).aggregate(total=Sum('current_amount'))['total'] or Decimal('0.00')
        net_worth = balance + goals_saved

        # 1. Category Chart (Donut)
        category_spending = {}
        for exp in expenses.filter(date__gte=start_of_month).select_related('category'):
            cat_name = exp.category.name
            rate = exp.currency.exchange_rate_to_usd if exp.currency else Decimal('1.0')
            usd_amt = exp.amount / rate
            category_spending[cat_name] = category_spending.get(cat_name, Decimal('0.00')) + usd_amt

        # 2. Monthly Trend Chart (Bar: Income vs Expense)
        # Get past 6 months
        monthly_trend = []
        for i in range(5, -1, -1):
            # Calculate months back
            first_day_of_target_month = (start_of_month - datetime.timedelta(days=i*30)).replace(day=1)
            # Find last day
            next_month = first_day_of_target_month.replace(day=28) + datetime.timedelta(days=4)
            last_day_of_target_month = next_month - datetime.timedelta(days=next_month.day)

            m_inc = convert_to_usd(incomes.filter(date__range=[first_day_of_target_month, last_day_of_target_month]))
            m_exp = convert_to_usd(expenses.filter(date__range=[first_day_of_target_month, last_day_of_target_month]))
            
            monthly_trend.append({
                'month': first_day_of_target_month.strftime('%b'),
                'income': float(m_inc),
                'expense': float(m_exp)
            })

        # 3. Weekly Trend Chart (Line: Day by Day)
        weekly_trend = {}
        for d in range(7):
            day_date = start_of_week + datetime.timedelta(days=d)
            day_exp = convert_to_usd(expenses.filter(date=day_date))
            weekly_trend[day_date.strftime('%a')] = float(day_exp)

        # 4. Financial Health Score
        # Max: 100 points
        # - Savings Ratio: max 40 points (40 points if ratio is 30%+)
        # - Budget Compliance: max 30 points (subtract 10 points per overspent budget)
        # - Emergency Fund: max 30 points (30 points if progress is 100%)
        health_score = 0
        
        # Savings Score
        health_score += min(int(savings_ratio * 1.33), 40)
        
        # Budget Score
        budgets = Budget.objects.filter(user=user)
        overspent_count = 0
        from budgets.views import get_budget_spent
        for b in budgets:
            if get_budget_spent(b) > b.amount:
                overspent_count += 1
        budget_score = max(30 - (overspent_count * 10), 0)
        health_score += budget_score

        # Emergency Fund Goal Score
        emergency_fund = Goal.objects.filter(user=user, goal_type='Emergency').first()
        if emergency_fund:
            health_score += int(float(emergency_fund.progress_percentage) * 0.3)
        else:
            health_score += 15 # default average points if they haven't set it up
        
        health_score = min(max(health_score, 10), 100)

        # 5. AI Suggestions (Heuristics Engine)
        ai_insights = []
        # Insight 1: Savings Ratio check
        if savings_ratio < 10:
            ai_insights.append({
                'title': 'Low Savings Rate',
                'message': 'Your savings rate is below 10%. Consider reducing non-essential expenses in discretionary categories like Entertainment or Shopping.',
                'type': 'warning'
            })
        elif savings_ratio >= 30:
            ai_insights.append({
                'title': 'Excellent Savings Rate!',
                'message': 'You are saving over 30% of your income. Consider allocating these savings to an investment goal or your emergency fund.',
                'type': 'success'
            })

        # Insight 2: Overspending detection
        top_category = None
        if category_spending:
            top_category = max(category_spending, key=category_spending.get)
            if category_spending[top_category] > Decimal('500.00'):
                ai_insights.append({
                    'title': f'High spending in {top_category}',
                    'message': f'{top_category} accounts for your highest spending this month (${category_spending[top_category]:.2f}). Can you find cheaper alternatives?',
                    'type': 'info'
                })

        # Insight 3: Linear Forecast
        # Simple forecast: average of last 3 months expense
        three_months_ago = start_of_month - datetime.timedelta(days=90)
        recent_expenses = convert_to_usd(expenses.filter(date__gte=three_months_ago))
        avg_monthly = recent_expenses / 3
        forecast_expense = avg_monthly * Decimal('1.05') # expect a 5% inflation/increase
        ai_insights.append({
            'title': 'Next Month Expense Forecast',
            'message': f'Based on your recent 3-month spending, we forecast your next month expenses to be around ${forecast_expense:.2f}.',
            'type': 'info'
        })

        # Recent Transactions
        recent_txs = txs.select_related('category', 'currency').order_by('-date', '-created_at')[:5]
        recent_txs_data = [{
            'title': t.title,
            'amount': float(t.amount),
            'type': t.transaction_type,
            'category': t.category.name,
            'category_color': t.category.color,
            'category_icon': t.category.icon,
            'currency': t.currency.code,
            'currency_symbol': t.currency.symbol,
            'date': t.date.strftime('%Y-%m-%d')
        } for t in recent_txs]

        upcoming_bills = Bill.objects.filter(user=user, paid=False).order_by('due_date')[:3]
        upcoming_bills_data = [{
            'name': b.name,
            'category': b.category,
            'amount': float(b.amount),
            'due_date': b.due_date.strftime('%Y-%m-%d'),
            'days_left': (b.due_date - today).days
        } for b in upcoming_bills]

        # Goals Progress
        user_goals = Goal.objects.filter(user=user)[:3]
        goals_data = [{
            'name': g.name,
            'target_amount': float(g.target_amount),
            'current_amount': float(g.current_amount),
            'percent': float(g.progress_percentage),
            'is_completed': g.is_completed
        } for g in user_goals]

        # JSON response payload
        return Response({
            'kpis': {
                'balance': float(balance),
                'income': float(total_income),
                'expense': float(total_expense),
                'savings_ratio': float(savings_ratio),
                'net_worth': float(net_worth),
                'today_expense': float(today_expense),
                'week_expense': float(week_expense),
                'month_expense': float(month_expense),
                'health_score': health_score
            },
            'category_pie': {
                'categories': list(category_spending.keys()),
                'amounts': [float(v) for v in category_spending.values()]
            },
            'monthly_trend': monthly_trend,
            'weekly_trend': weekly_trend,
            'ai_insights': ai_insights,
            'recent_transactions': recent_txs_data,
            'upcoming_bills': upcoming_bills_data,
            'goals': goals_data
        })
