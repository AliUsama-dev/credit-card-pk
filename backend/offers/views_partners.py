# offers/views_partners.py
# API views for Partners Offers

from rest_framework import generics, permissions, status, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.utils import timezone

import logging
logger = logging.getLogger(__name__)

try:
    from offers.models_partners import PartnerBank, PartnerCard, PartnerOffer
    from offers.serializers_partners import PartnerBankSerializer, PartnerCardSerializer, PartnerOfferSerializer
except ImportError:
    PartnerBank = None
    PartnerCard = None
    PartnerOffer = None
    PartnerBankSerializer = None
    PartnerCardSerializer = None
    PartnerOfferSerializer = None

class PartnerBankListView(generics.ListAPIView):
    """List all partner banks"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PartnerBankSerializer if PartnerBankSerializer else None
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'description']
    
    def get_queryset(self):
        if not PartnerBank:
            return []
        return PartnerBank.objects.all().order_by('name')

class PartnerCardListView(generics.ListAPIView):
    """List cards for a partner bank"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PartnerCardSerializer if PartnerCardSerializer else None
    
    def get_queryset(self):
        if not PartnerCard:
            return []
        partner_bank_id = self.request.query_params.get('partner_bank_id')
        queryset = PartnerCard.objects.filter(is_active=True)
        
        if partner_bank_id:
            queryset = queryset.filter(partner_bank_id=partner_bank_id)
        
        return queryset.order_by('name')

