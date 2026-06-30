from rest_framework import serializers
from .models import Currency, PaymentMethod, Category, Transaction, Receipt, Bill

class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = ['id', 'code', 'symbol', 'exchange_rate_to_usd']

class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = ['id', 'name', 'icon']

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'color', 'icon']

class ReceiptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Receipt
        fields = ['id', 'file', 'uploaded_at', 'ocr_raw_text', 'ocr_parsed_json']
        read_only_fields = ['ocr_raw_text', 'ocr_parsed_json']

class TransactionSerializer(serializers.ModelSerializer):
    category_detail = CategorySerializer(source='category', read_only=True)
    payment_method_detail = PaymentMethodSerializer(source='payment_method', read_only=True)
    currency_detail = CurrencySerializer(source='currency', read_only=True)
    receipt = ReceiptSerializer(read_only=True)

    class Meta:
        model = Transaction
        fields = [
            'id', 'title', 'description', 'amount', 'transaction_type', 'date',
            'category', 'category_detail', 'payment_method', 'payment_method_detail',
            'currency', 'currency_detail', 'tags', 'location', 'is_recurring',
            'recurring_period', 'reminder', 'receipt', 'created_at', 'updated_at'
        ]

    def create(self, validated_data):
        # Assign current authenticated user
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class BillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bill
        fields = ['id', 'name', 'category', 'amount', 'due_date', 'paid', 'recurring', 'reminder_days_before']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
