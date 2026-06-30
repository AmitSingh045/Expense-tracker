from rest_framework import serializers
from .models import Goal

class GoalSerializer(serializers.ModelSerializer):
    progress_percentage = serializers.ReadOnlyField()
    is_completed = serializers.ReadOnlyField()

    class Meta:
        model = Goal
        fields = ['id', 'name', 'goal_type', 'target_amount', 'current_amount', 'target_date', 'progress_percentage', 'is_completed', 'completed_at']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
