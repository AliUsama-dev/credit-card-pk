# offers/serializers_partners.py
# Serializers for Partners Offers

from rest_framework import serializers
from django.utils import timezone

try:
    from offers.models_partners import PartnerBank, PartnerCard, PartnerOffer
    from cards.serializers import BankSerializer, CreditCardSerializer
except ImportError:
    PartnerBank = None
    PartnerCard = None
    PartnerOffer = None
    BankSerializer = None
    CreditCardSerializer = None

class PartnerCardSerializer(serializers.ModelSerializer):
    credit_card = CreditCardSerializer(read_only=True) if CreditCardSerializer else serializers.SerializerMethodField()
    partner_bank = serializers.SerializerMethodField()
    
    class Meta:
        model = PartnerCard if PartnerCard else None
        fields = [
            'id', 'name', 'slug', 'description', 'image', 'card_type',
            'credit_card', 'partner_bank', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_credit_card(self, obj):
        if hasattr(obj, 'credit_card') and obj.credit_card:
            return CreditCardSerializer(obj.credit_card).data if CreditCardSerializer else None
        return None
    
    def get_partner_bank(self, obj):
        if hasattr(obj, 'partner_bank') and obj.partner_bank:
            # Return basic bank info to avoid circular reference
            return {
                'id': obj.partner_bank.id,
                'name': obj.partner_bank.name,
                'peekaboo_slug': obj.partner_bank.peekaboo_slug,
                'logo': obj.partner_bank.logo,
                'bank': BankSerializer(obj.partner_bank.bank).data if obj.partner_bank.bank and BankSerializer else None,
            }
        return None

class PartnerBankSerializer(serializers.ModelSerializer):
    bank = BankSerializer(read_only=True) if BankSerializer else serializers.SerializerMethodField()
    cards_count = serializers.SerializerMethodField()
    offers_count = serializers.SerializerMethodField()
    
    class Meta:
        model = PartnerBank if PartnerBank else None
        fields = [
            'id', 'peekaboo_entity_id', 'peekaboo_slug', 'name', 'description',
            'logo', 'website', 'bank', 'cards_count', 'offers_count',
            'is_active', 'created_at', 'updated_at', 'last_scraped_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_scraped_at']
    
    def get_bank(self, obj):
        if hasattr(obj, 'bank') and obj.bank:
            return BankSerializer(obj.bank).data if BankSerializer else None
        return None
    
    def get_cards_count(self, obj):
        return obj.cards.filter(is_active=True).count() if hasattr(obj, 'cards') else 0
    
    def get_offers_count(self, obj):
        return obj.offers.filter(is_active=True, is_expired=False).count() if hasattr(obj, 'offers') else 0

class PartnerOfferSerializer(serializers.ModelSerializer):
    partner_bank = PartnerBankSerializer(read_only=True)
    partner_card = PartnerCardSerializer(read_only=True)
    is_currently_valid = serializers.SerializerMethodField()
    days_remaining = serializers.SerializerMethodField()
    source_url = serializers.SerializerMethodField()  # Make it a method field to regenerate URL
    
    class Meta:
        model = PartnerOffer if PartnerOffer else None
        fields = [
            'id', 'title', 'description', 'discount_percentage', 'discount_amount',
            'min_spend', 'max_discount', 'merchant_name', 'merchant_logo',
            'valid_from', 'valid_to', 'city', 'category', 'image',
            'terms_conditions', 'source_url', 'partner_bank', 'partner_card',
            'is_active', 'is_expired', 'is_currently_valid', 'days_remaining',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_is_currently_valid(self, obj):
        if not obj.valid_to:
            return True
        return timezone.now() <= obj.valid_to
    
    def get_days_remaining(self, obj):
        if not obj.valid_to:
            return None
        delta = obj.valid_to - timezone.now()
        if delta.total_seconds() < 0:
            return 0
        return delta.days
    
    def get_source_url(self, obj):
        """
        Regenerate source_url with the correct card slug from partner_card.
        This ensures URLs always use the card slug from the linked card, not the scraping context.
        """
        # Get the request context to check if credit_card_id was provided
        request = self.context.get('request')
        if not request:
            # Fallback to stored source_url if no request context
            return obj.source_url
        
        # Check if this is a credit_card_id filtered request
        credit_card_id = request.query_params.get('credit_card_id')
        if not credit_card_id:
            # Not a filtered request, return stored URL
            return obj.source_url
        
        # Get the partner_card and its linked credit_card
        partner_card = obj.partner_card
        if not partner_card:
            return obj.source_url
        
        credit_card = partner_card.credit_card
        if not credit_card:
            return obj.source_url
        
        # Only regenerate URL if the credit_card matches the requested one
        try:
            if int(credit_card_id) != credit_card.id:
                return obj.source_url
        except (ValueError, TypeError):
            return obj.source_url
        
        # Regenerate URL with correct card slug
        try:
            from scraping.tasks_peekaboo import BANK_PEEKABOO_IDS, BANK_SLUG_MAP
            
            bank = credit_card.bank
            if not bank:
                return obj.source_url
            
            bank_code = bank.code.upper()
            bank_info = BANK_PEEKABOO_IDS.get(bank_code, {})
            source_entity_id = bank_info.get('sourceEntityId')
            entity_id = bank_info.get('entityId')
            bank_slug = BANK_SLUG_MAP.get(bank_code, bank.name.lower().replace(' ', '-'))
            
            # Get card slug and associationTypeId
            card_slug = credit_card.peekaboo_card_slug or credit_card.name.lower().replace(' ', '-').replace('card', '').replace('debit', '').replace('credit', '').strip('-')
            association_type_id = credit_card.peekaboo_association_type_id
            
            # Try to get association ID from partner_card or deal associations
            # For now, use association_type_id as ai (we can improve this later)
            ai = association_type_id
            
            # Extract dealId from existing source_url if available
            deal_id = None
            if obj.source_url and 'dealId=' in obj.source_url:
                try:
                    deal_id = obj.source_url.split('dealId=')[1].split('&')[0].split('#')[0]
                except:
                    pass
            
            # Build URL parameters
            city_lower = (obj.city or 'karachi').lower()
            url_params = {
                'ai': str(ai) if ai else '',
                'associationTypeId': str(association_type_id) if association_type_id else '',
                'card': card_slug,
                'discounts': bank_slug,
                'ei': str(entity_id) if entity_id else '',
                'selfDeal': 'true',
                'sourceEntityId': str(source_entity_id) if source_entity_id else '',
            }
            
            if deal_id:
                url_params['dealId'] = deal_id
            
            # Build full URL
            base_url = 'https://peekaboo.guru'
            url_path = f"/{city_lower}/places/_all/all"
            query_string = '&'.join([f"{k}={v}" for k, v in url_params.items() if v])
            
            if query_string:
                return f"{base_url}{url_path}?{query_string}"
            else:
                return obj.source_url
                
        except Exception as e:
            # If URL generation fails, return stored URL
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"Failed to regenerate URL for offer {obj.id}: {str(e)}")
            return obj.source_url