# planning/serializers.py
from rest_framework import serializers
from .models import ScheduledPurchase
from cards.serializers import CreditCardSerializer


class ScheduledPurchaseSerializer(serializers.ModelSerializer):
    recommended_card_detail = CreditCardSerializer(source='recommended_card', read_only=True)
    
    class Meta:
        model = ScheduledPurchase
        fields = [
            'id', 'purchase_type', 'scheduled_date', 'estimated_amount',
            'location', 'merchant_preference', 'notes', 'recommended_card',
            'recommended_card_detail', 'recommended_merchants', 'active_offers',
            'status', 'reminder_sent', 'created_at', 'updated_at', 'completed_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'completed_at']


class ScheduledPurchaseCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduledPurchase
        fields = [
            'purchase_type', 'scheduled_date', 'estimated_amount',
            'location', 'merchant_preference', 'notes'
        ]

