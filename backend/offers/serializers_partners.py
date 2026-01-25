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
        Regenerate source_url with the correct card slug based on the selected card.
        When filtering by credit_card_id, find the matching PartnerCard from available_on_cards
        and use its information to generate the URL with the correct card slug.
        """
        import logging
        logger = logging.getLogger(__name__)
        
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
        
        logger.debug(f"🔗 Regenerating URL for offer {obj.id}, credit_card_id={credit_card_id}")
        
        try:
            credit_card_id_int = int(credit_card_id)
        except (ValueError, TypeError):
            return obj.source_url
        
        # Find the PartnerCard that matches the selected CreditCard
        # This is important because offers can be in available_on_cards for multiple cards
        # CRITICAL: We must find the EXACT PartnerCard that matches the selected CreditCard
        matching_partner_card = None
        
        # Get the CreditCard to ensure we match correctly
        try:
            from cards.models import CreditCard
            selected_credit_card = CreditCard.objects.get(id=credit_card_id_int)
        except CreditCard.DoesNotExist:
            return obj.source_url
        
        # First, try to find from available_on_cards (most accurate)
        # Prefetch available_on_cards to avoid N+1 queries
        try:
            if hasattr(obj, 'available_on_cards'):
                # Get all PartnerCards in available_on_cards that match the selected CreditCard
                # IMPORTANT: Filter by both credit_card_id AND partner_bank to ensure exact match
                matching_cards = obj.available_on_cards.filter(
                    credit_card_id=credit_card_id_int,
                    is_active=True,
                    partner_bank=obj.partner_bank  # Ensure same bank
                )
                if matching_cards.exists():
                    # CRITICAL: If multiple cards match, find the one that matches the selected card's name
                    # This ensures we get "CashBack" not "World" when user selected "CashBack"
                    card_name_lower = selected_credit_card.name.lower()
                    best_match = None
                    best_match_score = 0
                    
                    for card in matching_cards:
                        card_name_lower_card = card.name.lower()
                        score = 0
                        
                        # Exact name match = highest priority
                        if card_name_lower_card == card_name_lower:
                            score = 100
                        # Card name contains selected card name (e.g., "Mastercard CashBack" contains "CashBack")
                        elif card_name_lower in card_name_lower_card or card_name_lower_card in card_name_lower:
                            score = 50
                        # Slug matches
                        elif card.slug and (card.slug.lower() in card_name_lower or card_name_lower in card.slug.lower()):
                            score = 30
                        # Key words match (e.g., both have "cashback")
                        elif 'cashback' in card_name_lower and 'cashback' in card_name_lower_card:
                            score = 20
                        elif 'world' in card_name_lower and 'world' in card_name_lower_card:
                            score = 20
                        
                        if score > best_match_score:
                            best_match_score = score
                            best_match = card
                    
                    # Use best match if found, otherwise use first one
                    matching_partner_card = best_match if best_match else matching_cards.first()
        except (AttributeError, Exception) as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"Error finding from available_on_cards: {str(e)}")
            pass
        
        # Fallback: if not found in available_on_cards, try partner_card
        if not matching_partner_card:
            partner_card = obj.partner_card
            if partner_card and partner_card.credit_card_id == credit_card_id_int:
                matching_partner_card = partner_card
        
        # If still no match, try to find any PartnerCard linked to this CreditCard with same bank
        if not matching_partner_card:
            try:
                from offers.models_partners import PartnerCard
                matching_partner_card = PartnerCard.objects.filter(
                    credit_card_id=credit_card_id_int,
                    partner_bank=obj.partner_bank,
                    is_active=True
                ).first()
            except Exception:
                pass
        
        # If we found a matching PartnerCard, use it to regenerate URL
        if matching_partner_card and matching_partner_card.credit_card:
            credit_card = matching_partner_card.credit_card
            logger.debug(f"   ✅ Found matching PartnerCard: '{matching_partner_card.name}' (slug: '{matching_partner_card.slug}') for CreditCard: '{credit_card.name}'")
        else:
            # No matching card found, return stored URL
            logger.warning(f"   ⚠️ No matching PartnerCard found for credit_card_id={credit_card_id_int}, offer_id={obj.id}. Using stored URL.")
            return obj.source_url
        
        # Regenerate URL with correct card slug from the selected card
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
            
            # Get card slug from the selected card
            # CRITICAL: Use PartnerCard slug first (most accurate), then CreditCard slug, then generate
            # But ALWAYS verify it matches the selected card name
            card_slug = matching_partner_card.slug
            original_slug = card_slug  # Keep for comparison
            
            # Verify the slug matches the selected card before using it
            card_name_lower = credit_card.name.lower()
            key_words = ['cashback', 'world', 'platinum', 'gold', 'silver', 'classic', 'signature', 'elite', 'sapphire', 'titanium']
            card_key_word = None
            for word in key_words:
                if word in card_name_lower:
                    card_key_word = word
                    break
            
            # If PartnerCard slug doesn't match the selected card's key word, don't use it
            if card_slug and card_key_word:
                slug_lower = card_slug.lower()
                slug_has_key_word = any(word in slug_lower for word in key_words if word == card_key_word)
                if not slug_has_key_word:
                    # Slug doesn't match - don't use it, will regenerate
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"PartnerCard slug '{card_slug}' doesn't match card '{credit_card.name}' (key word: '{card_key_word}'). Will regenerate.")
                    card_slug = None
            
            if not card_slug:
                card_slug = credit_card.peekaboo_card_slug
                # Verify this one too
                if card_slug and card_key_word:
                    slug_lower = card_slug.lower()
                    if card_key_word not in slug_lower:
                        card_slug = None
            
            if not card_slug:
                # Generate slug from card name - be careful to preserve important words like "CashBack"
                card_slug = credit_card.name.lower()
                # Replace spaces with dashes
                card_slug = card_slug.replace(' ', '-')
                # Remove only standalone "card" word at the end, keep important words
                if card_slug.endswith('-card'):
                    card_slug = card_slug[:-5]  # Remove "-card" suffix
                elif card_slug.endswith(' card'):
                    card_slug = card_slug[:-5]  # Remove " card" suffix
                # Remove common suffixes that don't affect the card type
                for suffix in ['-credit', '-debit', ' credit', ' debit']:
                    if card_slug.endswith(suffix):
                        card_slug = card_slug[:-len(suffix)]
                card_slug = card_slug.strip('-')
                # Clean up multiple dashes
                while '--' in card_slug:
                    card_slug = card_slug.replace('--', '-')
            
            # IMPORTANT: Verify the slug matches the card name
            # For "Mastercard CashBack Credit Card", slug should be "mastercard-cashback-credit-card" or "mastercard-cashback"
            # NOT "mastercard-world-credit-card"
            card_name_lower = credit_card.name.lower()
            
            # Check for key distinguishing words
            key_words = ['cashback', 'world', 'platinum', 'gold', 'silver', 'classic', 'signature', 'elite']
            card_has_word = None
            slug_has_word = None
            
            for word in key_words:
                if word in card_name_lower:
                    card_has_word = word
                    break
            
            for word in key_words:
                if word in card_slug.lower():
                    slug_has_word = word
                    break
            
            # If card has a key word but slug doesn't match, regenerate
            if card_has_word and card_has_word != slug_has_word:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Card slug mismatch: card='{credit_card.name}' (has '{card_has_word}'), slug='{card_slug}' (has '{slug_has_word}'). Regenerating...")
                # Regenerate with proper handling - preserve key words
                card_slug = card_name_lower.replace(' ', '-')
                # Remove only standalone "card" word, keep important words
                card_slug = card_slug.replace('-card', '').replace(' card', '')
                # Remove common suffixes
                for suffix in [' credit', ' debit', 'credit', 'debit']:
                    if card_slug.endswith(suffix):
                        card_slug = card_slug[:-len(suffix)]
                while '--' in card_slug:
                    card_slug = card_slug.replace('--', '-')
                card_slug = card_slug.strip('-')
                logger.info(f"Regenerated slug: '{card_slug}' for card '{credit_card.name}'")
            
            # Get associationTypeId from PartnerCard or CreditCard
            association_type_id = matching_partner_card.peekaboo_association_type_id
            if not association_type_id:
                association_type_id = credit_card.peekaboo_association_type_id
            
            # Get association ID (ai parameter)
            ai = matching_partner_card.peekaboo_association_id
            if not ai:
                ai = association_type_id  # Fallback to association_type_id
            
            # Extract dealId from existing source_url if available
            deal_id = None
            if obj.source_url and 'dealId=' in obj.source_url:
                try:
                    import re
                    match = re.search(r'dealId=([^&]+)', obj.source_url)
                    if match:
                        deal_id = match.group(1).strip()
                except Exception:
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
                new_url = f"{base_url}{url_path}?{query_string}"
                # Extract card param from old and new URLs for comparison
                old_card_param = 'N/A'
                if obj.source_url and 'card=' in obj.source_url:
                    try:
                        old_card_param = obj.source_url.split('card=')[1].split('&')[0]
                    except:
                        pass
                logger.debug(f"   ✅ Regenerated URL: card_slug='{card_slug}'")
                logger.debug(f"   📎 Old URL card param: {old_card_param}")
                logger.debug(f"   📎 New URL card param: {card_slug}")
                return new_url
            else:
                logger.warning(f"   ⚠️ Could not build query string for offer {obj.id}")
                return obj.source_url
                
        except Exception as e:
            # If URL generation fails, return stored URL
            logger.error(f"   ❌ Failed to regenerate URL for offer {obj.id}: {str(e)}", exc_info=True)
            return obj.source_url