# offers/serializers.py
from rest_framework import serializers
from .models import Offer, UserOffer, Merchant
from cards.serializers import BankSerializer, CreditCardSerializer

class MerchantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Merchant
        fields = '__all__'

class OfferSerializer(serializers.ModelSerializer):
    bank = BankSerializer(read_only=True, allow_null=True)
    card = CreditCardSerializer(read_only=True, allow_null=True)
    merchant = MerchantSerializer(read_only=True, allow_null=True)
    status = serializers.SerializerMethodField()
    days_remaining = serializers.SerializerMethodField()
    
    class Meta:
        model = Offer
        fields = [
            'id', 'title', 'description', 'offer_type', 'bank', 'card',
            'merchant', 'discount_percentage', 'cashback_amount',
            'min_spend', 'max_discount', 'valid_from', 'valid_to',
            'terms_conditions', 'is_active', 'status', 'days_remaining',
            'last_updated', 'created_at'
        ]
    
    def get_status(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                user_offer = UserOffer.objects.get(user=request.user, offer=obj)
                return user_offer.status
            except UserOffer.DoesNotExist:
                return 'AVAILABLE'
        return None
    
    def get_days_remaining(self, obj):
        from datetime import date
        if obj.valid_to:
            delta = obj.valid_to - date.today()
            return delta.days
        return None

class UserOfferSerializer(serializers.ModelSerializer):
    offer = OfferSerializer(read_only=True)
    
    class Meta:
        model = UserOffer
        fields = '__all__'
        read_only_fields = ('user', 'activated_at', 'used_at')