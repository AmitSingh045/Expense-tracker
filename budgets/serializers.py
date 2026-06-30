from rest_framework import serializers
from .models import Budget
from transactions.serializers import CategorySerializer

class BudgetSerializer(serializers.ModelSerializer):
    category_detail = CategorySerializer(source='category', read_only=True)

    class Meta:
        model = Budget
        fields = ['id', 'category', 'category_detail', 'amount', 'period', 'start_date', 'end_date', 'alert_threshold', 'is_alerted']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
