from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from rest_framework import viewsets, permissions
from .models import Goal
from .serializers import GoalSerializer
from decimal import Decimal

# ----------------- HTML VIEWS -----------------

@login_required
def goals_list_view(request):
    user = request.user
    goals = Goal.objects.filter(user=user)

    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_goal':
            name = request.POST.get('name')
            g_type = request.POST.get('goal_type', 'Savings')
            target = Decimal(request.POST.get('target_amount'))
            current = Decimal(request.POST.get('current_amount', '0.00'))
            t_date = request.POST.get('target_date')

            Goal.objects.create(
                user=user, name=name, goal_type=g_type,
                target_amount=target, current_amount=current, target_date=t_date
            )
            messages.success(request, f"Savings goal '{name}' set successfully.")
            return redirect('goals_list')

        elif action == 'add_funds':
            g_id = request.POST.get('goal_id')
            amount = Decimal(request.POST.get('amount'))
            goal = get_object_or_404(Goal, id=g_id, user=user)
            
            goal.current_amount += amount
            goal.save()
            
            # Check if this completed the goal
            if goal.is_completed:
                from notifications.models import Notification
                Notification.objects.get_or_create(
                    user=user,
                    title=f"Goal Completed: {goal.name}!",
                    message=f"Fantastic job! You've achieved your savings goal of ${goal.target_amount} for '{goal.name}'!",
                    notification_type='Goal Completed'
                )
                messages.success(request, f"Congratulations! You completed the goal '{goal.name}'!")
            else:
                messages.success(request, f"Added ${amount} to '{goal.name}'.")
            return redirect('goals_list')

        elif action == 'delete_goal':
            g_id = request.POST.get('goal_id')
            goal = get_object_or_404(Goal, id=g_id, user=user)
            goal.delete()
            messages.success(request, "Goal deleted successfully.")
            return redirect('goals_list')

    return render(request, 'goals/goals.html', {
        'goals': goals,
        'goal_types': Goal.GOAL_TYPES
    })


# ----------------- REST API VIEWS -----------------

class GoalViewSet(viewsets.ModelViewSet):
    serializer_class = GoalSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Goal.objects.filter(user=self.request.user)
