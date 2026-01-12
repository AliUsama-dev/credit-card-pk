# offers/serializers_bank_specific.py
# Serializers for bank-specific deals

from rest_framework import serializers

try:
    from offers.models_bank_specific import (
        BankSpecificCity, BankSpecificCategory,
        BankSpecificEntity, BankSpecificCardAssociation
    )
    from cards.serializers import BankSerializer, CreditCardSerializer
except ImportError:
    BankSpecificCity = None
    BankSpecificCategory = None
    BankSpecificEntity = None
    BankSpecificCardAssociation = None
    BankSerializer = None
    CreditCardSerializer = None

class BankSpecificCitySerializer(serializers.ModelSerializer):
    bank = serializers.SerializerMethodField()
    
    class Meta:
        model = BankSpecificCity if BankSpecificCity else None
        fields = [
            'id', 'bank', 'city_id', 'name', 'slug', 'country',
            'latitude', 'longitude', 'image', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_bank(self, obj):
        if obj and obj.bank and BankSerializer:
            return BankSerializer(obj.bank).data
        return {'id': obj.bank.id, 'name': obj.bank.name} if obj and obj.bank else None

class BankSpecificCategorySerializer(serializers.ModelSerializer):
    bank = serializers.SerializerMethodField()
    
    class Meta:
        model = BankSpecificCategory if BankSpecificCategory else None
        fields = [
            'id', 'bank', 'category_id', 'name', 'order',
            'category_logo_url', 'image', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_bank(self, obj):
        if obj and obj.bank and BankSerializer:
            return BankSerializer(obj.bank).data
        return {'id': obj.bank.id, 'name': obj.bank.name} if obj and obj.bank else None

class BankSpecificEntitySerializer(serializers.ModelSerializer):
    bank = serializers.SerializerMethodField()
    
    class Meta:
        model = BankSpecificEntity if BankSpecificEntity else None
        fields = [
            'id', 'bank', 'entity_id', 'name', 'slug', 'description',
            'package', 'contact_number', 'keywords', 'entity_rating',
            'cover', 'logo', 'gallery', 'menu',
            'facebook', 'instagram', 'website', 'email', 'whatsapp', 'android', 'ios',
            'total_branches', 'total_open_branches', 'total_associated_deals',
            'max_discount', 'wishlist_count', 'review_counts', 'tags',
            'nearest_branch_id', 'nearest_branch_name', 'nearest_branch_lat_long',
            'nearest_branch_distance', 'nearest_branch_open_now',
            'nearest_branch_contact_number', 'branches',
            'is_active', 'online_service_available',
            'created_at', 'updated_at', 'last_scraped_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_scraped_at']
    
    def get_bank(self, obj):
        if obj and obj.bank and BankSerializer:
            return BankSerializer(obj.bank).data
        return {'id': obj.bank.id, 'name': obj.bank.name} if obj and obj.bank else None

class BankSpecificCardAssociationSerializer(serializers.ModelSerializer):
    bank = serializers.SerializerMethodField()
    linked_card = serializers.SerializerMethodField()
    
    class Meta:
        model = BankSpecificCardAssociation if BankSpecificCardAssociation else None
        fields = [
            'id', 'bank', 'association_id', 'type_id', 'type_name',
            'card_type', 'image', 'description', 'additional_info',
            'amenities', 'amenity_count', 'deal_count', 'linked_card',
            'is_active', 'created_at', 'updated_at', 'last_scraped_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_scraped_at']
    
    def get_bank(self, obj):
        if obj and obj.bank and BankSerializer:
            return BankSerializer(obj.bank).data
        return {'id': obj.bank.id, 'name': obj.bank.name} if obj and obj.bank else None
    
    def get_linked_card(self, obj):
        if obj and obj.linked_card and CreditCardSerializer:
            return CreditCardSerializer(obj.linked_card).data
        return None

