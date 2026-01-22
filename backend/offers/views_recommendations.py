from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import re

from django.db.models import Max, Q
from django.utils import timezone
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

import logging

logger = logging.getLogger(__name__)


# User-facing categories (Peekaboo-like)
UI_CATEGORIES: List[str] = [
    "Food",
    "Lifestyle",
    "Health",
    "Entertainment",
    "E-Stores",
    "Education",
    "Home Décor",
    "Services",
    "Electronics",
    "Self-Care",
    "Public Services",
    "Hotels",
    "Grocery",
]


# Map UI category -> internal CardRewardCategory.category choices
UI_TO_REWARD_CATEGORY: Dict[str, str] = {
    "Food": "DINING",
    "Grocery": "GROCERIES",
    "Entertainment": "ENTERTAINMENT",
    "E-Stores": "ONLINE_SHOPPING",
    "Hotels": "TRAVEL",
    "Public Services": "UTILITIES",
    "Services": "OTHER",
    "Lifestyle": "OTHER",
    "Health": "OTHER",
    "Education": "OTHER",
    "Home Décor": "SHOPPING",
    "Electronics": "SHOPPING",
    "Self-Care": "OTHER",
}

def _norm_cat(s: str) -> str:
    s = (s or "").strip().lower()
    # Normalize common punctuation/diacritics for matching
    s = s.replace("é", "e").replace("’", "'")
    s = s.replace("&", "and")
    # Collapse to alnum+space
    s = re.sub(r"[^a-z0-9]+", " ", s).strip()
    s = re.sub(r"\s+", " ", s)
    return s


def _category_variants(ui_category: str) -> List[str]:
    """
    Build robust match variants so that UI categories match Peekaboo/Partners stored categories:
    e.g. "E-Stores" -> ["e stores", "estores", "e store", "online shopping"]
    """
    base = _norm_cat(ui_category)
    variants = {base}
    variants.add(base.replace(" ", ""))  # lifestyle -> lifestyle, home decor -> homedecor
    if base.endswith("s"):
        variants.add(base[:-1])
    # Hand-tuned synonyms seen in Peekaboo/Partners content
    if base in {"e stores", "estores", "e store"}:
        variants.update({"online shopping", "online", "ecommerce", "e commerce", "ecommerce", "e-commerce"})
    if base in {"food"}:
        variants.update({"dining", "restaurant", "restaurants", "cafe", "cafes", "food & dining", "food and dining"})
    if base in {"grocery"}:
        variants.update({"groceries", "supermarket", "mart", "grocery store"})
    if base in {"home decor", "homedecor"}:
        variants.update({"home decor", "home decor", "decor", "furniture", "interiors"})
    if base in {"lifestyle"}:
        variants.update({"fashion", "beauty", "spa", "salon", "wellness"})
    if base in {"health"}:
        variants.update({"pharmacy", "hospital", "clinic", "medical", "healthcare"})
    if base in {"entertainment"}:
        variants.update({"cinema", "movies", "gaming", "amusement", "theater"})
    if base in {"electronics"}:
        variants.update({"gadgets", "mobile", "computer", "appliances", "tech"})
    if base in {"self care"}:
        variants.update({"wellness", "gym", "fitness", "yoga", "spa", "salon"})
    if base in {"hotels"}:
        variants.update({"travel", "accommodation", "resort", "hotel", "lodging"})
    return [v for v in variants if v]


def _category_q(field_name: str, ui_category: str) -> Q:
    """
    Build a Q that matches any variant against a text field (case-insensitive).
    """
    q = Q()
    for v in _category_variants(ui_category):
        q |= Q(**{f"{field_name}__icontains": v})
    return q


def _safe_float(v: Any) -> float:
    try:
        if v is None:
            return 0.0
        return float(v)
    except Exception:
        return 0.0