class PartnerOfferListView(generics.ListAPIView):
    """List partner offers with filtering"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PartnerOfferSerializer if PartnerOfferSerializer else None
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    # NOTE: 'city' is NOT in filterset_fields because we handle it manually in get_queryset()
    # This allows us to return offers from all cities when requested city has none (better UX)
    filterset_fields = ['partner_bank', 'partner_card', 'category', 'is_active', 'is_expired']
    search_fields = ['title', 'description', 'merchant_name']
    ordering_fields = ['valid_to', 'created_at', 'discount_percentage']
    ordering = ['-valid_to', '-created_at']
    
    def get_serializer_context(self):
        """Pass request context to serializer for URL regeneration"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def get_queryset(self):
        if not PartnerOffer:
            return []
        
        queryset = PartnerOffer.objects.filter(is_active=True)

        # Optional filter: show offers for a specific real CreditCard (used for "My Cards" flow)
        credit_card_id = self.request.query_params.get('credit_card_id')
        if credit_card_id:
            try:
                credit_card_id_int = int(credit_card_id)
                from cards.models import CreditCard
                
                # Try to get the CreditCard to match by name if direct link doesn't work
                try:
                    credit_card = CreditCard.objects.get(id=credit_card_id_int)
                    logger.info(f"🔍 Finding Partners Offers for CreditCard ID={credit_card_id_int} ({credit_card.name}, Bank: {credit_card.bank.name if credit_card.bank else 'None'})")
                    
                    # ULTRA-STRICT FILTERING: Only show offers for the EXACT selected card AND bank
                    # First, get the card slug and bank slug for filtering
                    card_slug = credit_card.peekaboo_card_slug
                    if not card_slug:
                        # Generate slug from card name if not stored
                        card_slug = credit_card.name.lower().replace(' ', '-').replace(' card', '').replace('card', '').replace(' debit', '').replace('debit', '').replace(' credit', '').replace('credit', '').strip('-')
                        # Clean up multiple dashes
                        while '--' in card_slug:
                            card_slug = card_slug.replace('--', '-')
                    
                    # Get bank slug for filtering
                    bank_slug = None
                    if credit_card.bank:
                        from scraping.tasks_peekaboo import BANK_SLUG_MAP
                        bank_code = credit_card.bank.code.upper()
                        bank_slug = BANK_SLUG_MAP.get(bank_code, credit_card.bank.name.lower().replace(' ', '-'))
                    
                    # ULTRA-STRICT: ONLY show offers that meet ALL of these conditions:
                    # 1. Offer is linked to the selected card (partner_card__credit_card_id)
                    # 2. Offer's bank matches selected card's bank (partner_bank.bank)
                    # 3. Offer's source_url contains the exact card slug (card=mastercard-silver-debit-card)
                    # 4. Offer's source_url contains the exact bank slug (discounts=al-baraka-bank)
                    # This ensures 100% accuracy - no offers from other cards or banks
                    
                    # Start with offers linked to the selected card
                    queryset = queryset.filter(
                        partner_card__credit_card_id=credit_card_id_int
                    )
                    
                    # CRITICAL: Filter by bank to ensure we only get offers from the selected bank
                    if credit_card.bank:
                        from offers.models_partners import PartnerBank
                        partner_bank = PartnerBank.objects.filter(bank=credit_card.bank, is_active=True).first()
                        if partner_bank:
                            queryset = queryset.filter(partner_bank=partner_bank)
                        else:
                            # If no partner_bank found, return empty (can't match bank)
                            queryset = queryset.none()
                            logger.warning(f"   ⚠️ No PartnerBank found for bank '{credit_card.bank.name}', returning no offers")
                    
                    # CRITICAL: Filter by source_url to ensure it contains the EXACT card slug
                    # This is the KEY fix - only show offers where URL matches the selected card
                    if card_slug:
                        queryset = queryset.filter(
                            source_url__icontains=f'card={card_slug}'
                        )
                    else:
                        # If no card slug, return empty (can't verify card match)
                        queryset = queryset.none()
                        logger.warning(f"   ⚠️ No card slug found for card '{credit_card.name}', returning no offers")
                    
                    # CRITICAL: Also filter by bank slug in source_url for double verification
                    if bank_slug:
                        queryset = queryset.filter(
                            source_url__icontains=f'discounts={bank_slug}'
                        )
                    
                    # Auto-link PartnerCards if needed (for future queries)
                    if credit_card.bank:
                        from offers.models_partners import PartnerCard, PartnerBank
                        partner_bank = PartnerBank.objects.filter(bank=credit_card.bank, is_active=True).first()
                        if partner_bank and card_slug:
                            matching_partner_cards = PartnerCard.objects.filter(
                                partner_bank=partner_bank,
                                is_active=True,
                                slug__iexact=card_slug
                            ).exclude(credit_card=credit_card)
                            
                            if matching_partner_cards.exists():
                                linked_count = 0
                                for partner_card in matching_partner_cards:
                                    partner_card.credit_card = credit_card
                                    partner_card.save(update_fields=['credit_card'])
                                    linked_count += 1
                                    logger.info(f"   ✅ Auto-linked PartnerCard '{partner_card.name}' (slug: {partner_card.slug}) to CreditCard '{credit_card.name}'")
                                
                                if linked_count > 0:
                                    logger.info(f"   ✅ Auto-linked {linked_count} PartnerCard(s) to CreditCard for future queries")
                    
                    final_count = queryset.count()
                    logger.info(f"   🎯 FINAL filtered offers (card={card_slug}, bank={bank_slug}): {final_count}")
                    
                    # CRITICAL: Filter out offers without dealId in URL
                    # These are generic place listings that don't have actual deals
                    # Only show offers that have a specific dealId (actual deals)
                    # This ensures users only see offers that actually exist on Peekaboo
                    from django.db.models import Q
                    queryset_before_dealid = queryset
                    queryset = queryset.filter(
                        Q(source_url__icontains='dealId=') | Q(source_url__icontains='&dealId=')
                    )
                    offers_with_deal_id = queryset.count()
                    offers_without_dealid = final_count - offers_with_deal_id
                    if offers_without_dealid > 0:
                        logger.info(f"   ⚠️ Filtered out {offers_without_dealid} offers without dealId (generic listings)")
                    logger.info(f"   ✅ Offers with dealId in URL: {offers_with_deal_id} (filtered from {final_count})")
                    
                    # CRITICAL DEDUPLICATION: The same offer can be linked to multiple PartnerCard objects
                    # which are all linked to the same CreditCard, causing duplicates
                    # Solution: Deduplicate by extracting dealId from URL (most reliable)
                    import re
                    from django.db.models import Q
                    
                    # Get all offer IDs with their source URLs
                    all_offers = list(queryset.values('id', 'source_url', 'merchant_name', 'city', 'discount_percentage'))
                    
                    # Group offers by dealId (extracted from URL) or by merchant+city+discount as fallback
                    offers_by_key = {}
                    
                    for offer in all_offers:
                        source_url = offer.get('source_url') or ''
                        deal_id = None
                        
                        # Extract dealId from URL (most reliable identifier)
                        if 'dealId=' in source_url:
                            match = re.search(r'dealId=([^&]+)', source_url)
                            if match:
                                deal_id = match.group(1).strip()
                        
                        # Use dealId as key if available, otherwise use merchant+city+discount
                        if deal_id:
                            key = f"dealId:{deal_id}"
                        else:
                            # Fallback: use merchant + city + discount
                            key = (
                                (offer.get('merchant_name') or '').strip().lower(),
                                (offer.get('city') or '').strip().upper(),
                                str(offer.get('discount_percentage') or '').strip()
                            )
                            key = f"merchant:{key[0]}|city:{key[1]}|discount:{key[2]}"
                        
                        # Group by key, keep track of all offer IDs with this key
                        if key not in offers_by_key:
                            offers_by_key[key] = []
                        offers_by_key[key].append(offer['id'])
                    
                    # For each group, keep only the offer with the smallest ID (oldest/first created)
                    unique_offer_ids = []
                    for key, offer_ids in offers_by_key.items():
                        if offer_ids:
                            unique_offer_ids.append(min(offer_ids))
                    
                    # Filter queryset to only unique offers
                    queryset = queryset.filter(id__in=unique_offer_ids)
                    deduplicated_count = queryset.count()
                    duplicates_removed = offers_with_deal_id - deduplicated_count
                    if duplicates_removed > 0:
                        logger.info(f"   ⚠️ Removed {duplicates_removed} duplicate offers (same dealId or merchant+city+discount)")
                    logger.info(f"   ✅ Final deduplicated offers: {deduplicated_count} (from {offers_with_deal_id})")
                    
                    total_count_before_city = queryset.count()
                    logger.info(f"   🎯 TOTAL Partners Offers found (before city filter): {total_count_before_city}")
                    
                    # IMPORTANT: Apply city filter AFTER matching by card
                    # If city is specified but no offers found for that city, return offers from ANY city
                    # This ensures users see offers even if they selected wrong city
                    city_filter = self.request.query_params.get('city')
                    if city_filter and total_count_before_city > 0:
                        city_filter_upper = city_filter.upper()
                        offers_with_city = queryset.filter(city__iexact=city_filter_upper)
                        city_count = offers_with_city.count()
                        logger.info(f"   📍 Offers in {city_filter_upper}: {city_count}")
                        
                        if city_count > 0:
                            # We have offers for the requested city, use them
                            queryset = offers_with_city
                            logger.info(f"   ✅ Using offers from {city_filter_upper}")
                        else:
                            # No offers for requested city, but we have offers for this card
                            # Show offers from ANY city (better UX than showing nothing)
                            available_cities = list(set(queryset.values_list('city', flat=True).distinct()))
                            logger.info(f"   ⚠️ No offers in {city_filter_upper}, but {total_count_before_city} offers available in: {available_cities}")
                            logger.info(f"   ✅ Returning offers from all cities for better UX")
                            # Keep all offers (don't filter by city) - queryset already has all offers
                    
                    total_count_after = queryset.count()
                    logger.info(f"   🎯 Partners Offers count (after city logic): {total_count_after}")
                    
                except CreditCard.DoesNotExist:
                    logger.warning(f"   ⚠️ CreditCard ID {credit_card_id_int} does not exist")
                    # CreditCard doesn't exist, fall back to direct link only
                    queryset = queryset.filter(partner_card__credit_card_id=credit_card_id_int)
                    
            except (ValueError, TypeError) as e:
                logger.warning(f"   ⚠️ Invalid credit_card_id: {credit_card_id} ({str(e)})")
                pass
        
        # Apply city filter if not already applied (for non-credit_card_id queries)
        city_filter = self.request.query_params.get('city')
        if city_filter and not credit_card_id:
            queryset = queryset.filter(city__iexact=city_filter.upper())
        
        # Filter expired offers by default
        show_expired = self.request.query_params.get('show_expired', 'false').lower() == 'true'
        if not show_expired:
            queryset = queryset.filter(is_expired=False)
        
        return queryset

