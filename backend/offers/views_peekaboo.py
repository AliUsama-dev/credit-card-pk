# offers/views_peekaboo.py
# API views for Peekaboo deals

from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, timedelta
import logging
import threading

logger = logging.getLogger(__name__)

# In-memory cache to prevent concurrent scraping for the same card+bank+city
_scraping_cache = {}
_scraping_lock = threading.Lock()

try:
    from offers.models_peekaboo import PeekabooDeal, PeekabooCategory, PeekabooEntity
    from offers.serializers_peekaboo import PeekabooDealSerializer, PeekabooCategorySerializer, PeekabooEntitySerializer
    from cards.models import UserCard
except ImportError:
    PeekabooDeal = None
    PeekabooCategory = None
    PeekabooEntity = None
    PeekabooDealSerializer = None
    PeekabooCategorySerializer = None
    PeekabooEntitySerializer = None
    UserCard = None

class PeekabooDealListView(generics.ListAPIView):
    """List all Peekaboo deals with filtering"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if PeekabooDealSerializer:
            return PeekabooDealSerializer
        from rest_framework import serializers
        return serializers.Serializer
    
    def get_queryset(self):
        if not PeekabooDeal:
            return []
        
        queryset = PeekabooDeal.objects.all()
        
        # Filter by city
        city = self.request.query_params.get('city')
        if city:
            queryset = queryset.filter(city=city.upper())
        
        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__icontains=category)
        
        # Filter by bank
        bank_id = self.request.query_params.get('bank')
        if bank_id:
            queryset = queryset.filter(bank_id=bank_id)
        
        # Filter expired/active
        show_expired = self.request.query_params.get('show_expired', 'false').lower() == 'true'
        if not show_expired:
            queryset = queryset.filter(is_expired=False, is_active=True)
        
        # Search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(target_entity_name__icontains=search)
            )
        
        return queryset.order_by('-end_date', '-created_at')
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        
        # Pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class PeekabooDealForUserCardsView(generics.ListAPIView):
    """List Peekaboo deals filtered by user's cards"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if PeekabooDealSerializer:
            return PeekabooDealSerializer
        from rest_framework import serializers
        return serializers.Serializer
    
    def get_queryset(self):
        if not PeekabooDeal or not UserCard:
            return []
        
        # Get query parameters - card_id, bank_id are optional (if not provided, show ALL user cards)
        card_id = self.request.query_params.get('card_id')
        bank_id = self.request.query_params.get('bank_id')
        city = self.request.query_params.get('city')
        
        # Get ALL user's active cards
        all_user_cards = UserCard.objects.filter(
            user=self.request.user,
            is_active=True
        ).select_related('card', 'card__bank')
        
        # If card_id is provided, filter to that specific card
        if card_id:
            user_cards = all_user_cards.filter(card_id=card_id)
            if not user_cards.exists():
                logger.warning(f"User {self.request.user.id} - Card {card_id} not found in user's cards.")
                return []
            
            # Get the selected card
            user_card = user_cards.first()
            selected_card = user_card.card
            selected_bank = selected_card.bank if selected_card else None
            
            # Verify bank_id matches the card's bank (if provided)
            if bank_id and selected_bank:
                try:
                    bank_id_int = int(bank_id)
                    if selected_bank.id != bank_id_int:
                        logger.warning(f"User {self.request.user.id} - Bank {bank_id} doesn't match card's bank {selected_bank.id}")
                        return []
                except (ValueError, TypeError):
                    pass
            
            # Use the selected card ID
            user_card_ids = [selected_card.id] if selected_card else []
            
            # Use the selected bank
            user_banks = [selected_bank.id] if selected_bank else []
            
            logger.info(f"User {self.request.user.id} - Selected card: {selected_card.name if selected_card else 'None'} (ID: {card_id}), Bank: {selected_bank.name if selected_bank else 'None'}")
        else:
            # No card_id provided - show deals for ALL user cards
            user_card_ids = []
            user_banks = []
            
            # Get all card IDs and bank IDs from user's cards
            for user_card in all_user_cards:
                if user_card.card:
                    if user_card.card.id not in user_card_ids:
                        user_card_ids.append(user_card.card.id)
                if user_card.card and user_card.card.bank:
                    if user_card.card.bank.id not in user_banks:
                        user_banks.append(user_card.card.bank.id)
            
            # If bank_id is provided, filter to that bank only
            if bank_id:
                try:
                    bank_id_int = int(bank_id)
                    # Filter user_card_ids to only cards from this bank
                    filtered_card_ids = []
                    for user_card in all_user_cards:
                        if user_card.card and user_card.card.bank and user_card.card.bank.id == bank_id_int:
                            if user_card.card.id not in filtered_card_ids:
                                filtered_card_ids.append(user_card.card.id)
                    user_card_ids = filtered_card_ids
                    user_banks = [bank_id_int]
                except (ValueError, TypeError):
                    pass
            
            logger.info(f"User {self.request.user.id} - Showing deals for ALL user cards ({len(user_card_ids)} cards from {len(user_banks)} banks)")
            # Set selected_card to None when showing all cards
            selected_card = None
        
        # Get query parameters for filtering (apply BEFORE union)
        # city is already retrieved above, but get other filters
        category = self.request.query_params.get('category')
        search = self.request.query_params.get('search')
        show_expired = self.request.query_params.get('show_expired', 'false').lower() == 'true'
        
        # Base filter for all querysets
        base_filter = Q(is_active=True)
        if not show_expired:
            base_filter &= Q(is_expired=False)
        
        if city:
            # IMPORTANT: Handle city case-insensitively - frontend may send "Lahore" but DB stores "LAHORE"
            base_filter &= Q(city__iexact=city.upper())
        
        if category:
            base_filter &= Q(category__icontains=category)
        
        if search:
            base_filter &= (
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(target_entity_name__icontains=search)
            )
        
        # Professional logic: 
        # IMPORTANT: Get IDs from each queryset separately to avoid ORDER BY in union
        # Django applies model's default ordering to union subqueries, causing errors
        # Solution: Fetch IDs separately, combine, then fetch objects
        
        # IMPORTANT: Only show deals that are DIRECTLY linked to user's cards
        # Do NOT show bank-level deals or deals from other cards in the same bank
        # This ensures we only show deals that are actually for the user's specific cards
        
        # 1. Get deals specifically linked to user's cards (ONLY these deals)
        # This includes deals scraped manually in "Bank & Card" tab AND automatically in "My Cards" tab
        # IMPORTANT: This finds ALL deals linked to ANY of the user's cards
        card_specific_ids = []
        if user_card_ids:
            # First, get deals with base_filter (respects city, category, search)
            card_specific_ids = list(
                PeekabooDeal.objects.filter(
                    base_filter,
                    linked_cards__id__in=user_card_ids,  # Find deals linked to ANY of user's cards
                    bank_id__in=user_banks  # IMPORTANT: Only deals from user's banks
                ).order_by().values_list('id', flat=True).distinct()
            )
            
            # ALSO get deals linked to user's cards that might not match base_filter (e.g., different city)
            # This ensures deals scraped manually in "Bank & Card" tab are always shown in "My Cards"
            # Only apply is_active and is_expired filters, ignore city/category for directly linked deals
            minimal_filter = Q(is_active=True)
            if not show_expired:
                minimal_filter &= Q(is_expired=False)
            
            additional_linked_ids = list(
                PeekabooDeal.objects.filter(
                    minimal_filter,
                    linked_cards__id__in=user_card_ids,
                    bank_id__in=user_banks  # IMPORTANT: Only deals from user's banks
                ).order_by().exclude(id__in=card_specific_ids).values_list('id', flat=True).distinct()
            )
            card_specific_ids.extend(additional_linked_ids)
            
            logger.info(f"✅ Found {len(card_specific_ids)} deals directly linked to user's cards (IDs: {user_card_ids})")
            logger.info(f"   - {len(card_specific_ids) - len(additional_linked_ids)} matches base_filter (city/category)")
            logger.info(f"   - {len(additional_linked_ids)} additional linked deals (from manual scraping)")
        
        # 2. DO NOT include bank-level deals - only show deals directly linked to user's cards
        # This ensures we don't show deals from other cards in the same bank
        bank_deal_ids = []
        
        # 3. Match deals by card NAME in associations (for ALL user cards, not just selected card)
        # IMPORTANT: Only match deals from user's banks to ensure we only show user's bank deals
        # IMPORTANT: Match deals for ALL user cards (same as manual selection for each card)
        card_name_deal_ids = []
        user_card_names = []
        user_card_name_variations = []
        
        # IMPORTANT: Match deals for ALL user cards (same as manual selection)
        # When auto-scraping, we scrape for ALL cards, so we should match deals for ALL cards
        if user_card_ids:
            # Get all user cards to match deals for ALL of them
            from cards.models import CreditCard
            user_cards_objs = CreditCard.objects.filter(id__in=user_card_ids)
            
            for user_card_obj in user_cards_objs:
                card_name = user_card_obj.name
                user_card_names.append(card_name)
                # IMPORTANT: Use SAME card name variations as Bank & Card tab to ensure exact same matching
                # Bank & Card tab uses these 4 variations, so My Cards tab should also use these 4
                user_card_name_variations.append(card_name)  # Exact match
                user_card_name_variations.append(card_name.replace(' Card', ''))
                user_card_name_variations.append(card_name.replace(' card', ''))
                user_card_name_variations.append(card_name.replace('Debit Card', '').replace('Credit Card', '').strip())
            
            # Remove duplicates from variations
            user_card_name_variations = list(set(user_card_name_variations))
        
        if user_card_name_variations and user_banks:
            # IMPORTANT: Only match deals from the selected bank
            from django.db import connection
            is_postgres = 'postgresql' in connection.vendor
            all_excluded_ids = card_specific_ids + bank_deal_ids
            
            if is_postgres:
                # PostgreSQL JSON contains - match by card name in associations, but ONLY for selected bank
                for card_name_var in user_card_name_variations:
                    try:
                        name_matched_ids = list(
                            PeekabooDeal.objects.filter(
                                base_filter,
                                bank_id__in=user_banks,  # IMPORTANT: Only match deals from selected bank
                                associations__contains=[{'name': card_name_var}]
                            ).order_by().exclude(id__in=all_excluded_ids).values_list('id', flat=True).distinct()
                        )
                        card_name_deal_ids.extend(name_matched_ids)
                    except Exception as e:
                        logger.debug(f"Error matching by card name '{card_name_var}': {str(e)}")
                        continue
            else:
                # SQLite - filter in Python, but ONLY for selected bank
                all_deals = PeekabooDeal.objects.filter(
                    base_filter,
                    bank_id__in=user_banks  # IMPORTANT: Only match deals from selected bank
                ).order_by().exclude(id__in=all_excluded_ids)
                
                for deal in all_deals:
                    if deal.id in card_name_deal_ids:
                        continue
                    if deal.associations:
                        for assoc in deal.associations:
                            if isinstance(assoc, dict):
                                assoc_name = assoc.get('name', '')
                                if not assoc_name:
                                    continue
                                assoc_name_lower = assoc_name.lower()
                                # IMPORTANT: Use SAME matching logic as Bank & Card tab
                                # Bank & Card tab uses: card_name_var.lower() in assoc_name.lower() or assoc_name.lower() in card_name_var.lower()
                                for card_name_var in user_card_name_variations:
                                    card_name_var_lower = card_name_var.lower()
                                    # SAME matching as Bank & Card tab
                                    if card_name_var_lower in assoc_name_lower or assoc_name_lower in card_name_var_lower:
                                        card_name_deal_ids.append(deal.id)
                                        logger.debug(f"✅ Matched deal {deal.id} by card name: '{card_name_var}' matches '{assoc_name}' (bank: {deal.bank.name if deal.bank else 'None'})")
                                        break
                                if deal.id in card_name_deal_ids:
                                    break
        
        # 4. IMPORTANT: Do NOT use association type ID matching - use SAME logic as Bank & Card tab
        # Bank & Card tab only uses: linked_deals + association_deals (by card name)
        # So My Cards tab should also only use: card_specific_ids + card_name_deal_ids
        # This ensures both tabs show the EXACT same deals
        association_deal_ids = []
        
        # REMOVED: Association type ID matching - Bank & Card tab doesn't use this
        # This ensures My Cards tab shows EXACT same deals as Bank & Card tab
        
        # REMOVED: The entire association_type_ids matching block - not used in Bank & Card tab
        if False:  # Disabled to match Bank & Card tab
            # Filter deals by associations JSON field, but ONLY for selected bank
            from django.db import connection
            is_postgres = 'postgresql' in connection.vendor
            
            all_excluded_ids = card_specific_ids + bank_deal_ids + card_name_deal_ids
            
            if is_postgres:
                # PostgreSQL JSON contains - check association type IDs, but ONLY for selected bank
                for assoc_id in association_type_ids:
                    assoc_ids = list(
                        PeekabooDeal.objects.filter(
                            base_filter,
                            bank_id__in=user_banks,  # IMPORTANT: Only match deals from selected bank
                            associations__contains=[{'typeId': assoc_id}]
                        ).order_by().exclude(id__in=all_excluded_ids).values_list('id', flat=True).distinct()
                    )
                    association_deal_ids.extend(assoc_ids)
            else:
                # SQLite - filter in Python, but ONLY for selected bank
                all_deals = PeekabooDeal.objects.filter(
                    base_filter,
                    bank_id__in=user_banks  # IMPORTANT: Only match deals from selected bank
                ).order_by().exclude(id__in=all_excluded_ids)
                
                for deal in all_deals:
                    if deal.id in association_deal_ids:
                        continue
                    if deal.associations:
                        for assoc in deal.associations:
                            if isinstance(assoc, dict):
                                assoc_type_id = assoc.get('typeId')
                                if assoc_type_id in association_type_ids:
                                    association_deal_ids.append(deal.id)
                                    break
        
        # 5. DO NOT use source_entity_name matching - only show deals directly linked to cards
        # This ensures we don't show deals from other cards in the same bank
        source_entity_deal_ids = []
        
        # Combine all deal IDs (ONLY card-specific and card-name matched - SAME as Bank & Card tab)
        # IMPORTANT: Do NOT include association_type_ids - Bank & Card tab doesn't use them
        # This ensures My Cards tab shows EXACT same deals as Bank & Card tab
        all_deal_ids = card_specific_ids + card_name_deal_ids
        
        # Remove duplicates while preserving order
        seen = set()
        unique_deal_ids = []
        for deal_id in all_deal_ids:
            if deal_id not in seen:
                seen.add(deal_id)
                unique_deal_ids.append(deal_id)
        
        # Log summary for debugging - comprehensive logging
        logger.info(f"User {self.request.user.id} - Found {len(unique_deal_ids)} total deals: "
                   f"{len(card_specific_ids)} card-specific (linked to {len(user_card_ids)} cards), "
                   f"{len(card_name_deal_ids)} card-name matched. "
                   f"Using SAME logic as Bank & Card tab (no association type IDs).")
        
        # Additional debug: Check if deals are actually linked to user's cards
        if user_card_ids:
            linked_deals_count = PeekabooDeal.objects.filter(
                linked_cards__id__in=user_card_ids,
                is_active=True,
                is_expired=False
            ).count()
            logger.info(f"  Directly linked deals count: {linked_deals_count} (should match card_specific_ids: {len(card_specific_ids)})")
        
        # IMPORTANT: Only show deals that match user's cards/banks
        # Do NOT show all deals - only show deals relevant to user's specific cards
        if not unique_deal_ids:
            logger.warning(f"User {self.request.user.id} - No deals found for user's cards. "
                          f"User has {len(user_card_ids)} cards from {len(user_banks)} banks: {user_banks}. "
                          f"Card names: {user_card_names}. "
                          f"User should scrape deals in 'Bank & Card' tab for their specific cards.")
        
        # Return a queryset with these IDs (will be fetched in list method)
        # We'll use a special marker to indicate we have IDs ready
        class QuerysetWithIDs:
            def __init__(self, deal_ids):
                self.deal_ids = deal_ids
            
            def __iter__(self):
                # This won't be called, but needed for compatibility
                return iter([])
        
        # Store IDs in a way we can access them in list method
        # Use a simple approach: return None and handle in list method
        return unique_deal_ids
    
    def list(self, request, *args, **kwargs):
        # IMPORTANT: Auto-scrape for ALL user cards when "My Cards" tab is opened
        # If no card_id/bank_id provided, automatically scrape for ALL user's cards
        # This works EXACTLY like manual selection - same scraping function, same parameters
        card_id = request.query_params.get('card_id')
        bank_id = request.query_params.get('bank_id')
        city = request.query_params.get('city', 'LAHORE')  # Default to LAHORE (uppercase) if not provided
        # Normalize city to uppercase to match database format
        if city:
            city = city.upper()
        
        logger.info(f"🔍 My Cards request - card_id: {card_id}, bank_id: {bank_id}, city: {city}")
        
        # If NO card_id AND NO bank_id provided, automatically scrape for ALL user cards
        # IMPORTANT: Return existing deals immediately, then scrape in background
        # This ensures user sees data instantly while scraping happens in background
        if not card_id and not bank_id:
            logger.info(f"🔍 AUTO MODE: No card_id/bank_id provided - will return existing deals immediately, scrape in background")
            from scraping.tasks_peekaboo import scrape_peekaboo_deals_by_bank
            from datetime import timedelta
            
            # Get all user's active cards
            user_cards = UserCard.objects.filter(
                user=request.user,
                is_active=True
            ).select_related('card', 'card__bank')
            
            if user_cards.exists():
                logger.info(f"🔍 AUTO: Found {user_cards.count()} user cards - checking which need scraping")
                
                # Check deals per card - if a new card is added, it will be scraped even if other cards have recent deals
                recent_threshold = timezone.now() - timedelta(hours=1)
                cards_to_scrape = []
                cards_with_deals = []
                
                for user_card in user_cards:
                    if not user_card.card or not user_card.card.bank:
                        continue
                    
                    card = user_card.card
                    bank = card.bank
                    
                    # Check if this specific card has recent deals
                    existing_deals_count = PeekabooDeal.objects.filter(
                        linked_cards__id=card.id,
                        bank_id=bank.id,
                        city__iexact=city,
                        is_active=True,
                        is_expired=False
                    ).filter(
                        Q(created_at__gte=recent_threshold) | Q(updated_at__gte=recent_threshold)
                    ).distinct().count()
                    
                    if existing_deals_count > 0:
                        cards_with_deals.append((card, bank, existing_deals_count))
                        logger.info(f"   ✅ Card {bank.code} - {card.name} (ID: {card.id}): Has {existing_deals_count} recent deals - skipping scraping")
                    else:
                        cards_to_scrape.append((card, bank))
                        logger.info(f"   📥 Card {bank.code} - {card.name} (ID: {card.id}): No recent deals - will scrape in background")
                
                # Trigger background scraping for cards that need it (don't wait for completion)
                if cards_to_scrape:
                    logger.info(f"📥 AUTO: Triggering background scraping for {len(cards_to_scrape)} card(s) (out of {len(cards_with_deals) + len(cards_to_scrape)} total cards)")
                    from scraping.tasks_peekaboo import scrape_peekaboo_entities_by_card
                    
                    def scrape_in_background():
                        """Scrape deals in background thread"""
                        for card, bank in cards_to_scrape:
                            try:
                                # STEP 1: Scrape entities first
                                logger.info(f"   📥 BACKGROUND: Scraping entities for {bank.code} - {card.name} (ID: {card.id}) in {city}...")
                                entities_result = scrape_peekaboo_entities_by_card(
                                    bank_code=bank.code,
                                    card_id=card.id,
                                    city_name=city,
                                    limit=100,
                                    offset=0
                                )
                                entities_count = entities_result.get('total', 0) if isinstance(entities_result, dict) else 0
                                logger.info(f"   ✅ BACKGROUND: Scraped {entities_count} entities for {card.name}")
                                
                                # STEP 2: Scrape deals
                                logger.info(f"   📥 BACKGROUND: Scraping deals for {bank.code} - {card.name} (ID: {card.id}) in {city}...")
                                result = scrape_peekaboo_deals_by_bank(
                                    bank.code,
                                    city,
                                    card_id=card.id
                                )
                                
                                if isinstance(result, dict):
                                    created = result.get('created', 0)
                                    updated = result.get('updated', 0)
                                    skipped = result.get('skipped', 0)
                                elif isinstance(result, tuple) and len(result) == 3:
                                    created, updated, skipped = result
                                else:
                                    created, updated, skipped = 0, 0, 0
                                
                                logger.info(f"   ✅ BACKGROUND: Scraped {created} new, {updated} updated deals for {card.name}")
                            except Exception as e:
                                logger.error(f"   ❌ BACKGROUND: Error scraping {card.name}: {str(e)}")
                                continue
                    
                    # Start scraping in background thread (non-blocking)
                    import threading
                    thread = threading.Thread(target=scrape_in_background, daemon=True)
                    thread.start()
                    logger.info(f"✅ BACKGROUND: Started background scraping thread for {len(cards_to_scrape)} cards")
                else:
                    logger.info(f"✅ AUTO: All {len(cards_with_deals)} card(s) have recent deals - no scraping needed")
        
        # If specific card_id, bank_id, and city are provided, check if scraping is needed
        # IMPORTANT: This is MANUAL selection - uses EXACTLY the same scraping function as automatic
        elif card_id and bank_id and city:
            logger.info(f"🔄 MANUAL MODE: card_id={card_id}, bank_id={bank_id} provided - will scrape for this specific card (same function as auto)")
            from scraping.tasks_peekaboo import scrape_peekaboo_deals_by_bank
            from cards.models import CreditCard, Bank
            from datetime import timedelta
            
            try:
                # Verify card belongs to user
                user_card = UserCard.objects.filter(
                    user=request.user,
                    is_active=True,
                    card_id=card_id
                ).select_related('card', 'card__bank').first()
                
                if not user_card or not user_card.card or not user_card.card.bank:
                    logger.warning(f"User {request.user.id} - Card {card_id} not found or invalid")
                else:
                    selected_card = user_card.card
                    selected_bank = selected_card.bank
                    
                    # Verify bank_id matches
                    try:
                        bank_id_int = int(bank_id)
                        if selected_bank.id != bank_id_int:
                            logger.warning(f"User {request.user.id} - Bank {bank_id} doesn't match card's bank")
                        else:
                            # IMPORTANT: Always scrape in manual mode (SAME AS AUTO MODE)
                            # Don't check for recent scrapes - always scrape to match auto behavior exactly
                            # Manual flow: 
                            #   1. Scrape entities first (same as auto)
                            #   2. Then scrape deals (same as auto)
                            from scraping.tasks_peekaboo import scrape_peekaboo_entities_by_card
                            
                            # STEP 1: Scrape entities first (SAME AS AUTO)
                            logger.info(f"📥 MANUAL STEP 1: Scraping entities for {selected_bank.code} - {selected_card.name} (ID: {card_id}) in {city}... (SAME AS AUTO - always scrape)")
                            entities_result = scrape_peekaboo_entities_by_card(
                                bank_code=selected_bank.code,  # EXACT same as auto
                                card_id=card_id,               # EXACT same as auto
                                city_name=city,                # EXACT same as auto
                                limit=100,                     # Same as auto
                                offset=0                       # Same as auto
                            )
                            entities_count = entities_result.get('total', 0) if isinstance(entities_result, dict) else 0
                            logger.info(f"✅ MANUAL STEP 1: Scraped {entities_count} entities for {selected_card.name} (SAME AS AUTO)")
                            
                            # STEP 2: Scrape deals (EXACT SAME AS get_entities_by_card)
                            # get_entities_by_card calls: scrape_peekaboo_deals_by_bank(bank.code, city, card_id=card.id)
                            logger.info(f"📥 MANUAL STEP 2: Scraping deals for {selected_bank.code} - {selected_card.name} (ID: {card_id}) in {city}... (EXACT SAME AS get_entities_by_card)")
                            result = scrape_peekaboo_deals_by_bank(
                                selected_bank.code,  # EXACT same as get_entities_by_card: bank.code (positional)
                                city,                # EXACT same as get_entities_by_card: city (positional)
                                card_id=card_id      # EXACT same as get_entities_by_card: card_id=card.id (keyword)
                            )
                            # Handle both dict and tuple return types
                            if isinstance(result, dict):
                                created = result.get('created', 0)
                                updated = result.get('updated', 0)
                                skipped = result.get('skipped', 0)
                            elif isinstance(result, tuple) and len(result) == 3:
                                created, updated, skipped = result
                            else:
                                created, updated, skipped = 0, 0, 0
                            logger.info(f"✅ Manual scraped {created} new, {updated} updated deals for {selected_card.name} (skipped: {skipped})")
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid bank_id: {bank_id}")
            except Exception as e:
                logger.error(f"❌ Error scraping deals: {str(e)}")
        
        # After scraping (or if no scraping needed), get deals for selected card
        # get_queryset() now returns a list of IDs instead of a queryset
        deal_ids = self.get_queryset()
        
        if not deal_ids:
            return Response({
                'count': 0,
                'next': None,
                'previous': None,
                'results': []
            })
        
        # Fetch the actual objects by ID (this allows us to sort in Python)
        # Use order_by() to explicitly remove any default ordering
        deals_list = list(PeekabooDeal.objects.filter(id__in=deal_ids).order_by())
        
        # Sort by: end_date (descending), then created_at (descending)
        deals_list.sort(key=lambda x: (
            x.end_date if x.end_date else timezone.now(),
            x.created_at if x.created_at else timezone.now()
        ), reverse=True)
        
        # Pagination (manual pagination since we have a list)
        page_size = self.paginator.page_size if hasattr(self, 'paginator') and self.paginator else 20
        page_number = request.query_params.get('page', 1)
        try:
            page_number = int(page_number)
        except (ValueError, TypeError):
            page_number = 1
        
        start = (page_number - 1) * page_size
        end = start + page_size
        paginated_deals = deals_list[start:end]
        
        serializer = self.get_serializer(paginated_deals, many=True)
        
        # Return paginated response
        return Response({
            'count': len(deals_list),
            'next': f"{request.path}?page={page_number + 1}" if end < len(deals_list) else None,
            'previous': f"{request.path}?page={page_number - 1}" if page_number > 1 else None,
            'results': serializer.data
        })

