# offers/serializers_peekaboo.py
# Serializers for Peekaboo deals

from rest_framework import serializers
from django.utils import timezone

try:
    from offers.models_peekaboo import PeekabooDeal, PeekabooCategory, PeekabooEntity
    from cards.serializers import BankSerializer, CreditCardSerializer
except ImportError:
    PeekabooDeal = None
    PeekabooCategory = None
    PeekabooEntity = None
    BankSerializer = None
    CreditCardSerializer = None

class PeekabooCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PeekabooCategory if PeekabooCategory else None
        fields = ['id', 'category_id', 'name', 'slug', 'description', 'icon', 'is_active', 'display_order']
        read_only_fields = ['id']

class PeekabooEntitySerializer(serializers.ModelSerializer):
    """Serializer for Peekaboo entities/merchants"""
    class Meta:
        model = PeekabooEntity if PeekabooEntity else None
        fields = ['id', 'source_entity_id', 'name', 'description', 'logo', 'keywords', 'categories', 'is_active']
        read_only_fields = ['id']

class PeekabooDealSerializer(serializers.ModelSerializer):
    bank = serializers.SerializerMethodField()
    linked_cards = serializers.SerializerMethodField()
    target_entity = serializers.SerializerMethodField()
    target_entity_id = serializers.SerializerMethodField()  # Return raw_entity_id for API compatibility
    source_entity = serializers.SerializerMethodField()  # Bank info from API
    is_currently_valid = serializers.SerializerMethodField()
    days_remaining = serializers.SerializerMethodField()
    hours_remaining = serializers.SerializerMethodField()
    
    class Meta:
        model = PeekabooDeal if PeekabooDeal else None
        fields = [
            'id', 'deal_id', 'title', 'description', 'percentage_value', 'discount_amount',
            'target_entity', 'target_entity_id', 'target_entity_name', 'target_entity_logo',
            'start_date', 'end_date', 'is_redeemable', 'redeemable_count', 'redeemed_count',
            'image', 'keywords', 'target_branches', 'order_type', 'powered_by',
            'expires_in', 'category', 'city', 'bank', 'linked_cards', 'associations',
            'source_entity_id', 'source_entity_name', 'source_entity_logo', 'source_entity',
            'is_active', 'is_expired', 'is_currently_valid',
            'days_remaining', 'hours_remaining',
            'created_at', 'updated_at', 'last_scraped_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_scraped_at']
    
    def get_target_entity_id(self, obj):
        """Return raw_entity_id for API compatibility"""
        return obj.raw_entity_id if obj else None
    
    def get_target_entity(self, obj):
        """Return entity details if linked"""
        if obj and obj.target_entity:
            return PeekabooEntitySerializer(obj.target_entity).data
        return None
    
    def get_bank(self, obj):
        if not obj or not obj.bank:
            return None
        try:
            if BankSerializer:
                return BankSerializer(obj.bank).data
            else:
                return {
                    'id': obj.bank.id,
                    'name': obj.bank.name,
                    'logo': obj.bank.logo.url if obj.bank.logo else None
                }
        except Exception:
            return None
    
    def get_linked_cards(self, obj):
        """Return linked cards details"""
        if not obj:
            return []
        try:
            if CreditCardSerializer and obj.linked_cards.exists():
                return [CreditCardSerializer(card).data for card in obj.linked_cards.all()]
            elif obj.linked_cards.exists():
                return [{
                    'id': card.id,
                    'name': card.name,
                    'bank': card.bank.name if card.bank else None,
                    'card_type': card.card_type
                } for card in obj.linked_cards.all()]
        except Exception:
            pass
        return []
    
    def get_source_entity(self, obj):
        """Return source entity (bank) info from API"""
        if not obj:
            return None
        return {
            'id': obj.source_entity_id,
            'name': obj.source_entity_name,
            'logo': obj.source_entity_logo
        } if obj.source_entity_name else None
    
    def get_is_currently_valid(self, obj):
        if not obj:
            return False
        now = timezone.now()
        return obj.start_date <= now <= obj.end_date and not obj.is_expired
    
    def get_days_remaining(self, obj):
        if not obj or not obj.end_date:
            return None
        now = timezone.now()
        if obj.end_date < now:
            return 0
        delta = obj.end_date - now
        return delta.days
    
    def get_hours_remaining(self, obj):
        if not obj or not obj.end_date:
            return None
        now = timezone.now()
        if obj.end_date < now:
            return 0
        delta = obj.end_date - now
        return int(delta.total_seconds() / 3600)

