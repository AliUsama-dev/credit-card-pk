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
        
        # NOTE: Peekaboo offers removed - only showing Partners offers as requested

        # Partners offers: best discount_percentage per credit_card_id + count
        # IMPORTANT: ONLY show deals for the selected category (no fallback to all offers)
        # Use available_on_cards ManyToMany field if it exists, otherwise fallback to partner_card__credit_card_id
        from django.core.exceptions import FieldError
        try:
            # Try to use available_on_cards for more accurate filtering
            # Find PartnerCards linked to user's CreditCards
            from offers.models_partners import PartnerCard
            partner_card_ids = list(
                PartnerCard.objects.filter(
                    credit_card_id__in=card_ids,
                    is_active=True
                ).values_list('id', flat=True)
            )
            
            if partner_card_ids:
                # Filter offers where user's cards are in available_on_cards
                partners_base_qs = PartnerOffer.objects.filter(
                    is_active=True,
                    is_expired=False,
                    available_on_cards__id__in=partner_card_ids,
                ).distinct()
            else:
                # Fallback to partner_card__credit_card_id if no PartnerCards found
                partners_base_qs = PartnerOffer.objects.filter(
                    is_active=True,
                    is_expired=False,
                    partner_card__credit_card_id__in=card_ids,
                )
        except (FieldError, AttributeError):
            # available_on_cards field doesn't exist yet (migrations not run)
            # Fallback to partner_card__credit_card_id
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
        
        # CRITICAL: Count offers per card using ONLY available_on_cards (associations array)
        # NO FALLBACK - only count offers where card is explicitly in associations
        try:
            from offers.models_partners import PartnerCard
            for cid in card_ids:
                # Find PartnerCard(s) linked to this CreditCard
                partner_cards = PartnerCard.objects.filter(
                    credit_card_id=cid,
                    is_active=True
                )
                partner_card_ids = list(partner_cards.values_list('id', flat=True))
                
                # CRITICAL: Only count if PartnerCards found (can verify associations)
                if partner_card_ids:
                    # Filter offers where this card is in available_on_cards (associations array)
                    card_offers = partners_qs.filter(available_on_cards__id__in=partner_card_ids).distinct()
                    partners_count_by_card[cid] = card_offers.count()
                    # Get best discount percentage for this card
                    best_pct = card_offers.aggregate(best=Max("discount_percentage")).get("best")
                    if best_pct:
                        partners_best_by_card[cid] = _safe_float(best_pct)
                else:
                    # No PartnerCards found - can't verify associations, set to 0
                    partners_count_by_card[cid] = 0
                    partners_best_by_card[cid] = 0.0
        except (FieldError, AttributeError):
            # available_on_cards field doesn't exist - can't verify associations, set all to 0
            for cid in card_ids:
                partners_count_by_card[cid] = 0
                partners_best_by_card[cid] = 0.0

        def _peekaboo_top_offers_for_card(card_id: int) -> List[Dict[str, Any]]:
            # NOTE: Peekaboo offers removed - always return empty
            return []

        def _partners_top_offers_for_card(card_id: int) -> List[Dict[str, Any]]:
            # CRITICAL: Only show offers where this card is EXPLICITLY in the associations array
            # This means the card must be in available_on_cards ManyToMany field
            # Filter by card_id and ensure card_id is in user's card_ids
            if card_id not in card_ids:
                return []  # Not a user's card, return empty
            
            # Find PartnerCard(s) linked to this CreditCard
            from offers.models_partners import PartnerCard
            partner_cards = PartnerCard.objects.filter(
                credit_card_id=card_id,
                is_active=True
            )
            partner_card_ids = list(partner_cards.values_list('id', flat=True))
            
            # CRITICAL: If no PartnerCards found, return empty (can't verify associations)
            if not partner_card_ids:
                return []  # No PartnerCards found - can't verify if card is in associations
            
            # STRICT FILTERING: Only show offers where this card is in available_on_cards (associations array)
            # NO FALLBACK - if available_on_cards doesn't exist or is empty, return empty
            try:
                # Filter offers where this card's PartnerCard(s) are in available_on_cards
                qs = (
                    partners_qs.filter(available_on_cards__id__in=partner_card_ids)
                    .prefetch_related('available_on_cards')
                    .distinct()
                    .order_by("-discount_percentage", "-valid_to", "-id")
                )
            except (FieldError, AttributeError):
                # available_on_cards field doesn't exist - return empty (can't verify associations)
                return []
            
            # CRITICAL: Additional verification - ensure each offer actually has this card in available_on_cards
            # This double-checks that the offer is in the associations array for this card
            verified_offers = []
            seen_offers = set()  # Track seen offers to prevent duplicates
            
            for o in qs[:20]:  # Get more to filter and deduplicate
                # STRICT VERIFICATION: Only include if this card is explicitly in available_on_cards
                is_linked = False
                try:
                    if hasattr(o, 'available_on_cards'):
                        # Check if any of the card's PartnerCards are in available_on_cards
                        offer_card_ids = list(o.available_on_cards.filter(id__in=partner_card_ids).values_list('id', flat=True))
                        is_linked = len(offer_card_ids) > 0
                except (AttributeError, Exception):
                    # If we can't verify, skip this offer (safety first)
                    continue
                
                # CRITICAL: If not linked via available_on_cards, skip (NO FALLBACK)
                if not is_linked:
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
            part_pct = partners_best_by_card.get(card.id, 0.0)
            part_cnt = partners_count_by_card.get(card.id, 0)

            # Pakistan-focused scoring (Partners offers only):
            # - Primary: best % OFF from Partners
            # - Secondary: number of active Partners offers found (small boost)
            # We intentionally DO NOT rely on points/cashback as users requested.
            best_offer_pct = part_pct
            score = best_offer_pct + (min(part_cnt, 20) * 0.05)

            reasons: List[str] = []
            if best_offer_pct > 0:
                if category:
                    reasons.append(f"Best {category} deal: {best_offer_pct:.0f}% OFF (Partners)")
                else:
                    reasons.append(f"Best deal: {best_offer_pct:.0f}% OFF (Partners)")
            if part_cnt:
                if category:
                    reasons.append(f"Active {category} offers: {part_cnt} Partners")
                else:
                    reasons.append(f"Active offers: {part_cnt} Partners")
            if not reasons:
                reasons.append("No specific offers found for this category, but it's an active card.")

            # Attach top offers so UI can show "brands/deals like Partners Offers"
            # Only show Partners offers (Peekaboo removed)
            all_offers = _partners_top_offers_for_card(card.id)
            
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
                    peekaboo_best_pct=0.0,  # Always 0 - Peekaboo removed
                    partners_best_pct=part_pct,
                    peekaboo_offer_count=0,  # Always 0 - Peekaboo removed
                    partners_offer_count=part_cnt,
                    top_offers=top_offers,
                    score=score,
                    reasons=reasons,
                )
            )

        scored.sort(key=lambda x: (x.score, x.partners_best_pct), reverse=True)
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
                    "peekaboo_best_offer_pct": 0,  # Always 0 - Peekaboo removed
                    "partners_best_offer_pct": cs.partners_best_pct,
                    "peekaboo_offer_count": 0,  # Always 0 - Peekaboo removed
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