class PeekabooCategoryListView(generics.ListAPIView):
    """List all Peekaboo categories"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if PeekabooCategorySerializer:
            return PeekabooCategorySerializer
        from rest_framework import serializers
        return serializers.Serializer
    
    def get_queryset(self):
        if not PeekabooCategory:
            return []
        return PeekabooCategory.objects.filter(is_active=True).order_by('display_order', 'name')
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class PeekabooEntityListView(generics.ListAPIView):
    """List all Peekaboo entities/merchants"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if PeekabooEntitySerializer:
            return PeekabooEntitySerializer
        from rest_framework import serializers
        return serializers.Serializer
    
    def get_queryset(self):
        if not PeekabooEntity:
            return []
        
        queryset = PeekabooEntity.objects.filter(is_active=True)
        
        # Filter by search term
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(keywords__icontains=search)
            )
        
        return queryset.order_by('name')
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class PeekabooDealByBankCardView(generics.ListAPIView):
    """List Peekaboo deals filtered by bank and/or card"""
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_serializer_class(self):
        if PeekabooDealSerializer:
            return PeekabooDealSerializer
        from rest_framework import serializers
        return serializers.Serializer
    
    def get_queryset(self):
        if not PeekabooDeal:
            return []
        
        # Get query parameters
        bank_id = self.request.query_params.get('bank_id')
        card_id = self.request.query_params.get('card_id')
        city = self.request.query_params.get('city')
        show_expired = self.request.query_params.get('show_expired', 'false').lower() == 'true'
        search = self.request.query_params.get('search')
        
        # Start with base queryset
        queryset = PeekabooDeal.objects.all()
        
        # Build filters
        filters = Q()
        
        # Filter by bank
        if bank_id:
            try:
                bank_id_int = int(bank_id)
                filters &= Q(bank_id=bank_id_int)
                logger.info(f"Filtering by bank_id: {bank_id_int}")
            except (ValueError, TypeError):
                pass
        
        # Filter by city (case-insensitive)
        if city:
            filters &= Q(city__iexact=city.upper())
            logger.info(f"Filtering by city: {city.upper()}")
        
        # Filter expired/active
        if not show_expired:
            filters &= Q(is_expired=False, is_active=True)
            logger.info("Filtering out expired deals")
        
        # Apply base filters first
        queryset = queryset.filter(filters)
        
        # Filter by card - use linked_cards many-to-many relationship
        if card_id:
            from cards.models import CreditCard
            from django.db import connection
            try:
                card = CreditCard.objects.get(id=card_id)
                logger.info(f"Filtering by card: {card.name} (ID: {card_id})")
                
                # First: Get deals directly linked to this card
                linked_deals = queryset.filter(linked_cards__id=card_id).distinct()
                linked_count = linked_deals.count()
                logger.info(f"Found {linked_count} deals directly linked to card {card_id}")
                
                # Second: Filter by associations JSON field (for deals not yet linked)
                card_name_variations = [
                    card.name,
                    card.name.replace(' Card', ''),
                    card.name.replace(' card', ''),
                    card.name.replace('Debit Card', '').replace('Credit Card', '').strip(),
                ]
                
                # Use database-agnostic approach for JSON filtering
                is_postgres = 'postgresql' in connection.vendor
                
                association_deals = queryset.none()
                if is_postgres:
                    # PostgreSQL supports JSON contains
                    for card_name_var in card_name_variations:
                        try:
                            association_deals = queryset.filter(
                                associations__contains=[{'name': card_name_var}]
                            ).exclude(id__in=linked_deals.values_list('id', flat=True)).distinct()
                            if association_deals.exists():
                                logger.info(f"Found {association_deals.count()} deals by association name: {card_name_var}")
                                break
                        except Exception as e:
                            logger.debug(f"Error filtering by association name '{card_name_var}': {str(e)}")
                            continue
                
                # If not PostgreSQL or JSON contains failed, filter in Python
                if not is_postgres or not association_deals.exists():
                    # Get all deals and filter in Python
                    all_deals = queryset.exclude(id__in=linked_deals.values_list('id', flat=True))
                    matching_deal_ids = []
                    for deal in all_deals:
                        if deal.associations:
                            for assoc in deal.associations:
                                if isinstance(assoc, dict):
                                    assoc_name = assoc.get('name', '')
                                    for card_name_var in card_name_variations:
                                        if card_name_var.lower() in assoc_name.lower() or assoc_name.lower() in card_name_var.lower():
                                            matching_deal_ids.append(deal.id)
                                            break
                    
                    if matching_deal_ids:
                        association_deals = queryset.filter(id__in=matching_deal_ids).distinct()
                        logger.info(f"Found {association_deals.count()} deals by association name (Python filtering)")
                
                # Combine both querysets
                queryset = (linked_deals | association_deals).distinct()
                total_count = queryset.count()
                logger.info(f"Total deals found for card {card_id}: {total_count}")
                
            except CreditCard.DoesNotExist:
                logger.warning(f"Card {card_id} not found")
                # If card doesn't exist, just filter by linked_cards
                queryset = queryset.filter(linked_cards__id=card_id).distinct()
        
        # Search filter (apply after card filtering)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(target_entity_name__icontains=search)
            )
        
        final_count = queryset.count()
        logger.info(f"Final queryset count after all filters: {final_count}")
        
        return queryset.order_by('-end_date', '-created_at')
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        
        # Pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def trigger_peekaboo_scraping(request):
    """Manually trigger Peekaboo scraping"""
    try:
        from scraping.tasks_peekaboo import scrape_peekaboo_deals, scrape_peekaboo_categories, scrape_peekaboo_entities
        
        # Check if models are available
        if not PeekabooDeal or not PeekabooCategory:
            return Response({
                'status': 'error',
                'message': 'Peekaboo models not available. Please run migrations: python manage.py migrate'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Check if bank-specific scraping is requested
        bank_code = request.data.get('bank_code')
        scrape_all_banks = request.data.get('scrape_all_banks', False)
        scrape_card_associations = request.data.get('scrape_card_associations', False)
        
        if scrape_card_associations and bank_code:
            # Scrape card associations for a specific bank
            from scraping.tasks_peekaboo import scrape_peekaboo_card_associations
            city = request.data.get('city', 'Lahore')
            try:
                task = scrape_peekaboo_card_associations.delay(bank_code, city)
                return Response({
                    'status': 'success',
                    'message': f'Scraping card associations for {bank_code} started',
                    'task_id': task.id if task else None
                })
            except:
                result = scrape_peekaboo_card_associations(bank_code, city)
                return Response({
                    'status': 'success',
                    'message': f'Scraping card associations for {bank_code} completed',
                    'results': result
                })
        elif scrape_all_banks:
            # Scrape all banks with card associations
            from scraping.tasks_peekaboo import scrape_all_banks_card_deals
            try:
                task = scrape_all_banks_card_deals.delay()
                return Response({
                    'status': 'success',
                    'message': 'Scraping all banks card-based deals started',
                    'task_id': task.id if task else None
                })
            except:
                result = scrape_all_banks_card_deals()
                return Response({
                    'status': 'success',
                    'message': 'Scraping all banks card-based deals completed',
                    'results': result
                })
        elif bank_code:
            # Scrape specific bank (with optional card_id for card-specific scraping)
            from scraping.tasks_peekaboo import scrape_peekaboo_deals_by_bank, scrape_peekaboo_card_associations, scrape_peekaboo_entities_by_card
            city = request.data.get('city', 'Lahore')
            card_id = request.data.get('card_id')  # Optional: scrape for specific card
            
            try:
                if card_id:
                    # Scrape deals and entities for specific card
                    from cards.models import CreditCard
                    try:
                        card = CreditCard.objects.get(id=card_id)
                        # Scrape entities (which will also trigger deal scraping)
                        entities_task = scrape_peekaboo_entities_by_card.delay(bank_code, card_id, city)
                        # Also scrape general deals for the bank
                        deals_task = scrape_peekaboo_deals_by_bank.delay(bank_code, city)
                        return Response({
                            'status': 'success',
                            'message': f'Scraping {bank_code} deals for card "{card.name}" in {city} started',
                            'task_ids': {
                                'entities': entities_task.id if entities_task else None,
                                'deals': deals_task.id if deals_task else None,
                            }
                        })
                    except CreditCard.DoesNotExist:
                        return Response({
                            'status': 'error',
                            'message': f'Card with id {card_id} not found'
                        }, status=status.HTTP_404_NOT_FOUND)
                else:
                    # Scrape all deals for bank (general scraping)
                    # First scrape card associations, then deals
                    from scraping.tasks_peekaboo import scrape_peekaboo_card_associations
                    assoc_task = scrape_peekaboo_card_associations.delay(bank_code, city)
                    deals_task = scrape_peekaboo_deals_by_bank.delay(bank_code, city)
                    return Response({
                        'status': 'success',
                        'message': f'Scraping {bank_code} card associations and deals started',
                        'task_ids': {
                            'associations': assoc_task.id if assoc_task else None,
                            'deals': deals_task.id if deals_task else None,
                        }
                    })
            except Exception as e:
                # Fallback to synchronous execution
                if card_id:
                    from cards.models import CreditCard
                    try:
                        card = CreditCard.objects.get(id=card_id)
                        result_entities = scrape_peekaboo_entities_by_card(bank_code, card_id, city)
                        result_deals = scrape_peekaboo_deals_by_bank(bank_code, city)
                        return Response({
                            'status': 'success',
                            'message': f'Scraping {bank_code} deals for card "{card.name}" in {city} completed',
                            'results': {
                                'entities': result_entities,
                                'deals': result_deals,
                            }
                        })
                    except CreditCard.DoesNotExist:
                        return Response({
                            'status': 'error',
                            'message': f'Card with id {card_id} not found'
                        }, status=status.HTTP_404_NOT_FOUND)
                else:
                    result_assoc = scrape_peekaboo_card_associations(bank_code, city)
                    result_deals = scrape_peekaboo_deals_by_bank(bank_code, city)
                    return Response({
                        'status': 'success',
                        'message': f'Scraping {bank_code} card associations and deals completed',
                        'results': {
                            'associations': result_assoc,
                            'deals': result_deals,
                        }
                    })
        else:
            # Default: scrape all deals (general scraping)
            # Try to trigger tasks asynchronously (Celery)
            try:
                entities_task = scrape_peekaboo_entities.delay()
                category_task = scrape_peekaboo_categories.delay()
                deals_task = scrape_peekaboo_deals.delay()
                
                return Response({
                    'status': 'success',
                    'message': 'Peekaboo scraping started successfully (running in background)',
                    'task_ids': {
                        'entities': entities_task.id if entities_task else None,
                        'categories': category_task.id if category_task else None,
                        'deals': deals_task.id if deals_task else None,
                    }
                })
            except Exception as celery_error:
                # If Celery is not running, run synchronously
                logger.warning(f"Celery not available, running synchronously: {str(celery_error)}")
                
                # Run synchronously
                entities_result = scrape_peekaboo_entities()
                category_result = scrape_peekaboo_categories()
                deals_result = scrape_peekaboo_deals()
                
                return Response({
                    'status': 'success',
                    'message': 'Peekaboo scraping completed (ran synchronously - Celery not running)',
                    'results': {
                        'entities': entities_result,
                        'categories': category_result,
                        'deals': deals_result,
                    }
                })
            
    except ImportError as e:
        logger.error(f"Import error in trigger_peekaboo_scraping: {str(e)}")
        import traceback
        error_trace = traceback.format_exc()
        return Response({
            'status': 'error',
            'message': f'Failed to import scraping tasks: {str(e)}',
            'details': error_trace if request.user.is_staff else 'Make sure migrations are run: python manage.py migrate'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"Error in trigger_peekaboo_scraping: {str(e)}\n{error_trace}")
        return Response({
            'status': 'error',
            'message': f'Failed to start scraping: {str(e)}',
            'details': error_trace if request.user.is_staff else None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticatedOrReadOnly])
def get_entities_by_card(request):
    """
    Get entities filtered by bank and card, then fetch deals for those entities.
    This endpoint scrapes entities from Peekaboo API with proper card filters.
    """
    from cards.models import CreditCard, Bank
    from scraping.tasks_peekaboo import scrape_peekaboo_entities_by_card
    
    bank_id = request.query_params.get('bank_id')
    card_id = request.query_params.get('card_id')
    city = request.query_params.get('city', 'Lahore')
    limit = int(request.query_params.get('limit', 12))
    offset = int(request.query_params.get('offset', 0))
    sort_by = request.query_params.get('sort_by', 'trending')  # trending, rating, name
    
    if not bank_id or not card_id:
        return Response({
            'error': 'bank_id and card_id are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Get bank and card
        bank = Bank.objects.get(id=bank_id)
        card = CreditCard.objects.get(id=card_id, bank=bank)
        
        # Scrape entities with card filters
        result = scrape_peekaboo_entities_by_card(
            bank_code=bank.code,
            card_id=card.id,
            city_name=city,
            limit=limit,
            offset=offset
        )
        
        entities = result.get('entities', [])
        total = result.get('total', 0)
        next_page = result.get('nextPage', False)
        
        # IMPORTANT: Also scrape deals for the selected card and save them to DB
        # This ensures deals are available in "My Cards" tab
        from scraping.tasks_peekaboo import scrape_peekaboo_deals_by_bank
        logger.info(f"Scraping deals for {bank.code} with card {card.id} in {city}...")
        deals_result = scrape_peekaboo_deals_by_bank(bank.code, city, card_id=card.id)
        logger.info(f"Deals scraped: {deals_result.get('created', 0)} created, {deals_result.get('updated', 0)} updated")
        
        # For each entity, fetch its deals
        entities_with_deals = []
        for entity_data in entities:
            entity_id = entity_data.get('entity_id')
            
            # Get deals for this entity
            if PeekabooDeal:
                # First, get ALL deals for this entity (for counting)
                all_deals_for_entity = PeekabooDeal.objects.filter(
                    raw_entity_id=entity_id,
                    bank=bank,
                    linked_cards=card,
                    is_expired=False,
                    is_active=True
                ).distinct()
                
                # If no deals found via linked_cards, try associations JSON
                if all_deals_for_entity.count() == 0:
                    # Filter in Python for SQLite compatibility
                    all_deals = PeekabooDeal.objects.filter(
                        raw_entity_id=entity_id,
                        bank=bank,
                        is_expired=False,
                        is_active=True
                    )
                    matching_deals = []
                    for deal in all_deals:
                        if deal.associations:
                            for assoc in deal.associations:
                                if isinstance(assoc, dict):
                                    assoc_type_id = assoc.get('typeId')
                                    if assoc_type_id and card.peekaboo_association_type_id and assoc_type_id == card.peekaboo_association_type_id:
                                        matching_deals.append(deal)
                                        break
                    all_deals_for_entity = matching_deals
                
                # Count ALL deals (not just the ones we'll show)
                total_deal_count = len(all_deals_for_entity) if isinstance(all_deals_for_entity, list) else all_deals_for_entity.count()
                
                # Limit to 5 deals for display
                deals_to_show = all_deals_for_entity[:5] if isinstance(all_deals_for_entity, list) else list(all_deals_for_entity[:5])
                
                entity_data['deals'] = [
                    {
                        'id': deal.id,
                        'deal_id': deal.deal_id,
                        'title': deal.title,
                        'description': deal.description,
                        'percentage_value': float(deal.percentage_value) if deal.percentage_value else None,
                        'start_date': deal.start_date.isoformat() if deal.start_date else None,
                        'end_date': deal.end_date.isoformat() if deal.end_date else None,
                        'target_entity_name': deal.target_entity_name,
                        'target_entity_logo': deal.target_entity_logo,
                        'target_branches': deal.target_branches if hasattr(deal, 'target_branches') else {},
                        'associations': deal.associations if hasattr(deal, 'associations') else [],
                        'is_currently_valid': deal.is_currently_valid if hasattr(deal, 'is_currently_valid') else True,
                        'days_remaining': deal.days_remaining if hasattr(deal, 'days_remaining') else None,
                        'image': deal.image if hasattr(deal, 'image') else None,
                    }
                    for deal in deals_to_show
                ]
                # Use total count, not just the displayed deals
                entity_data['deal_count'] = total_deal_count
                
                # Ensure all entity fields are included
                if 'stats' not in entity_data:
                    entity_data['stats'] = {
                        'branches': entity_data.get('stats', {}).get('branches', 0),
                        'partnerOffers': entity_data.get('stats', {}).get('partnerOffers', 0),
                        'brandOffers': entity_data.get('stats', {}).get('brandOffers', 0),
                        'maxDiscount': entity_data.get('stats', {}).get('maxDiscount', 0),
                        'discountFlag': entity_data.get('stats', {}).get('discountFlag', None),
                    }
                
                if 'nearestBranch' in entity_data and entity_data['nearestBranch']:
                    # Ensure openNow is included in nearestBranch
                    if 'openNow' not in entity_data['nearestBranch']:
                        entity_data['nearestBranch']['openNow'] = entity_data.get('openNow', False)
                
                # Ensure openNow is at entity level too
                if 'openNow' not in entity_data:
                    entity_data['openNow'] = entity_data.get('nearestBranch', {}).get('openNow', False) if entity_data.get('nearestBranch') else False
            else:
                entity_data['deals'] = []
                entity_data['deal_count'] = 0
            
            entities_with_deals.append(entity_data)
        
        # Apply sorting
        if sort_by == 'rating':
            entities_with_deals.sort(key=lambda x: x.get('rating', 0) or 0, reverse=True)
        elif sort_by == 'name':
            entities_with_deals.sort(key=lambda x: x.get('name', '').lower())
        elif sort_by == 'deals':
            entities_with_deals.sort(key=lambda x: x.get('deal_count', 0), reverse=True)
        # Default is 'trending' - keep original order
        
        return Response({
            'entities': entities_with_deals,
            'total': total,
            'nextPage': next_page,
            'limit': limit,
            'offset': offset,
        })
        
    except Bank.DoesNotExist:
        return Response({
            'error': 'Bank not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except CreditCard.DoesNotExist:
        return Response({
            'error': 'Card not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error in get_entities_by_card: {str(e)}")
        import traceback
        return Response({
            'error': str(e),
            'traceback': traceback.format_exc() if request.user.is_staff else None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_entities_for_user_cards(request):
    """
    Get entities for ALL user's cards automatically (for "My Cards" tab).
    This aggregates entities from all user cards and shows "Places with Deals" view.
    Works EXACTLY like Bank & Card tab - scrapes entities and deals for each card.
    """
    from cards.models import CreditCard, Bank
    from cards.models import UserCard
    from scraping.tasks_peekaboo import scrape_peekaboo_entities_by_card
    
    city = request.query_params.get('city', 'LAHORE')
    if city:
        city = city.upper()
    limit = int(request.query_params.get('limit', 12))
    offset = int(request.query_params.get('offset', 0))
    sort_by = request.query_params.get('sort_by', 'trending')
    
    # Get all user's active cards
    user_cards = UserCard.objects.filter(
        user=request.user,
        is_active=True
    ).select_related('card', 'card__bank')
    
    if not user_cards.exists():
        return Response({
            'entities': [],
            'total': 0,
            'nextPage': False,
            'limit': limit,
            'offset': offset,
        })
    
    # Aggregate entities from ALL user cards (SAME as Bank & Card tab)
    all_entities_map = {}  # Use entity_id as key to deduplicate
    total_entities = 0
    
    logger.info(f"🔍 AUTO: Fetching entities for {user_cards.count()} user cards in {city}...")
    
    # Check deals per card - if a new card is added, it will be scraped even if other cards have recent deals
    recent_threshold = timezone.now() - timedelta(hours=1)
    cards_to_process = []
    cards_with_deals = []
    cards_needing_scrape = []
    
    for uc in user_cards:
        if uc.card and uc.card.bank:
            card = uc.card
            bank = uc.card.bank
            cards_to_process.append((card, bank))
            logger.info(f"   📋 User Card: {card.name} (ID: {card.id}) from Bank: {bank.name} (Code: {bank.code})")
            
            # Check if this specific card has recent deals
            existing_deals_count = PeekabooDeal.objects.filter(
                linked_cards__id=card.id,
                bank_id=bank.id,
                city__iexact=city,
                is_active=True,
                is_expired=False
            ).filter(
                Q(created_at__gte=recent_threshold) | Q(updated_at__gte=recent_threshold)
            ).distinct().count()
            
            if existing_deals_count > 0:
                cards_with_deals.append((card.id, bank.id, existing_deals_count))
                logger.info(f"   ✅ Card {bank.code} - {card.name} (ID: {card.id}): Has {existing_deals_count} recent deals - skipping scraping")
            else:
                cards_needing_scrape.append((card.id, bank.id))
                logger.info(f"   📥 Card {bank.code} - {card.name} (ID: {card.id}): No recent deals - will scrape")
        else:
            logger.warning(f"   ⚠️ User Card {uc.id} has missing card or bank")
    
    if cards_needing_scrape:
        logger.info(f"📥 AUTO: Will scrape {len(cards_needing_scrape)} card(s) that don't have recent deals (out of {len(cards_with_deals) + len(cards_needing_scrape)} total cards)")
    else:
        logger.info(f"✅ AUTO: All {len(cards_with_deals)} card(s) have recent deals - skipping scraping, using existing data")
    
    for card, bank in cards_to_process:
        logger.info(f"   🔄 Processing card: {card.name} (ID: {card.id}) from {bank.name} (Code: {bank.code})")
        
        # Check if this specific card needs scraping (compare by ID to avoid object identity issues)
        card_needs_scrape = (card.id, bank.id) in cards_needing_scrape
        
        try:
            # Only scrape if this card doesn't have recent deals
            if card_needs_scrape:
                # STEP 1: Scrape entities for this card (EXACT SAME as get_entities_by_card)
                logger.info(f"   📥 AUTO: Scraping entities for {bank.code} - {card.name} (ID: {card.id}) in {city}... (EXACT SAME AS MANUAL)")
                result = scrape_peekaboo_entities_by_card(
                    bank_code=bank.code,  # EXACT same as get_entities_by_card
                    card_id=card.id,      # EXACT same as get_entities_by_card
                    city_name=city,       # EXACT same as get_entities_by_card
                    limit=100,            # Get more entities to aggregate
                    offset=0
                )
                
                entities = result.get('entities', [])
                card_total = result.get('total', 0)
                total_entities = max(total_entities, card_total)  # Use max total
                
                logger.info(f"   ✅ AUTO: Scraped {len(entities)} entities for {card.name} (EXACT SAME AS MANUAL)")
                
                # STEP 2: Scrape deals for this card (EXACT SAME as get_entities_by_card)
                from scraping.tasks_peekaboo import scrape_peekaboo_deals_by_bank
                logger.info(f"   📥 AUTO: Scraping deals for {bank.code} - {card.name} (ID: {card.id}) in {city}... (EXACT SAME AS MANUAL)")
                deals_result = scrape_peekaboo_deals_by_bank(bank.code, city, card_id=card.id)
                logger.info(f"   ✅ AUTO: Scraped {deals_result.get('created', 0)} created, {deals_result.get('updated', 0)} updated deals (EXACT SAME AS MANUAL)")
            else:
                # Use existing entities from database (if available) or fetch from API without scraping
                # For entities, we still need to fetch them from API to show the list, but we don't need to scrape deals again
                logger.info(f"   📋 AUTO: Using existing deals - fetching entities for {bank.code} - {card.name} (ID: {card.id}) in {city}...")
                result = scrape_peekaboo_entities_by_card(
                    bank_code=bank.code,
                    card_id=card.id,
                    city_name=city,
                    limit=100,
                    offset=0
                )
                
                entities = result.get('entities', [])
                card_total = result.get('total', 0)
                total_entities = max(total_entities, card_total)
                
                logger.info(f"   ✅ AUTO: Fetched {len(entities)} entities for {card.name} (using existing deals)")
            
            # Merge entities (deduplicate by entity_id)
            for entity_data in entities:
                entity_id = entity_data.get('entity_id')
                if entity_id:
                    if entity_id not in all_entities_map:
                        all_entities_map[entity_id] = entity_data.copy()
                        # Initialize deals list
                        all_entities_map[entity_id]['deals'] = []
                        all_entities_map[entity_id]['deal_count'] = 0
                        all_entities_map[entity_id]['cards'] = []  # Track which cards have this entity
                    
                    # Add card info to entity (only if not already added)
                    # Check if this card is already in the cards list
                    card_already_added = any(
                        c.get('id') == card.id and c.get('bank') == bank.name 
                        for c in all_entities_map[entity_id]['cards']
                    )
                    if not card_already_added:
                        all_entities_map[entity_id]['cards'].append({
                            'id': card.id,
                            'name': card.name,
                            'bank': bank.name
                        })
                    
                    # Get deals for this entity and card (SAME logic as get_entities_by_card)
                    if PeekabooDeal:
                        entity_deals = PeekabooDeal.objects.filter(
                            raw_entity_id=entity_id,
                            bank=bank,
                            linked_cards=card,
                            is_expired=False,
                            is_active=True
                        ).distinct()
                        
                        # If no deals found via linked_cards, try associations JSON (SAME as get_entities_by_card)
                        if entity_deals.count() == 0:
                            all_deals = PeekabooDeal.objects.filter(
                                raw_entity_id=entity_id,
                                bank=bank,
                                is_expired=False,
                                is_active=True
                            )
                            matching_deals = []
                            for deal in all_deals:
                                if deal.associations:
                                    for assoc in deal.associations:
                                        if isinstance(assoc, dict):
                                            assoc_type_id = assoc.get('typeId')
                                            if assoc_type_id and card.peekaboo_association_type_id and assoc_type_id == card.peekaboo_association_type_id:
                                                matching_deals.append(deal)
                                                break
                            entity_deals = matching_deals
                        
                        # Add deals to entity (deduplicate by deal.id)
                        existing_deal_ids = {d.get('id') for d in all_entities_map[entity_id]['deals']}
                        for deal in entity_deals:
                            if deal.id not in existing_deal_ids:
                                # Get card and bank info for this deal
                                deal_cards = list(deal.linked_cards.all())
                                deal_card_info = []
                                for dc in deal_cards:
                                    deal_card_info.append({
                                        'id': dc.id,
                                        'name': dc.name,
                                        'bank': dc.bank.name if dc.bank else None,
                                        'bank_id': dc.bank.id if dc.bank else None,
                                    })
                                
                                all_entities_map[entity_id]['deals'].append({
                                    'id': deal.id,
                                    'deal_id': deal.deal_id,
                                    'title': deal.title,
                                    'description': deal.description,
                                    'percentage_value': float(deal.percentage_value) if deal.percentage_value else None,
                                    'start_date': deal.start_date.isoformat() if deal.start_date else None,
                                    'end_date': deal.end_date.isoformat() if deal.end_date else None,
                                    'target_entity_name': deal.target_entity_name,
                                    'target_entity_logo': deal.target_entity_logo,
                                    'target_branches': deal.target_branches if hasattr(deal, 'target_branches') else {},
                                    'associations': deal.associations if hasattr(deal, 'associations') else [],
                                    'is_currently_valid': deal.is_currently_valid if hasattr(deal, 'is_currently_valid') else True,
                                    'days_remaining': deal.days_remaining if hasattr(deal, 'days_remaining') else None,
                                    'image': deal.image if hasattr(deal, 'image') else None,
                                    # Add card and bank info
                                    'cards': deal_card_info,
                                    'bank': {
                                        'id': bank.id,
                                        'name': bank.name,
                                        'code': bank.code,
                                    } if bank else None,
                                })
                                existing_deal_ids.add(deal.id)
                        
                        # Update deal count (total count from ALL cards/banks for this entity)
                        all_entities_map[entity_id]['deal_count'] = len(all_entities_map[entity_id]['deals'])
                        
        except Exception as e:
            logger.error(f"   ❌ AUTO: Error scraping entities for {card.name} (Bank: {bank.name}): {str(e)}")
            import traceback
            logger.error(f"   Traceback: {traceback.format_exc()}")
            continue
    
    # After processing all cards, ensure all entities have accurate deal counts
    # This handles cases where the same entity appears for multiple cards from different banks
    logger.info(f"✅ AUTO: Processed {len(all_entities_map)} unique entities from {user_cards.count()} cards")
    
    # Log summary of entities and their associated cards
    for entity_id, entity_data in all_entities_map.items():
        cards_count = len(entity_data.get('cards', []))
        deals_count = entity_data.get('deal_count', 0)
        entity_name = entity_data.get('name', 'Unknown')
        logger.info(f"   📊 Entity {entity_id} ({entity_name}): {cards_count} cards, {deals_count} deals")
    
    # Convert map to list
    all_entities = list(all_entities_map.values())
    
    # Limit deals to 5 per entity for display (SAME as get_entities_by_card)
    for entity in all_entities:
        if entity.get('deals'):
            entity['deals'] = entity['deals'][:5]
    
    # Apply sorting (SAME as get_entities_by_card)
    if sort_by == 'rating':
        all_entities.sort(key=lambda x: x.get('rating', 0) or 0, reverse=True)
    elif sort_by == 'name':
        all_entities.sort(key=lambda x: x.get('name', '').lower())
    elif sort_by == 'deals':
        all_entities.sort(key=lambda x: x.get('deal_count', 0), reverse=True)
    # Default is 'trending' - keep original order
    
    # Apply pagination
    paginated_entities = all_entities[offset:offset + limit]
    has_next = (offset + limit) < len(all_entities)
    
    logger.info(f"✅ AUTO: Returning {len(paginated_entities)} entities (total: {len(all_entities)}) for user's cards")
    
    return Response({
        'entities': paginated_entities,
        'total': len(all_entities),
        'nextPage': has_next,
        'limit': limit,
        'offset': offset,
    })