class ScrapePartnersBanksView(APIView):
    """Admin endpoint to scrape all partner banks"""
    permission_classes = [permissions.IsAdminUser]
    
    def post(self, request):
        city = request.data.get('city', 'karachi')
        
        try:
            from scraping.tasks_partners import scrape_partners_banks
            result = scrape_partners_banks(city)
            
            return Response({
                'status': 'success',
                'message': f'Scraped {result.get("total", 0)} partner banks',
                **result
            })
        except Exception as e:
            logger.error(f"Error scraping partner banks: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ScrapePartnerBankDetailView(APIView):
    """Admin endpoint to scrape detailed info for a partner bank"""
    permission_classes = [permissions.IsAdminUser]
    
    def post(self, request):
        partner_bank_id = request.data.get('partner_bank_id')
        city = request.data.get('city', 'karachi')
        
        if not partner_bank_id:
            return Response({
                'status': 'error',
                'error': 'partner_bank_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from scraping.tasks_partners import scrape_partner_bank_detail
            result = scrape_partner_bank_detail(partner_bank_id, city)
            
            if 'error' in result:
                return Response({
                    'status': 'error',
                    'error': result['error']
                }, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({
                'status': 'success',
                'message': f'Scraped {result.get("bank", "bank")} details',
                **result
            })
        except Exception as e:
            logger.error(f"Error scraping partner bank detail: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ScrapeAllPartnersBanksView(APIView):
    """Admin endpoint to scrape all partner banks and their details"""
    permission_classes = [permissions.IsAdminUser]
    
    def post(self, request):
        city = request.data.get('city', 'karachi')
        
        try:
            from scraping.tasks_partners import scrape_all_partners_banks
            result = scrape_all_partners_banks(city)
            
            return Response({
                'status': 'success',
                'message': f'Scraped {result.get("banks_scraped", 0)} partner banks',
                **result
            })
        except Exception as e:
            logger.error(f"Error scraping all partner banks: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
