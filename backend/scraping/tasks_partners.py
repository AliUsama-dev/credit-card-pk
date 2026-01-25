# scraping/tasks_partners.py
# Celery tasks for scraping Peekaboo Partners Offers

import logging
import time
from celery import shared_task
from django.utils import timezone
from django.db import transaction
from django.db.utils import OperationalError
from django.db import connection
from django.db.models import Q
from cards.models import Bank, CreditCard
from offers.models_partners import PartnerBank, PartnerCard, PartnerOffer
from .scrapers.partners_scraper import PartnersOffersScraper

logger = logging.getLogger(__name__)

def _is_sqlite() -> bool:
    try:
        return connection.vendor == "sqlite"
    except Exception:
        return False

def _retry_db_operation(func, max_retries=5, initial_delay=0.1):
    """
    Retry a database operation with exponential backoff to handle SQLite lock errors.
    
    Args:
        func: Function to execute (should be a lambda or callable)
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds before retry
    
    Returns:
        Result of the function call
    """
    retry_count = 0
    delay = initial_delay
    
    while retry_count < max_retries:
        try:
            return func()
        except OperationalError as e:
            error_msg = str(e).lower()
            if 'database is locked' in error_msg or 'locked' in error_msg:
                retry_count += 1
                if retry_count < max_retries:
                    # Exponential backoff with jitter
                    wait_time = delay * (2 ** retry_count) + (retry_count * 0.05)
                    wait_time = min(wait_time, 2.0)  # Cap at 2 seconds
                    logger.debug(f"Database locked, retrying ({retry_count}/{max_retries}) after {wait_time:.2f}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"Database locked after {max_retries} retries: {str(e)}")
                    raise
            else:
                # Not a lock error, re-raise
                raise
        except Exception as e:
            # Other errors, re-raise immediately
            raise

def _ensure_bank_for_partner(bank_name: str, slug: str, website: str | None = None) -> Bank:
    """
    Ensure we have a real `cards.Bank` row for a partner bank.
    After `flush_db`, there may be no banks at all, so the Add New Card dropdown would be empty.
    """
    # Make a stable-ish code from slug (bank.code is unique)
    code = (slug or bank_name or "UNKNOWN").upper().replace("-", "_")[:50] or "UNKNOWN"
    website = website or "https://peekaboo.guru"

    bank, _created = Bank.objects.get_or_create(
        code=code,
        defaults={
            "name": bank_name[:255] if bank_name else code,
            "country": "PK",
            "bank_type": "COMMERCIAL",
            "website": website,
            "support_email": "support@peekaboo.guru",
            "support_phone": "N/A",
            "is_active": True,
        },
    )

    # If the bank exists but has empty required fields (legacy rows), patch them.
    changed = False
    if not bank.name:
        bank.name = bank_name[:255] if bank_name else code
        changed = True
    if not bank.website:
        bank.website = website
        changed = True
    if not bank.support_email:
        bank.support_email = "support@peekaboo.guru"
        changed = True
    if not bank.support_phone:
        bank.support_phone = "N/A"
        changed = True
    if not bank.is_active:
        bank.is_active = True
        changed = True
    if changed:
        bank.save(update_fields=["name", "website", "support_email", "support_phone", "is_active"])

    return bank

@shared_task
def scrape_partners_banks(city: str = 'karachi'):
    """Scrape all partner banks from Peekaboo city page"""
    scraper = PartnersOffersScraper()
    banks_data = scraper.get_all_partner_banks(city)
    
    created_count = 0
    updated_count = 0
    
    with transaction.atomic():
        for bank_data in banks_data:
            try:
                # Ensure we have a real Bank row (critical after flush_db)
                matching_bank = _ensure_bank_for_partner(
                    bank_name=bank_data.get("name", "") or "",
                    slug=bank_data.get("slug", "") or "",
                    website=bank_data.get("website"),
                )
                
                # Create or update PartnerBank
                partner_bank, created = PartnerBank.objects.update_or_create(
                    peekaboo_entity_id=bank_data['entity_id'],
                    defaults={
                        'peekaboo_slug': bank_data['slug'],
                        'name': bank_data['name'],
                        'bank': matching_bank,
                        'last_scraped_at': timezone.now(),
                    }
                )
                
                if created:
                    created_count += 1
                else:
                    updated_count += 1
                
                # Avoid spamming terminal when refreshing the banks list
                logger.debug(f"{'Created' if created else 'Updated'} partner bank: {partner_bank.name}")
                
            except Exception as e:
                logger.error(f"Error processing partner bank {bank_data.get('name', 'Unknown')}: {str(e)}")
                continue
    
    logger.info(f"Scraped {len(banks_data)} partner banks: {created_count} created, {updated_count} updated")
    return {
        'total': len(banks_data),
        'created': created_count,
        'updated': updated_count,
    }

@shared_task
def scrape_partner_bank_detail(partner_bank_id: int, city: str = 'karachi'):
    """Scrape detailed information for a specific partner bank"""
    try:
        partner_bank = PartnerBank.objects.get(id=partner_bank_id)
    except PartnerBank.DoesNotExist:
        logger.error(f"Partner bank {partner_bank_id} not found")
        return {'error': 'Partner bank not found'}
    
    scraper = PartnersOffersScraper()
    bank_data = scraper.scrape_bank_detail(
        partner_bank.peekaboo_entity_id,
        partner_bank.peekaboo_slug,
        city
    )
    
    if not bank_data:
        return {'error': 'Failed to scrape bank detail'}
    
    cards_created = 0
    cards_updated = 0
    offers_created = 0
    offers_updated = 0
    
    # Update partner bank info (separate transaction to avoid long locks)
    def _update_partner_bank():
        with transaction.atomic():
            partner_bank.name = bank_data.get('name', partner_bank.name)
            partner_bank.description = bank_data.get('description', partner_bank.description)
            partner_bank.logo = bank_data.get('logo', partner_bank.logo)
            partner_bank.last_scraped_at = timezone.now()

            # Ensure linked real bank exists (critical after flush_db)
            if not partner_bank.bank:
                partner_bank.bank = _ensure_bank_for_partner(
                    bank_name=partner_bank.name,
                    slug=partner_bank.peekaboo_slug,
                    website=bank_data.get("website"),
                )

            partner_bank.save()
    
    _retry_db_operation(_update_partner_bank)
    
    # Process cards - each card in its own transaction to avoid long locks
    for idx, card_data in enumerate(bank_data.get('cards', [])):
        try:
            # NOTE: Avoid fixed sleeps; rely on retry/backoff when locks happen.
            # Keeping scraping fast on Postgres/MySQL, and acceptable on SQLite.
            
            def _process_card():
                with transaction.atomic():
                    # Ensure a real CreditCard exists for this partner card, linked to the real bank.
                    credit_card = None
                    if partner_bank.bank:
                        credit_card, _cc_created = CreditCard.objects.get_or_create(
                            bank=partner_bank.bank,
                            name=card_data["name"][:255],
                            defaults={
                                "card_type": card_data.get("card_type", "CREDIT") or "CREDIT",
                                "annual_fee": 0,
                                "is_active": True,
                                "peekaboo_association_type_id": card_data.get("association_type_id"),
                                "peekaboo_card_slug": card_data.get("slug"),
                            },
                        )
                        # Keep peekaboo mapping fresh
                        updated_fields = []
                        if card_data.get("association_type_id") and not credit_card.peekaboo_association_type_id:
                            credit_card.peekaboo_association_type_id = card_data.get("association_type_id")
                            updated_fields.append("peekaboo_association_type_id")
                        if card_data.get("slug") and not credit_card.peekaboo_card_slug:
                            credit_card.peekaboo_card_slug = card_data.get("slug")
                            updated_fields.append("peekaboo_card_slug")
                        if updated_fields:
                            credit_card.save(update_fields=updated_fields)
                    
                    partner_card, created = PartnerCard.objects.update_or_create(
                        partner_bank=partner_bank,
                        name=card_data['name'],
                        defaults={
                            'slug': card_data.get('slug', ''),
                            'description': card_data.get('description', ''),
                            'image': card_data.get('image', ''),
                            'card_type': card_data.get('card_type', 'CREDIT'),
                            'credit_card': credit_card,
                            'last_scraped_at': timezone.now(),
                        }
                    )
                    
                    return partner_card, created
            
            partner_card, card_created = _retry_db_operation(_process_card)
            
            if card_created:
                cards_created += 1
            else:
                cards_updated += 1
                
        except Exception as e:
            logger.error(f"Error processing card {card_data.get('name', 'Unknown')}: {str(e)}")
            continue
    
    # CRITICAL: Process ALL offers from the bank (not per card)
    # Each offer should be linked to ALL cards in its associations array
    # This ensures when user selects a card, only offers with that card in associations are shown
    logger.info(f"Processing {len(bank_data.get('offers', []))} offers for {partner_bank.name}...")
    
    # Deduplicate offers by deal_id (same deal can appear in multiple card scrapes)
    offers_by_deal_id = {}
    for offer_data in bank_data.get('offers', []):
        deal_id = offer_data.get('deal_id')
        if deal_id:
            # Use deal_id as key - same deal should only be stored once
            if deal_id not in offers_by_deal_id:
                offers_by_deal_id[deal_id] = offer_data
            else:
                # Merge associations if deal already exists
                existing = offers_by_deal_id[deal_id]
                existing_associations = existing.get('available_on_associations', [])
                new_associations = offer_data.get('available_on_associations', [])
                # Combine unique associations
                all_associations = existing_associations + new_associations
                # Deduplicate by typeId
                seen_type_ids = set()
                unique_associations = []
                for assoc in all_associations:
                    type_id = assoc.get('typeId')
                    if type_id and type_id not in seen_type_ids:
                        seen_type_ids.add(type_id)
                        unique_associations.append(assoc)
                existing['available_on_associations'] = unique_associations
                # Update card names/typeIds/slugs from unique associations
                existing['available_on_card_names'] = [a.get('name') for a in unique_associations if a.get('name')]
                existing['available_on_card_type_ids'] = [a.get('typeId') for a in unique_associations if a.get('typeId')]
                existing['available_on_card_slugs'] = [a.get('slug') for a in unique_associations if a.get('slug')]
        else:
            # No deal_id - use source_url as key
            source_url = offer_data.get('source_url', '')
            if source_url and source_url not in offers_by_deal_id:
                offers_by_deal_id[source_url] = offer_data
    
    # Process each unique offer
    for offer_key, offer_data in offers_by_deal_id.items():
        try:
            def _process_offer():
                with transaction.atomic():
                    # Find ALL PartnerCards that match cards in this offer's associations array
                    available_on_card_names = offer_data.get('available_on_card_names', [])
                    available_on_card_type_ids = offer_data.get('available_on_card_type_ids', [])
                    available_on_card_slugs = offer_data.get('available_on_card_slugs', [])
                    
                    # Find matching PartnerCards by name, typeId, or slug
                    matching_partner_cards = PartnerCard.objects.filter(
                        partner_bank=partner_bank,
                        is_active=True
                    ).filter(
                        Q(name__in=available_on_card_names) |
                        Q(peekaboo_association_type_id__in=available_on_card_type_ids) |
                        Q(slug__in=available_on_card_slugs)
                    ).distinct()
                    
                    # If no matches found, try to match by the card_name from offer (backward compatibility)
                    if not matching_partner_cards.exists():
                        card_name = offer_data.get('card_name')
                        if card_name:
                            matching_partner_cards = PartnerCard.objects.filter(
                                partner_bank=partner_bank,
                                name=card_name,
                                is_active=True
                            )
                    
                    # Use first matching card as default partner_card (for backward compatibility)
                    default_partner_card = matching_partner_cards.first()
                    
                    # Use deal_id or source_url as primary identifier
                    lookup_kwargs = {
                        'partner_bank': partner_bank,
                    }
                    
                    deal_id = offer_data.get('deal_id')
                    if deal_id:
                        # Extract dealId from source_url if not in offer_data
                        source_url = offer_data.get('source_url', '')
                        if source_url and 'dealId=' in source_url:
                            import re
                            match = re.search(r'dealId=([^&]+)', source_url)
                            if match:
                                deal_id_from_url = match.group(1).strip()
                                if deal_id_from_url:
                                    lookup_kwargs['source_url__icontains'] = f'dealId={deal_id_from_url}'
                    elif offer_data.get('source_url'):
                        lookup_kwargs['source_url'] = offer_data['source_url']
                    else:
                        lookup_kwargs['title'] = offer_data['title']
                        lookup_kwargs['merchant_name'] = offer_data.get('merchant_name', '')[:200]
                    
                    # Add default partner_card to lookup if available
                    if default_partner_card:
                        lookup_kwargs['partner_card'] = default_partner_card
                    
                    partner_offer, created = PartnerOffer.objects.update_or_create(
                        **lookup_kwargs,
                        defaults={
                            'title': offer_data['title'],
                            'description': offer_data.get('description', ''),
                            'discount_percentage': offer_data.get('discount_percentage'),
                            'discount_amount': offer_data.get('discount_amount'),
                            'merchant_name': offer_data.get('merchant_name', '')[:200],
                            'merchant_logo': offer_data.get('merchant_logo', ''),
                            'image': offer_data.get('image', ''),
                            'category': offer_data.get('category', ''),
                            'city': city.upper(),
                            'source_url': offer_data.get('source_url', ''),
                            'terms_conditions': offer_data.get('terms_conditions', ''),
                            'last_scraped_at': timezone.now(),
                        }
                    )
                    
                    # CRITICAL: Link offer to ALL cards in associations array via available_on_cards ManyToMany
                    try:
                        if hasattr(PartnerOffer, 'available_on_cards'):
                            # Clear existing associations and set new ones
                            partner_offer.available_on_cards.clear()
                            if matching_partner_cards.exists():
                                partner_offer.available_on_cards.set(matching_partner_cards)
                                logger.debug(f"Linked offer '{offer_data.get('title', '')[:50]}' to {matching_partner_cards.count()} cards via associations")
                            else:
                                # Fallback: if no matches found, link to default card if available
                                if default_partner_card:
                                    partner_offer.available_on_cards.add(default_partner_card)
                                    logger.debug(f"Linked offer '{offer_data.get('title', '')[:50]}' to default card '{default_partner_card.name}'")
                    except (AttributeError, Exception) as e:
                        logger.warning(f"Could not set available_on_cards for offer: {str(e)}")
                    
                    return created
            
            offer_created = _retry_db_operation(_process_offer)
            
            if offer_created:
                offers_created += 1
            else:
                offers_updated += 1
                
        except Exception as e:
            logger.error(f"Error processing offer: {str(e)}")
            continue
    
    logger.info(f"Scraped {partner_bank.name}: {cards_created} cards created, {cards_updated} updated, "
                f"{offers_created} offers created, {offers_updated} updated")
    
    return {
        'bank': partner_bank.name,
        'cards_created': cards_created,
        'cards_updated': cards_updated,
        'offers_created': offers_created,
        'offers_updated': offers_updated,
    }

@shared_task
def scrape_all_partners_banks(city: str = 'karachi'):
    """Scrape all partner banks and their details"""
    logger.info(f"🚀 Starting to scrape ALL partner banks in {city}...")
    
    # First, get all partner banks
    logger.info("📋 Step 1: Fetching list of all partner banks...")
    scrape_result = scrape_partners_banks(city)
    
    if 'error' in scrape_result:
        logger.error(f"❌ Failed to fetch partner banks list: {scrape_result.get('error')}")
        return scrape_result
    
    logger.info(f"✅ Found {scrape_result.get('total', 0)} partner banks")
    
    # Then scrape details for each bank
    partner_banks = PartnerBank.objects.filter(is_active=True)
    total_banks = partner_banks.count()
    logger.info(f"📊 Step 2: Scraping details for {total_banks} partner banks...")
    
    total_results = {
        'banks_scraped': 0,
        'total_cards_created': 0,
        'total_cards_updated': 0,
        'total_offers_created': 0,
        'total_offers_updated': 0,
    }
    
    for idx, partner_bank in enumerate(partner_banks, 1):
        try:
            # Avoid fixed delays; if SQLite is in use, keep a tiny delay to reduce lock churn.
            if _is_sqlite() and idx > 1:
                time.sleep(0.05)
            
            logger.info(f"📊 [{idx}/{total_banks}] Scraping {partner_bank.name}...")
            result = scrape_partner_bank_detail(partner_bank.id, city)
            if 'error' not in result:
                total_results['banks_scraped'] += 1
                total_results['total_cards_created'] += result.get('cards_created', 0)
                total_results['total_cards_updated'] += result.get('cards_updated', 0)
                total_results['total_offers_created'] += result.get('offers_created', 0)
                total_results['total_offers_updated'] += result.get('offers_updated', 0)
                logger.info(f"   ✅ Completed {partner_bank.name}: {result.get('cards_created', 0)} cards created, {result.get('offers_created', 0)} offers created")
            else:
                logger.warning(f"   ⚠️  {partner_bank.name}: {result.get('error', 'Unknown error')}")
        except Exception as e:
            logger.error(f"   ❌ Error scraping {partner_bank.name}: {str(e)}", exc_info=True)
            continue
    
    logger.info(f"🎉 COMPLETE: Scraped {total_results['banks_scraped']} banks. "
                f"Total: {total_results['total_cards_created']} cards created, {total_results['total_cards_updated']} cards updated, "
                f"{total_results['total_offers_created']} offers created, {total_results['total_offers_updated']} offers updated")
    
    return total_results