@dataclass
class CardScore:
    card_id: int
    card_name: str
    bank_id: int
    bank_name: str
    base_cashback: float
    base_rewards: float
    category_reward: float
    peekaboo_best_pct: float
    partners_best_pct: float
    peekaboo_offer_count: int
    partners_offer_count: int
    top_offers: List[Dict[str, Any]]
    score: float
    reasons: List[str]


class SmartRecommendationsView(APIView):
    """
    AI-powered (deterministic) recommendations: ranks ONLY user-owned cards for a given category.

    GET params:
      - category: one of UI_CATEGORIES
      - city: optional (e.g., LAHORE/KARACHI). If provided but no offers exist in that city,
              the partners endpoint already falls back to all cities; we mimic similar behavior for Peekaboo.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        category = (request.query_params.get("category") or "").strip()
        city = (request.query_params.get("city") or "").strip()
        city_upper = city.upper() if city else ""

        if not category:
            return Response(
                {"status": "error", "error": "category is required", "allowed_categories": UI_CATEGORIES},
                status=400,
            )
        if category not in UI_CATEGORIES:
            return Response(
                {"status": "error", "error": f"Invalid category '{category}'", "allowed_categories": UI_CATEGORIES},
                status=400,
            )

        # Import models lazily (keeps app boot resilient)
        from cards.models import CreditCard, UserCard
        from offers.models_peekaboo import PeekabooDeal
        from offers.models_partners import PartnerOffer

        # User cards
        user_cards_qs = (
            UserCard.objects.filter(user=request.user, is_active=True)
            .select_related("card", "card__bank")
        )
        card_ids = [uc.card_id for uc in user_cards_qs if uc.card_id]
        if not card_ids:
            return Response(
                {
                    "status": "success",
                    "category": category,
                    "city": city_upper or None,
                    "best": None,
                    "ranking": [],
                    "message": "User has no active cards.",
                }
            )

        cards = list(CreditCard.objects.filter(id__in=card_ids).select_related("bank"))
        
        # Peekaboo offers: best percentage_value per card + count
        # IMPORTANT: ONLY show deals for the selected category (no fallback to all offers)
        base_deal_filter = Q(is_active=True, is_expired=False) & Q(linked_cards__id__in=card_ids)
        
        # Apply category filter - REQUIRED, no fallback
        if category:
            category_filter = _category_q("category", category) | _category_q("title", category)
            peekaboo_qs = PeekabooDeal.objects.filter(base_deal_filter & category_filter).distinct()
        else:
            # Should not happen (category is required), but handle gracefully
            peekaboo_qs = PeekabooDeal.objects.none()
        
        # Apply city filter if provided
        if city_upper:
            if peekaboo_qs.filter(city__iexact=city_upper).exists():
                peekaboo_qs = peekaboo_qs.filter(city__iexact=city_upper)
            # Note: We don't fall back to all cities - only show deals for selected city if available

        peekaboo_best_by_card: Dict[int, float] = {}
        peekaboo_count_by_card: Dict[int, int] = {}
        # Aggregate max percentage per card
        for row in (
            peekaboo_qs.values("linked_cards__id")
            .annotate(best_pct=Max("percentage_value"))
        ):
            cid = row.get("linked_cards__id")
            if cid:
                peekaboo_best_by_card[int(cid)] = _safe_float(row.get("best_pct"))
        # Count per card
        for row in peekaboo_qs.values("linked_cards__id").annotate(cnt=Max("id")):
            # cheap way: we'll just compute counts via python below; keep DB load simple
            pass
        # python counts (safer because M2M can duplicate rows)
        for cid in card_ids:
            peekaboo_count_by_card[cid] = peekaboo_qs.filter(linked_cards__id=cid).distinct().count()

        # Partners offers: best discount_percentage per credit_card_id + count
        # IMPORTANT: ONLY show deals for the selected category (no fallback to all offers)
        partners_base_qs = PartnerOffer.objects.filter(
            is_active=True,
            is_expired=False,
            partner_card__credit_card_id__in=card_ids,
        )
        
        # Apply category filter - REQUIRED, no fallback
        if category:
            category_filter = _category_q("category", category) | _category_q("title", category) | _category_q("merchant_name", category)
            partners_qs = partners_base_qs.filter(category_filter)
        else:
            # Should not happen (category is required), but handle gracefully
            partners_qs = PartnerOffer.objects.none()
        
        # Apply city filter if provided
        if city_upper:
            if partners_qs.filter(city__iexact=city_upper).exists():
                partners_qs = partners_qs.filter(city__iexact=city_upper)
            # Note: We don't fall back to all cities - only show deals for selected city if available

        partners_best_by_card: Dict[int, float] = {}
        partners_count_by_card: Dict[int, int] = {}
        for row in (
            partners_qs.values("partner_card__credit_card_id")
            .annotate(best_pct=Max("discount_percentage"))
        ):
            cid = row.get("partner_card__credit_card_id")
            if cid:
                partners_best_by_card[int(cid)] = _safe_float(row.get("best_pct"))
        for cid in card_ids:
            partners_count_by_card[cid] = partners_qs.filter(partner_card__credit_card_id=cid).count()

        def _peekaboo_top_offers_for_card(card_id: int) -> List[Dict[str, Any]]:
            # CRITICAL: Only show deals that are ACTUALLY linked to this specific card
            # Filter by card_id and ensure card_id is in user's card_ids
            if card_id not in card_ids:
                return []  # Not a user's card, return empty
            
            # Filter deals to only those linked to this specific card
            # Use distinct() to avoid duplicates from M2M relationships
            qs = (
                peekaboo_qs.filter(linked_cards__id=card_id)
                .prefetch_related('linked_cards')  # Prefetch to avoid N+1 queries
                .order_by("-percentage_value", "-end_date")
                .distinct()
            )
            
            # Additional safety check: verify each deal is actually linked to this card
            # This prevents showing deals that might have been incorrectly included
            # Also deduplicate by merchant_name + discount_percentage to prevent showing same deal multiple times
            verified_deals = []
            seen_deals = set()  # Track seen deals to prevent duplicates
            
            for d in qs[:20]:  # Get more to filter and deduplicate
                try:
                    linked_card_ids = [c.id for c in d.linked_cards.all()] if hasattr(d, 'linked_cards') else []
                    if card_id not in linked_card_ids:
                        continue
                    
                    # Create deduplication key
                    merchant = (d.target_entity_name or d.title or "").strip().lower()
                    discount = _safe_float(d.percentage_value)
                    deal_category = (d.category or "").strip().lower()
                    
                    # Use deal_id if available for better deduplication
                    if d.deal_id:
                        dedup_key = f"deal_{d.deal_id}"
                    else:
                        dedup_key = f"{merchant}_{discount}_{deal_category}"
                    
                    # Only add if not seen before
                    if dedup_key not in seen_deals:
                        seen_deals.add(dedup_key)
                        verified_deals.append(d)
                    
                    if len(verified_deals) >= 6:
                        break
                except Exception:
                    # Skip deals that can't be verified
                    continue
            
            # Use verified and deduplicated deals
            deals_to_process = verified_deals
            
            # Get card info for URL generation
            card = next((c for c in cards if c.id == card_id), None)
            if not card:
                return []
            
            # Get bank info for URL generation
            bank = card.bank if card else None
            bank_code = bank.code.upper() if bank else None
            
            # Get bank slug and IDs from BANK_PEEKABOO_IDS
            try:
                from scraping.tasks_peekaboo import BANK_PEEKABOO_IDS, BANK_SLUG_MAP
                bank_info = BANK_PEEKABOO_IDS.get(bank_code, {}) if bank_code else {}
                source_entity_id = bank_info.get('sourceEntityId')
                entity_id = bank_info.get('entityId')
                bank_slug = BANK_SLUG_MAP.get(bank_code, bank.name.lower().replace(' ', '-') if bank else '') if bank_code else ''
            except ImportError:
                # Fallback if imports fail
                bank_info = {}
                source_entity_id = None
                entity_id = None
                bank_slug = bank.name.lower().replace(' ', '-') if bank else ''
            
            # Get card slug and associationTypeId
            card_slug = card.peekaboo_card_slug or card.name.lower().replace(' ', '-').replace('card', '').replace('debit', '').replace('credit', '').strip('-')
            association_type_id = card.peekaboo_association_type_id
            
            out: List[Dict[str, Any]] = []
            
            # If no associationTypeId, we can't build the URL properly, but still return deals
            if not association_type_id and not source_entity_id:
                # Still return deals but without proper URL
                for d in deals_to_process:
                    out.append(
                        {
                            "source": "PEEKABOO",
                            "title": d.title,
                            "merchant_name": d.target_entity_name,
                            "image": d.image or d.target_entity_logo,
                            "merchant_logo": d.target_entity_logo,
                            "discount_percentage": _safe_float(d.percentage_value),
                            "city": d.city,
                            "category": d.category,
                            "source_url": None,
                            "bank_name": bank.name if bank else None,
                            "card_name": card.name if card else None,
                        }
                    )
                return out
            
            # CRITICAL: Always use the recommended card's information for URL generation
            # Don't try to find a "matching" card from the deal - this ensures URLs always point to the recommended card
            # A deal can be linked to multiple cards, but we want to show it for the recommended card specifically
            for d in deals_to_process:
                # Always use the recommended card's info (card_id parameter)
                # This ensures all URLs are for the recommended card, not other cards linked to the same deal
                actual_card_slug = card_slug  # Always use recommended card's slug
                actual_association_type_id = association_type_id  # Always use recommended card's association type
                actual_card_name = card.name if card else None  # Always use recommended card's name
                
                # Try to get association ID (ai) from deal's associations JSON that matches our card
                # But still use the recommended card's slug and associationTypeId
                actual_ai = association_type_id  # Default to recommended card's association type
                
                # Try to find the association ID (ai) from deal's associations that matches our card
                if d.associations and isinstance(d.associations, list):
                    for assoc in d.associations:
                        if isinstance(assoc, dict):
                            assoc_type_id = assoc.get('typeId')
                            # Only use this association if it matches our recommended card's associationTypeId
                            if assoc_type_id == actual_association_type_id:
                                # Found matching association - use its associationId (ai) but keep our card's slug
                                actual_ai = assoc.get('associationId') or assoc.get('id') or actual_association_type_id
                                break
                
                # Generate Peekaboo URL matching the pattern:
                # /{city}/places/{categoryId}/{categorySlug}?ai={ai}&associationTypeId={associationTypeId}&card={cardSlug}&dealId={dealId}&discounts={bankSlug}&ei={entityId}&selfDeal=true&sourceEntityId={sourceEntityId}
                city_lower = (d.city or city_upper or 'karachi').lower()
                category_slug = (d.category or 'all').lower().replace(' ', '-').replace('&', 'and')
                category_id = '1'  # Default to 1 (Food), but we could map categories to IDs
                
                # Map common categories to Peekaboo category IDs
                category_id_map = {
                    'food': '1',
                    'lifestyle': '18',
                    'health': '2',
                    'entertainment': '3',
                    'e-stores': '4',
                    'education': '5',
                    'home-decor': '6',
                    'services': '7',
                    'electronics': '8',
                    'self-care': '9',
                    'public-services': '10',
                    'hotels': '11',
                    'grocery': '12',
                }
                category_id = category_id_map.get(category_slug, '_all')  # Use _all if category not found
                
                # Build URL parameters - ALWAYS use recommended card's info
                # This ensures URLs always point to the recommended card, not other cards
                url_params = {}
                if actual_ai:
                    url_params['ai'] = str(actual_ai)
                if actual_association_type_id:
                    url_params['associationTypeId'] = str(actual_association_type_id)
                if actual_card_slug:
                    url_params['card'] = actual_card_slug  # Always recommended card's slug
                if bank_slug:
                    url_params['discounts'] = bank_slug
                if entity_id:
                    url_params['ei'] = str(entity_id)
                url_params['selfDeal'] = 'true'
                if source_entity_id:
                    url_params['sourceEntityId'] = str(source_entity_id)
                
                # Add dealId if available
                if d.deal_id:
                    url_params['dealId'] = str(d.deal_id)
                
                # Build full URL - use _all/all if we don't have category info
                base_url = 'https://peekaboo.guru'
                if category_id == '_all' or not category_slug or category_slug == 'all':
                    url_path = f"/{city_lower}/places/_all/all"
                else:
                    url_path = f"/{city_lower}/places/{category_id}/{category_slug}"
                
                query_string = '&'.join([f"{k}={v}" for k, v in url_params.items() if v])
                source_url = f"{base_url}{url_path}?{query_string}" if query_string else None
                
                # If we still don't have a URL, create a basic one
                if not source_url and d.deal_id:
                    source_url = f"{base_url}/{city_lower}/places/_all/all?dealId={d.deal_id}"
                
                out.append(
                    {
                        "source": "PEEKABOO",
                        "title": d.title,
                        "merchant_name": d.target_entity_name,
                        "image": d.image or d.target_entity_logo,
                        "merchant_logo": d.target_entity_logo,
                        "discount_percentage": _safe_float(d.percentage_value),
                        "city": d.city,
                        "category": d.category,
                        "source_url": source_url,  # Always include URL (even if basic)
                        "bank_name": bank.name if bank else None,
                        "card_name": actual_card_name,  # Always use recommended card's name
                    }
                )
            return out

        def _partners_top_offers_for_card(card_id: int) -> List[Dict[str, Any]]:
            # CRITICAL: Only show offers that are ACTUALLY linked to this specific card
            # Filter by card_id and ensure card_id is in user's card_ids
            if card_id not in card_ids:
                return []  # Not a user's card, return empty
            
            qs = (
                partners_qs.filter(partner_card__credit_card_id=card_id)
                .order_by("-discount_percentage", "-valid_to", "-id")
            )
            
            # Additional safety check: verify each offer is actually linked to this card
            # This prevents showing offers that might have been incorrectly included
            # Also deduplicate by merchant_name + discount_percentage to prevent showing same offer multiple times
            verified_offers = []
            seen_offers = set()  # Track seen offers to prevent duplicates
            
            for o in qs[:20]:  # Get more to filter and deduplicate
                if not (o.partner_card and o.partner_card.credit_card_id == card_id):
                    continue
                
                # Create deduplication key
                merchant = (o.merchant_name or o.title or "").strip().lower()
                discount = _safe_float(o.discount_percentage)
                offer_category = (o.category or "").strip().lower()
                
                # Try to extract dealId from source_url for better deduplication
                deal_id = None
                if o.source_url and "dealId=" in o.source_url:
                    try:
                        deal_id = o.source_url.split("dealId=")[1].split("&")[0].split("#")[0].strip()
                    except:
                        pass
                
                # Use deal_id if available for better deduplication
                if deal_id:
                    dedup_key = f"deal_{deal_id}"
                else:
                    dedup_key = f"{merchant}_{discount}_{offer_category}"
                
                # Only add if not seen before
                if dedup_key not in seen_offers:
                    seen_offers.add(dedup_key)
                    verified_offers.append(o)
                
                if len(verified_offers) >= 6:
                    break
            
            # Get card info for display and URL generation
            card = next((c for c in cards if c.id == card_id), None)
            bank = card.bank if card else None
            
            # Get bank slug and IDs for URL generation
            bank_code = bank.code.upper() if bank else None
            try:
                from scraping.tasks_peekaboo import BANK_PEEKABOO_IDS, BANK_SLUG_MAP
                bank_info = BANK_PEEKABOO_IDS.get(bank_code, {}) if bank_code else {}
                source_entity_id = bank_info.get('sourceEntityId')
                entity_id = bank_info.get('entityId')
                bank_slug = BANK_SLUG_MAP.get(bank_code, bank.name.lower().replace(' ', '-') if bank else '') if bank_code else ''
            except ImportError:
                bank_info = {}
                source_entity_id = None
                entity_id = None
                bank_slug = bank.name.lower().replace(' ', '-') if bank else ''
            
            # Get card slug and associationTypeId for URL generation
            card_slug = card.peekaboo_card_slug if card else None
            if not card_slug and card:
                card_slug = card.name.lower().replace(' ', '-').replace('card', '').replace('debit', '').replace('credit', '').strip('-')
            association_type_id = card.peekaboo_association_type_id if card else None
            
            out: List[Dict[str, Any]] = []
            for o in verified_offers:
                # CRITICAL: Regenerate URL to ensure it uses the recommended card's info
                # Don't use o.source_url directly - it might be for a different card
                source_url = o.source_url  # Default to original URL
                
                # Extract dealId from existing URL if available
                deal_id = None
                if o.source_url and 'dealId=' in o.source_url:
                    try:
                        deal_id = o.source_url.split('dealId=')[1].split('&')[0].split('#')[0]
                    except:
                        pass
                
                # Regenerate URL with recommended card's info
                if card_slug and bank_slug and association_type_id:
                    city_lower = (o.city or 'karachi').lower()
                    url_params = {
                        'ai': str(association_type_id) if association_type_id else '',
                        'associationTypeId': str(association_type_id) if association_type_id else '',
                        'card': card_slug,  # Always use recommended card's slug
                        'discounts': bank_slug,
                        'ei': str(entity_id) if entity_id else '',
                        'selfDeal': 'true',
                        'sourceEntityId': str(source_entity_id) if source_entity_id else '',
                    }
                    
                    if deal_id:
                        url_params['dealId'] = deal_id
                    
                    base_url = 'https://peekaboo.guru'
                    url_path = f"/{city_lower}/places/_all/all"
                    query_string = '&'.join([f"{k}={v}" for k, v in url_params.items() if v])
                    
                    if query_string:
                        source_url = f"{base_url}{url_path}?{query_string}"
                
                out.append(
                    {
                        "source": "PARTNERS",
                        "title": o.title,
                        "merchant_name": o.merchant_name,
                        "image": o.image or o.merchant_logo,
                        "merchant_logo": o.merchant_logo,
                        "discount_percentage": _safe_float(o.discount_percentage),
                        "city": o.city,
                        "category": o.category,
                        "source_url": source_url,  # Regenerated URL with recommended card's info
                        "bank_name": bank.name if bank else (o.partner_bank.name if hasattr(o, 'partner_bank') and o.partner_bank else None),
                        "card_name": card.name if card else None,  # Always use recommended card's name
                    }
                )
            return out

        # Score cards
        scored: List[CardScore] = []
        for card in cards:
            peek_pct = peekaboo_best_by_card.get(card.id, 0.0)
            part_pct = partners_best_by_card.get(card.id, 0.0)
            peek_cnt = peekaboo_count_by_card.get(card.id, 0)
            part_cnt = partners_count_by_card.get(card.id, 0)

            # Pakistan-focused scoring (offers first):
            # - Primary: best % OFF across Peekaboo + Partners
            # - Secondary: number of active offers found (small boost)
            # We intentionally DO NOT rely on points/cashback as users requested.
            best_offer_pct = max(peek_pct, part_pct)
            score = best_offer_pct + (min(peek_cnt + part_cnt, 20) * 0.05)

            reasons: List[str] = []
            if best_offer_pct > 0:
                source = "Peekaboo" if peek_pct >= part_pct else "Partners"
                if category:
                    reasons.append(f"Best {category} deal: {best_offer_pct:.0f}% OFF ({source})")
                else:
                    reasons.append(f"Best deal: {best_offer_pct:.0f}% OFF ({source})")
            if peek_cnt or part_cnt:
                if category:
                    reasons.append(f"Active {category} offers: {peek_cnt} Peekaboo, {part_cnt} Partners")
                else:
                    reasons.append(f"Active offers: {peek_cnt} Peekaboo, {part_cnt} Partners")
            if not reasons:
                reasons.append("No specific offers found for this category, but it's an active card.")

            # Attach top offers so UI can show "brands/deals like Partners Offers"
            # Combine Peekaboo and Partners offers
            all_offers = _partners_top_offers_for_card(card.id) + _peekaboo_top_offers_for_card(card.id)
            
            # CRITICAL: Deduplicate offers to prevent showing the same deal multiple times
            # Deduplicate by merchant_name + discount_percentage + category (or dealId if available)
            seen_offers = set()
            unique_offers = []
            
            for offer in all_offers:
                # Create a unique key for deduplication
                merchant = (offer.get("merchant_name") or offer.get("title") or "").strip().lower()
                discount = _safe_float(offer.get("discount_percentage", 0))
                offer_category = (offer.get("category") or "").strip().lower()
                
                # Try to extract dealId from source_url for better deduplication
                deal_id = None
                source_url = offer.get("source_url", "")
                if source_url and "dealId=" in source_url:
                    try:
                        deal_id = source_url.split("dealId=")[1].split("&")[0].split("#")[0].strip()
                    except:
                        pass
                
                # Create deduplication key - prefer dealId if available, otherwise use merchant+discount+category
                if deal_id:
                    dedup_key = f"{deal_id}_{merchant}_{discount}"
                else:
                    dedup_key = f"{merchant}_{discount}_{offer_category}"
                
                # Only add if we haven't seen this offer before
                if dedup_key not in seen_offers:
                    seen_offers.add(dedup_key)
                    unique_offers.append(offer)
                    
                    # Limit to 6 unique offers (not 8) to prevent duplicates
                    if len(unique_offers) >= 6:
                        break
            
            # Sort by discount percentage (highest first), then by source (Partners preferred)
            unique_offers.sort(key=lambda x: (_safe_float(x.get("discount_percentage", 0)), x.get("source") == "PARTNERS"), reverse=True)
            top_offers = unique_offers[:6]  # Limit to 6 unique offers

            scored.append(
                CardScore(
                    card_id=card.id,
                    card_name=card.name,
                    bank_id=card.bank_id,
                    bank_name=card.bank.name if card.bank else "",
                    base_cashback=0.0,
                    base_rewards=0.0,
                    category_reward=0.0,
                    peekaboo_best_pct=peek_pct,
                    partners_best_pct=part_pct,
                    peekaboo_offer_count=peek_cnt,
                    partners_offer_count=part_cnt,
                    top_offers=top_offers,
                    score=score,
                    reasons=reasons,
                )
            )

        scored.sort(key=lambda x: (x.score, x.partners_best_pct, x.peekaboo_best_pct), reverse=True)
        best = scored[0] if scored else None

        def _serialize(cs: CardScore) -> Dict[str, Any]:
            return {
                "card": {
                    "id": cs.card_id,
                    "name": cs.card_name,
                    "bank": {"id": cs.bank_id, "name": cs.bank_name},
                },
                "score": round(cs.score, 3),
                "metrics": {
                    "base_cashback_pct": cs.base_cashback,
                    "base_reward_points_rate": cs.base_rewards,
                    "category_reward_rate": cs.category_reward,
                    "peekaboo_best_offer_pct": cs.peekaboo_best_pct,
                    "partners_best_offer_pct": cs.partners_best_pct,
                    "peekaboo_offer_count": cs.peekaboo_offer_count,
                    "partners_offer_count": cs.partners_offer_count,
                },
                "top_offers": cs.top_offers,
                "reasons": cs.reasons,
            }

        return Response(
            {
                "status": "success",
                "category": category,
                "city": city_upper or None,
                "best": _serialize(best) if best else None,
                "ranking": [_serialize(cs) for cs in scored],
                "allowed_categories": UI_CATEGORIES,
            }
        )

