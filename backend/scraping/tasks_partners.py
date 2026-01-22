# scraping/tasks_partners.py
# Celery tasks for scraping Peekaboo Partners Offers

import logging
import time
from celery import shared_task
from django.utils import timezone
from django.db import transaction
from django.db.utils import OperationalError
from django.db import connection
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
            
            # Process offers for this card (only offers linked to this card)
            card_offers = [
                o for o in bank_data.get('offers', [])
                if o.get('card_name') == card_data['name'] or o.get('card_slug') == card_data.get('slug')
            ]
            
            # Process offers in batches to avoid long transactions
            for offer_idx, offer_data in enumerate(card_offers):
                try:
                    # NOTE: Avoid fixed sleeps; rely on retry/backoff when locks happen.
                    
                    def _process_offer():
                        with transaction.atomic():
                            # Use source_url as primary identifier if available, otherwise use title + merchant
                            lookup_kwargs = {
                                'partner_bank': partner_bank,
                                'partner_card': partner_card,
                            }
                            
                            if offer_data.get('source_url'):
                                lookup_kwargs['source_url'] = offer_data['source_url']
                            else:
                                lookup_kwargs['title'] = offer_data['title']
                                lookup_kwargs['merchant_name'] = offer_data.get('merchant_name', '')[:200]
                            
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
                            
                            return created
                    
                    offer_created = _retry_db_operation(_process_offer)
                    
                    if offer_created:
                        offers_created += 1
                    else:
                        offers_updated += 1
                        
                except Exception as e:
                    logger.error(f"Error processing offer: {str(e)}")
                    continue
                
        except Exception as e:
            logger.error(f"Error processing card {card_data.get('name', 'Unknown')}: {str(e)}")
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
