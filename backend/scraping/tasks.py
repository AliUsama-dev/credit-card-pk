# scraping/tasks.py
from celery import shared_task
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from typing import Dict, List, Tuple, Any
import logging

logger = logging.getLogger(__name__)

# Map scraper "category" (DINING/TRAVEL/...) to Merchant.MERCHANT_TYPES
_CATEGORY_TO_MERCHANT_TYPE = {
    'DINING': 'RESTAURANT',
    'TRAVEL': 'TRAVEL',
    'SHOPPING': 'RETAIL',
    'E_COMMERCE': 'E_COMMERCE',
    'GROCERIES': 'SUPERMARKET',
    'FUEL': 'FUEL_STATION',
    'ELECTRONICS': 'ELECTRONICS',
    'ENTERTAINMENT': 'ENTERTAINMENT',
    'UTILITIES': 'OTHER',
    'HEALTHCARE': 'HEALTHCARE',
    'EDUCATION': 'EDUCATION',
    'AUTOMOTIVE': 'AUTOMOTIVE',
    'FASHION': 'FASHION',
    'HOME': 'HOME',
    'BEAUTY': 'BEAUTY',
    'OTHER': 'OTHER',
}

# scraping/tasks.py - Update the process_bank_offers function
def process_bank_offers(bank, offers: List[Dict]) -> Tuple[int, int]:
    """Process and save offers for a bank"""
    from offers.models import Offer, Merchant
    
    created_count = 0
    updated_count = 0
    
    with transaction.atomic():
        for offer_data in offers:
            try:
                title = (offer_data.get('title') or '').strip()
                if not title or len(title) < 3:
                    continue

                # Get or create merchant
                merchant_name = offer_data.get('merchant', 'Various Merchants')[:255]
                city = (offer_data.get('city') or 'ALL_PAKISTAN').upper().replace(' ', '_')
                category = (offer_data.get('category') or 'OTHER').upper()
                merchant_type = _CATEGORY_TO_MERCHANT_TYPE.get(category, 'OTHER')

                # Default validity if scraper didn't detect dates
                valid_from = offer_data.get('valid_from') or timezone.now().date()
                valid_to = offer_data.get('valid_to') or (timezone.now().date() + timezone.timedelta(days=60))
                
                merchant, _ = Merchant.objects.get_or_create(
                    name=merchant_name,
                    defaults={
                        'merchant_type': merchant_type,
                        'city': city,
                        'is_active': True,
                        'is_verified': False,
                    }
                )
                
                # Debug logging
                logger.info(f"Processing offer: {title[:50]}...")
                logger.info(f"Merchant: {merchant_name}, Bank: {bank.name}")
                
                # Create or update offer
                offer, created = Offer.objects.update_or_create(
                    bank=bank,
                    title=title[:255],
                    merchant=merchant,
                    defaults={
                        'description': offer_data.get('description', '')[:2000],
                        'offer_type': offer_data.get('offer_type', 'OTHER') or 'OTHER',
                        'discount_percentage': offer_data.get('discount_percentage'),
                        'cashback_amount': offer_data.get('cashback_amount'),
                        'min_spend': offer_data.get('min_spend'),
                        'max_discount': offer_data.get('max_discount'),
                        'valid_from': valid_from,
                        'valid_to': valid_to,
                        'terms_conditions': offer_data.get('terms_conditions', '')[:2000] if offer_data.get('terms_conditions') else '',
                        'scraping_source': offer_data.get('source_url', ''),
                        'is_active': True,
                        'last_updated': timezone.now(),
                    }
                )
                
                if created:
                    created_count += 1
                    logger.info(f"Created new offer: {title[:50]}")
                else:
                    updated_count += 1
                    logger.info(f"Updated existing offer: {title[:50]}")
                    
            except Exception as e:
                logger.error(f"Error processing offer '{title[:50]}...': {str(e)}")
                continue
    
    logger.info(f"Processed {len(offers)} offers, created {created_count}, updated {updated_count}")
    return created_count, updated_count

