"""
Celery tasks for scraping Trinidad & Tobago banks credit cards
"""
import logging
from celery import shared_task
from django.db import transaction
from django.utils import timezone
from .scrapers.trinidad_tobago_bank_scraper import TrinidadTobagoBankScraper

logger = logging.getLogger(__name__)

from cards.models import Bank, CreditCard


@shared_task
def scrape_trinidad_tobago_bank(bank_code: str):
    """Scrape credit cards for a specific Trinidad & Tobago bank"""
    scraper = TrinidadTobagoBankScraper()
    bank_info = scraper.banks.get(bank_code)
    
    if not bank_info:
        logger.error(f"Bank not found: {bank_code}")
        return {'created': 0, 'updated': 0, 'error': f'Bank {bank_code} not found'}
    
    # Get or create bank in database
    try:
        bank, bank_created = Bank.objects.get_or_create(
            code=bank_code,
            defaults={
                'name': bank_info['name'],
                'bank_type': bank_info['type'],
                'country': 'TT',
                'website': bank_info['urls'][0] if bank_info['urls'] else '',
                'support_email': f'support@{bank_code.lower()}.com',
                'support_phone': '+1-868-XXX-XXXX',
                'is_active': True,
            }
        )
        
        if bank_created:
            logger.info(f"✅ Created bank: {bank.name}")
        else:
            Bank.objects.filter(code=bank_code).update(
                name=bank_info['name'],
                bank_type=bank_info['type'],
                country='TT',
                is_active=True,
            )
    except Exception as e:
        logger.error(f"Error creating/updating bank {bank_code}: {str(e)}")
        return {'created': 0, 'updated': 0, 'error': str(e)}
    
    # Scrape cards
    try:
        _, cards_data = scraper.scrape_bank(bank_code)
    except Exception as e:
        logger.error(f"Error scraping {bank_code}: {str(e)}")
        return {'created': 0, 'updated': 0, 'error': str(e)}
    
    if not cards_data:
        logger.warning(f"No cards found for {bank_code}")
        return {'created': 0, 'updated': 0, 'error': 'No cards found'}
    
    created_count = 0
    updated_count = 0
    
    with transaction.atomic():
        for card_data in cards_data:
            try:
                card_name = card_data.get('name', '').strip()
                if not card_name:
                    continue
                
                card_type = card_data.get('card_type', 'CREDIT')
                annual_fee = card_data.get('annual_fee') or 0.0
                cashback_rate = card_data.get('cashback_rate') or 0.0
                reward_points_rate = card_data.get('reward_points_rate') or 1.0
                
                card, card_created = CreditCard.objects.update_or_create(
                    bank=bank,
                    name=card_name,
                    defaults={
                        'card_type': card_type,
                        'annual_fee': annual_fee,
                        'cashback_rate': cashback_rate,
                        'reward_points_rate': reward_points_rate,
                        'welcome_bonus': card_data.get('welcome_bonus'),
                        'features': card_data.get('features'),
                        'requirements': card_data.get('requirements'),
                        'scraping_url': card_data.get('scraping_url'),
                        'image_url': card_data.get('image_url'),
                        'last_scraped': timezone.now(),
                        'is_active': True,
                    }
                )
                
                if card_created:
                    created_count += 1
                    logger.info(f"  ✅ Created card: {card.name}")
                else:
                    updated_count += 1
                    logger.info(f"  🔄 Updated card: {card.name}")
                    
            except Exception as e:
                logger.error(f"Error processing card {card_data.get('name', 'Unknown')}: {str(e)}")
                continue
    
    logger.info(f"✅ Scraped cards for {bank_code}: {created_count} created, {updated_count} updated")
    return {
        'created': created_count,
        'updated': updated_count,
        'total': created_count + updated_count,
        'bank': bank.name,
    }