@shared_task(bind=True, max_retries=3)
def scrape_verified_banks(self):
    """Task to scrape verified banks - Keep this for backward compatibility"""
    from admin_panel.models import ScrapingLog
    from cards.models import Bank
    
    # Create scraping log
    log = ScrapingLog.objects.create(
        status='RUNNING',
        task_id=getattr(self.request, 'id', None),
        offers_found=0,
        offers_created=0,
        offers_updated=0,
    )
    
    try:
        logger.info("Starting verified bank scraping...")
        
        # Get scraper function
        from .scrapers.simple_bank_scraper import scrape_banks_with_filters_sync_simple
        scrape_all_verified_banks = scrape_banks_with_filters_sync_simple
        
        # Scrape all banks
        all_offers = scrape_all_verified_banks({})
        
        total_offers_found = 0
        total_offers_created = 0
        total_offers_updated = 0
        
        for bank_code, offers in all_offers.items():
            total_offers_found += len(offers)
            
            # Find bank in database
            bank = Bank.objects.filter(
                Q(code__iexact=bank_code) | 
                Q(name__icontains=bank_code)
            ).first()
            
            if not bank:
                logger.warning(f"Bank {bank_code} not found in database")
                continue
            
            # Process offers
            created, updated = process_bank_offers(bank, offers)
            total_offers_created += created
            total_offers_updated += updated
        
        # Update log
        log.status = 'COMPLETED'
        log.offers_found = total_offers_found
        log.offers_created = total_offers_created
        log.offers_updated = total_offers_updated
        log.completed_at = timezone.now()
        if log.started_at:
            log.duration_seconds = int((log.completed_at - log.started_at).total_seconds())
        
        logger.info(f"Scraping completed: Found {total_offers_found} offers, "
                   f"Created {total_offers_created}, Updated {total_offers_updated}")
        
        return {
            'status': 'COMPLETED',
            'offers_found': total_offers_found,
            'offers_created': total_offers_created,
            'offers_updated': total_offers_updated,
        }
        
    except Exception as e:
        logger.error(f"Scraping task failed: {str(e)}")
        log.status = 'FAILED'
        log.error_message = str(e)[:500]
        log.completed_at = timezone.now()
        log.save()
        
        # Retry after 5 minutes
        self.retry(exc=e, countdown=300)
        
        return {
            'status': 'FAILED',
            'error': str(e)
        }
    
    finally:
        if log.status != 'FAILED':
            log.save()

# Add new import at top
from .scrapers.peekaboo_scraper import scrape_peekaboo_banks_sync

# Update the scrape_verified_banks_with_filters function:
@shared_task(bind=True, max_retries=3)
def scrape_verified_banks_with_filters(self, filters: Dict[str, Any] = None):
    """Task to scrape verified banks with filters using Peekaboo API"""
    from admin_panel.models import ScrapingLog
    from cards.models import Bank
    
    filters = filters or {}
    
    # Create scraping log
    log = ScrapingLog.objects.create(
        status='RUNNING',
        task_id=getattr(self.request, 'id', None),
        offers_found=0,
        offers_created=0,
        offers_updated=0,
    )
    
    try:
        logger.info(f"Starting Peekaboo bank scraping with filters: {filters}")
        
        # Use Peekaboo scraper
        all_offers = scrape_peekaboo_banks_sync(filters)
        
        total_offers_found = 0
        total_offers_created = 0
        total_offers_updated = 0
        
        for bank_code, offers in all_offers.items():
            total_offers_found += len(offers)
            
            # Find bank in database
            bank = Bank.objects.filter(
                Q(code__iexact=bank_code) | 
                Q(name__icontains=bank_code)
            ).first()
            
            if not bank:
                logger.warning(f"Bank {bank_code} not found in database")
                continue
            
            # Process offers
            created, updated = process_bank_offers(bank, offers)
            total_offers_created += created
            total_offers_updated += updated
        
        # Update log
        log.status = 'COMPLETED'
        log.offers_found = total_offers_found
        log.offers_created = total_offers_created
        log.offers_updated = total_offers_updated
        log.completed_at = timezone.now()
        if log.started_at:
            log.duration_seconds = int((log.completed_at - log.started_at).total_seconds())
        log.save()
        
        logger.info(f"Peekaboo scraping completed: Found {total_offers_found} offers, "
                   f"Created {total_offers_created}, Updated {total_offers_updated}")
        
        return {
            'status': 'COMPLETED',
            'offers_found': total_offers_found,
            'offers_created': total_offers_created,
            'offers_updated': total_offers_updated,
            'filters_applied': filters,
        }
        
    except Exception as e:
        logger.error(f"Peekaboo scraping task failed: {str(e)}")
        log.status = 'FAILED'
        log.error_message = str(e)[:500]
        log.completed_at = timezone.now()
        log.save()
        
        self.retry(exc=e, countdown=300)
        
        return {
            'status': 'FAILED',
            'error': str(e),
            'filters_applied': filters,
        }
    
@shared_task
def scrape_single_bank_with_filters(bank_id: int, filters: Dict[str, Any] = None):
    """Scrape single bank with filters using Peekaboo API"""
    from admin_panel.models import ScrapingLog
    from cards.models import Bank
    
    filters = filters or {}
    
    try:
        bank = Bank.objects.get(id=bank_id)
        
        # Create scraping log
        log = ScrapingLog.objects.create(
            bank=bank,
            status='RUNNING',
            offers_found=0,
            offers_created=0,
            offers_updated=0,
        )
        
        # Import and use Peekaboo scraper
        from .scrapers.peekaboo_scraper import PeekabooGuruScraper
        scraper = PeekabooGuruScraper(use_async=False)
        
        # Scrape bank with filters
        offers = scraper.scrape_bank_offers_sync(bank.code, filters)
        
        # Process offers
        created, updated = process_bank_offers(bank, offers)
        
        # Update log
        log.status = 'COMPLETED'
        log.offers_found = len(offers)
        log.offers_created = created
        log.offers_updated = updated
        log.completed_at = timezone.now()
        if log.started_at:
            log.duration_seconds = int((log.completed_at - log.started_at).total_seconds())
        log.save()
        
        return {
            'status': 'COMPLETED',
            'bank': bank.name,
            'offers_found': len(offers),
            'offers_created': created,
            'offers_updated': updated,
            'filters_applied': filters,
        }
            
    except Bank.DoesNotExist:
        return {
            'status': 'FAILED',
            'error': f'Bank with id {bank_id} not found'
        }
    except Exception as e:
        logger.error(f"Single bank scraping failed: {str(e)}")
        return {
            'status': 'FAILED',
            'error': str(e),
            'filters_applied': filters,
        }
    
@shared_task
def scheduled_hourly_scraping():
    """Scheduled hourly scraping - runs every 1 hour"""
    logger.info("🔄 Running scheduled hourly scraping...")
    try:
        result = scrape_verified_banks.delay()
        logger.info(f"✅ Hourly scraping task started: {result.id}")
        return {
            'status': 'started',
            'task_id': result.id,
            'message': 'Hourly scraping task started successfully'
        }
    except Exception as e:
        logger.error(f"❌ Hourly scraping failed: {str(e)}")
        return {
            'status': 'failed',
            'error': str(e)
        }

@shared_task
def scheduled_daily_scraping():
    """Scheduled daily scraping - comprehensive update"""
    logger.info("🔄 Running scheduled daily scraping...")
    try:
        result = scrape_verified_banks.delay()
        logger.info(f"✅ Daily scraping task started: {result.id}")
        return {
            'status': 'started',
            'task_id': result.id,
            'message': 'Daily scraping task started successfully'
        }
    except Exception as e:
        logger.error(f"❌ Daily scraping failed: {str(e)}")
        return {
            'status': 'failed',
            'error': str(e)
        }