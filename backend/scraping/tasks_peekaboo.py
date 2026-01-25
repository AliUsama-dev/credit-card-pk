# scraping/tasks_peekaboo.py
# Hourly scraping task for Peekaboo API deals

from celery import shared_task
from django.utils import timezone
from django.utils.timezone import make_aware
from django.db import transaction
from datetime import datetime, timedelta
import logging
import requests
import pytz
import time

logger = logging.getLogger(__name__)

# Import models after they're created
try:
    from offers.models_peekaboo import PeekabooDeal, PeekabooCategory, PeekabooEntity
    from cards.models import Bank, CreditCard
except ImportError:
    logger.warning("Peekaboo models not found - run migrations first")
    PeekabooDeal = None
    PeekabooCategory = None
    PeekabooEntity = None
    Bank = None
    CreditCard = None

# Peekaboo API configuration
PEEKABOO_API_BASE = 'https://peekaboo.guru'
PEEKABOO_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'Origin': 'https://peekaboo.guru',
    'Referer': 'https://peekaboo.guru/',
    'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpZCI6NzIsInJvbGUiOiJndWVzdCIsImlhdCI6MTU1MzcwMDgwNiwianRpIjoiUEpJMXFTb2ktQzRBZFJWcm9nb3RNV2UzV3VXcFdXTm0ifQ.2mb26xL4Qt7FfBQZ-XQvp-fhecMpaVUVXWp_GEST_6U',
    'medium': 'WEB',
    'version': '2.1.0.2',
}

# Pakistani cities with coordinates
CITIES = [
    {'name': 'Karachi', 'code': 'KARACHI', 'lat': 24.8607, 'long': 67.0011},
    {'name': 'Lahore', 'code': 'LAHORE', 'lat': 31.5204, 'long': 74.3587},
    {'name': 'Islamabad', 'code': 'ISLAMABAD', 'lat': 33.7294, 'long': 73.0931},
    {'name': 'Rawalpindi', 'code': 'RAWALPINDI', 'lat': 33.5651, 'long': 73.0169},
    {'name': 'Faisalabad', 'code': 'FAISALABAD', 'lat': 31.4504, 'long': 73.1350},
    {'name': 'Multan', 'code': 'MULTAN', 'lat': 30.1575, 'long': 71.5249},
    {'name': 'Hyderabad', 'code': 'HYDERABAD', 'lat': 25.3960, 'long': 68.3578},
    {'name': 'Peshawar', 'code': 'PESHAWAR', 'lat': 34.0151, 'long': 71.5249},
    {'name': 'Quetta', 'code': 'QUETTA', 'lat': 30.1798, 'long': 66.9750},
    {'name': 'Gujranwala', 'code': 'GUJRANWALA', 'lat': 32.1617, 'long': 74.1883},
    {'name': 'Sialkot', 'code': 'SIALKOT', 'lat': 32.4945, 'long': 74.5229},
    {'name': 'Bahawalpur', 'code': 'BAHAWALPUR', 'lat': 29.4000, 'long': 71.6833},
    {'name': 'Sargodha', 'code': 'SARGODHA', 'lat': 32.0836, 'long': 72.6711},
    {'name': 'Sukkur', 'code': 'SUKKUR', 'lat': 27.7025, 'long': 68.8567},
    {'name': 'Larkana', 'code': 'LARKANA', 'lat': 27.5590, 'long': 68.2120},
]

@shared_task
def scrape_peekaboo_all_banks_info(city_name: str = 'Lahore'):
    """
    Scrape all banks information from Peekaboo API v5 endpoint.
    This discovers all banks with their sourceEntityId, entityId, and other metadata.
    Returns a dictionary mapping bank codes to their Peekaboo IDs.
    """
    city_info = next((c for c in CITIES if c['name'] == city_name), None)
    if not city_info:
        city_info = {'name': city_name, 'code': city_name.upper(), 'lat': 31.554606, 'long': 74.357158}
    
    try:
        url = f"{PEEKABOO_API_BASE}/api/v5/entity/_all/branch/_all/sourceEntities/_all"
        params = {
            'city': city_info['name'],
            'country': 'Pakistan',
            'entity': 'All',
            'language': 'en',
            'lat': city_info['lat'],
            'limit': 100,
            'long': city_info['long'],
            'offset': 0,
        }
        
        logger.info(f"🔍 Fetching all banks from Peekaboo API...")
        response = requests.get(url, params=params, headers=PEEKABOO_HEADERS, timeout=30)
        
        if response.status_code == 200:
            banks_data = response.json()
            if not isinstance(banks_data, list):
                banks_data = []
            
            logger.info(f"✅ Found {len(banks_data)} banks in Peekaboo")
            
            # Map bank names to our bank codes
            bank_name_to_code = {
                'Allied Bank': 'ABL',
                'Al Baraka Bank': 'AL_BARAKA',
                'Askari Bank Limited': 'ASKARI',
                'Bank AL Habib': 'BANK_AL_HABIB',
                'Bank Alfalah': 'BAFL',
                'Bank of Punjab': 'BOP',
                'Bank of Khyber': 'BANK_OF_KHYBER',
                'BankIslami': 'BANK_ISLAMI',
                'Dubai Islamic Bank': 'DIB',
                'Faysal Bank Limited': 'FAYSAL',
                'Habib Bank Limited': 'HBL',
                'Habib Metro Bank': 'HABIB_METRO',
                'HBL Islamic Bank Limited': 'HBL_ISLAMIC',
                'JS Bank': 'JS_BANK',
                'MCB Bank Limited': 'MCB',
                'MCB Islamic Bank Ltd': 'MCB_ISLAMIC',
                'Meezan Bank': 'MEEZAN',
                'National Bank of Pakistan': 'NBP',
                'Samba Bank': 'SAMBA',
                'Silk Bank': 'SILK',
                'Soneri Bank Limited': 'SONERI',
                'Standard Chartered Bank': 'SCB',
                'United Bank Limited (UBL)': 'UBL',
            }
            
            discovered_banks = {}
            for bank_data in banks_data:
                entity_name = bank_data.get('entityName', '')
                source_entity_id = bank_data.get('sourceEntityId')
                entity_id = bank_data.get('id')  # This is the entityId used in URLs
                
                if not source_entity_id or not entity_id:
                    continue
                
                # Try to match bank name to our bank codes
                bank_code = None
                for name_pattern, code in bank_name_to_code.items():
                    if name_pattern.lower() in entity_name.lower() or entity_name.lower() in name_pattern.lower():
                        bank_code = code
                        break
                
                if bank_code:
                    discovered_banks[bank_code] = {
                        'sourceEntityId': source_entity_id,
                        'entityId': entity_id,
                        'entityName': entity_name,
                        'dealCount': bank_data.get('dealCount', 0),
                        'maxDiscount': bank_data.get('maxDiscount', 0),
                    }
                    logger.info(f"✅ Mapped {entity_name} -> {bank_code} (sourceEntityId: {source_entity_id}, entityId: {entity_id})")
            
            return discovered_banks
        else:
            logger.warning(f"❌ Failed to fetch banks: {response.status_code} - {response.text[:200]}")
            return {}
            
    except Exception as e:
        logger.error(f"Error fetching banks info: {str(e)}")
        return {}

# Bank Peekaboo sourceEntityId and entityId mapping (from Peekaboo API)
# sourceEntityId: The bank's source entity ID in Peekaboo system (used for filtering deals)
# entityId: The bank's entity ID (used for associationType endpoint: /api/sourceEntity/{entityId}/associationType/_all)
# These are discovered from /api/v5/entity/_all/branch/_all/sourceEntities/_all endpoint
# Updated with real data from Peekaboo API
BANK_PEEKABOO_IDS = {
    'MEEZAN': {'sourceEntityId': 29, 'entityId': 45},  # Meezan Bank
    'HBL': {'sourceEntityId': 32, 'entityId': 289},     # Habib Bank Limited
    'UBL': {'sourceEntityId': 38, 'entityId': 321},     # United Bank Limited
    'MCB': {'sourceEntityId': 44, 'entityId': 777},     # MCB Bank Limited
    'BAFL': {'sourceEntityId': 43, 'entityId': 627},    # Bank Alfalah
    'SCB': {'sourceEntityId': 31, 'entityId': 54},      # Standard Chartered Bank
    'ABL': {'sourceEntityId': 45, 'entityId': 778},     # Allied Bank
    'FAYSAL': {'sourceEntityId': 30, 'entityId': 44},   # Faysal Bank Limited
    'ASKARI': {'sourceEntityId': 37, 'entityId': 322},  # Askari Bank Limited
    'BANK_ISLAMI': {'sourceEntityId': 50, 'entityId': 1006}, # BankIslami
    'BANK_AL_HABIB': {'sourceEntityId': 28, 'entityId': 46}, # Bank AL Habib
    'BOP': {'sourceEntityId': 96, 'entityId': 4468},     # Bank of Punjab
    'BANK_OF_PUNJAB': {'sourceEntityId': 96, 'entityId': 4468},  # Bank of Punjab (alias)
    'HABIB_METRO': {'sourceEntityId': 46, 'entityId': 782}, # Habib Metro Bank
    'HBL_ISLAMIC': {'sourceEntityId': 239, 'entityId': 65659}, # HBL Islamic Bank Limited
    'MCB_ISLAMIC': {'sourceEntityId': 241, 'entityId': 73011}, # MCB Islamic Bank Ltd
    'AL_BARAKA': {'sourceEntityId': 106, 'entityId': 6095}, # Al Baraka Bank
    'JS_BANK': {'sourceEntityId': 39, 'entityId': 325}, # JS Bank
    'JSBANK': {'sourceEntityId': 39, 'entityId': 325},  # JS Bank (alias - database code)
    'NBP': {'sourceEntityId': 213, 'entityId': 14708},  # National Bank of Pakistan
    'DIB': {'sourceEntityId': 40, 'entityId': 327},     # Dubai Islamic Bank
    'SONERI': {'sourceEntityId': 51, 'entityId': 1045}, # Soneri Bank Limited
    'SILK': {'sourceEntityId': 1, 'entityId': 40},      # Silk Bank
    'SAMBA': {'sourceEntityId': 231, 'entityId': 27919}, # Samba Bank
    'BANK_OF_KHYBER': {'sourceEntityId': 246, 'entityId': 74535}, # Bank of Khyber
}

# Reverse mapping for quick lookup (by sourceEntityId)
PEEKABOO_ID_TO_BANK = {}
for bank_code, ids in BANK_PEEKABOO_IDS.items():
    if isinstance(ids, dict) and ids.get('sourceEntityId'):
        PEEKABOO_ID_TO_BANK[ids['sourceEntityId']] = bank_code

# Bank slug mapping for discounts parameter in URLs
BANK_SLUG_MAP = {
    'MEEZAN': 'meezan-bank',
    'HBL': 'hbl',
    'ABL': 'allied-bank',
    'FAYSAL': 'faysal-bank',
    'AL_BARAKA': 'al-baraka-bank',
    'UBL': 'ubl',
    'MCB': 'mcb',
    'BAFL': 'bank-alfalah',
    'SCB': 'standard-chartered',
    'ASKARI': 'askari-bank',
    'BANK_ISLAMI': 'bank-islami',
    'BANK_AL_HABIB': 'bank-al-habib',
    'BOP': 'bank-of-punjab',
    'HABIB_METRO': 'habib-metro',
    'HBL_ISLAMIC': 'hbl-islamic',
    'MCB_ISLAMIC': 'mcb-islamic',
    'JS_BANK': 'js-bank',
    'JSBANK': 'js-bank',  # Alias for database code
    'NBP': 'national-bank-of-pakistan',
    'DIB': 'dubai-islamic-bank',
    'SONERI': 'soneri-bank',
    'SILK': 'silk-bank',
    'SAMBA': 'samba-bank',
    'BANK_OF_KHYBER': 'bank-of-khyber',
}

@shared_task
def scrape_peekaboo_entities():
    """Scrape source entities/merchants from Peekaboo v6/sourceEntities API"""
    if not PeekabooEntity:
        logger.error("PeekabooEntity model not available")
        return 0
    
    try:
        url = f"{PEEKABOO_API_BASE}/api/v6/sourceEntities"
        # API requires limit, offset, city, and country in body
        payload = {
            'limit': 1000,
            'offset': 0,
            'city': 'Karachi',  # Use a default city to get all entities
            'country': 'Pakistan',
        }
        response = requests.post(url, json=payload, headers=PEEKABOO_HEADERS, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            entities = data if isinstance(data, list) else data.get('entities', []) or data.get('sourceEntities', [])
            
            created_count = 0
            updated_count = 0
            
            with transaction.atomic():
                for entity_data in entities:
                    try:
                        source_entity_id = entity_data.get('sourceEntityId') or entity_data.get('id')
                        if not source_entity_id:
                            continue
                        
                        name = entity_data.get('name', 'Unknown Entity')
                        if not name or name == 'Unknown Entity':
                            continue
                        
                        # Get categories from entity
                        categories = entity_data.get('categories', [])
                        
                        entity, created = PeekabooEntity.objects.update_or_create(
                            source_entity_id=source_entity_id,
                            defaults={
                                'entity_id': source_entity_id,
                                'name': name,
                                'description': entity_data.get('description', ''),
                                'logo': entity_data.get('logo', ''),
                                'is_active': True,
                                'last_scraped_at': timezone.now(),
                            }
                        )
                        
                        if created:
                            created_count += 1
                        else:
                            updated_count += 1
                            
                    except Exception as e:
                        logger.error(f"Error processing entity {entity_data.get('name', 'unknown')}: {str(e)}")
                        continue
            
            logger.info(f"✅ Scraped {len(entities)} entities: {created_count} created, {updated_count} updated")
            return created_count + updated_count
        else:
            logger.warning(f"❌ Failed to fetch entities: {response.status_code}")
            return 0
            
    except Exception as e:
        logger.error(f"Error scraping entities: {str(e)}")
        return 0

@shared_task
def scrape_peekaboo_categories():
    """Scrape categories from Peekaboo v7/category API"""
    if not PeekabooCategory:
        logger.error("PeekabooCategory model not available")
        return 0
    
    try:
        url = f"{PEEKABOO_API_BASE}/api/v7/category"
        payload = {}
        response = requests.post(url, json=payload, headers=PEEKABOO_HEADERS, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            categories = data if isinstance(data, list) else []
            
            created_count = 0
            updated_count = 0
            
            with transaction.atomic():
                for cat_data in categories:
                    try:
                        category_id = cat_data.get('id')
                        if not category_id:
                            continue
                        
                        category, created = PeekabooCategory.objects.update_or_create(
                            category_id=category_id,
                            defaults={
                                'name': cat_data.get('name', ''),
                                'logo': cat_data.get('logo', ''),
                                'image': cat_data.get('image', ''),
                                'scope': cat_data.get('scope', ''),
                                'entities': cat_data.get('entities', 0),
                                'discount': cat_data.get('discount', 0),
                                'dealCount': cat_data.get('dealCount', 0),
                                'last_scraped_at': timezone.now(),
                            }
                        )
                        
                        if created:
                            created_count += 1
                        else:
                            updated_count += 1
                            
                    except Exception as e:
                        logger.error(f"Error processing category: {str(e)}")
                        continue
            
            logger.info(f"✅ Scraped {len(categories)} categories: {created_count} created, {updated_count} updated")
            return created_count + updated_count
        else:
            logger.warning(f"❌ Failed to fetch categories: {response.status_code}")
            return 0
            
    except Exception as e:
        logger.error(f"Error scraping categories: {str(e)}")
        return 0

@shared_task
def scrape_peekaboo_deals():
    """Scrape deals from Peekaboo v8/entity/deals API for all cities"""
    if not PeekabooDeal:
        logger.error("PeekabooDeal model not available")
        return {'created': 0, 'updated': 0, 'skipped': 0}
    
    total_created = 0
    total_updated = 0
    total_skipped = 0
    
    try:
        for city in CITIES:
            try:
                url = f"{PEEKABOO_API_BASE}/api/v8/entity/deals"
                
                payload = {
                    'city': city['name'],
                    'country': 'Pakistan',
                    'entity': 'All',
                    'language': 'en',
                    'lat': city['lat'],
                    'long': city['long'],
                    'limit': 1000,  # Get maximum deals
                    'offset': 0,
                }
                
                # Add retry logic for connection errors
                max_retries = 3
                retry_delay = 2  # seconds
                response = None
                
                for attempt in range(max_retries):
                    try:
                        response = requests.post(url, json=payload, headers=PEEKABOO_HEADERS, timeout=60)
                        break  # Success, exit retry loop
                    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, ConnectionResetError) as e:
                        if attempt < max_retries - 1:
                            logger.warning(f"⚠️  Connection error (attempt {attempt + 1}/{max_retries}): {str(e)}. Retrying in {retry_delay}s...")
                            time.sleep(retry_delay)
                            retry_delay *= 2  # Exponential backoff
                        else:
                            logger.error(f"❌ Connection failed after {max_retries} attempts: {str(e)}")
                            raise
                
                if not response:
                    logger.error(f"❌ Failed to get response after {max_retries} attempts")
                    continue
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Handle response structure
                    if isinstance(data, dict):
                        deals_list = data.get('deals', [])
                        total_deals = data.get('total', len(deals_list))
                    else:
                        deals_list = data if isinstance(data, list) else []
                        total_deals = len(deals_list)
                    
                    logger.info(f"✅ REAL DATA from Peekaboo API: {city['name']} - {total_deals} total deals, {len(deals_list)} in response")
                    
                    created, updated, skipped = process_peekaboo_deals(deals_list, city, bank_code=None, card_id=None)
                    total_created += created
                    total_updated += updated
                    total_skipped += skipped
                    
                    logger.info(f"✅ Processed {city['name']}: {created} created, {updated} updated, {skipped} skipped")
                else:
                    logger.warning(f"❌ Failed to fetch deals for {city['name']}: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"Error scraping deals for {city['name']}: {str(e)}")
                continue
        
        logger.info(f"✅ TOTAL: {total_created} created, {total_updated} updated, {total_skipped} skipped")
        return {'created': total_created, 'updated': total_updated, 'skipped': total_skipped}
        
    except Exception as e:
        logger.error(f"Error in scrape_peekaboo_deals: {str(e)}")
        return {'created': 0, 'updated': 0, 'skipped': 0}

@shared_task
def scrape_peekaboo_deals_by_bank(bank_code: str, city_name: str = 'Lahore', card_id: int = None):
    """
    Scrape deals for a specific bank and ALL its cards using the places URL pattern.
    This matches the behavior when user visits https://peekaboo.guru/karachi/places/_all/all?ai=2644&associationTypeId=1897&card=mastercard-platinum-debit-card&discounts=al-baraka-bank&ei=6095&sourceEntityId=106
    
    Args:
        bank_code: Bank code (e.g., 'AL_BARAKA', 'AL_BARAKA_BANK')
        city_name: City name (default: 'Lahore')
        card_id: Optional card ID to scrape deals for only that card
    """
    if not PeekabooDeal or not Bank or not CreditCard:
        logger.error("Models not available")
        return {'created': 0, 'updated': 0, 'skipped': 0}
    
    # Normalize bank code - handle variations like "AL_BARAKA_BANK" -> "AL_BARAKA"
    bank_code_normalized = bank_code.upper()
    # Try exact match first
    bank_info = BANK_PEEKABOO_IDS.get(bank_code_normalized)
    # If not found, try removing common suffixes like "_BANK", "_LIMITED", etc.
    if not bank_info or not isinstance(bank_info, dict):
        # Remove common suffixes
        base_code = bank_code_normalized.replace('_BANK', '').replace('_LIMITED', '').replace('_LTD', '').strip('_')
        bank_info = BANK_PEEKABOO_IDS.get(base_code)
        if bank_info and isinstance(bank_info, dict):
            bank_code_normalized = base_code
            logger.info(f"✅ Matched bank code '{bank_code}' to '{base_code}' (removed suffix)")
        else:
            # Try prefix matching
            for key in BANK_PEEKABOO_IDS.keys():
                if bank_code_normalized.startswith(key) or key.startswith(bank_code_normalized.split('_')[0]):
                    bank_info = BANK_PEEKABOO_IDS.get(key)
                    if bank_info and isinstance(bank_info, dict):
                        bank_code_normalized = key
                        logger.info(f"✅ Matched bank code '{bank_code}' to '{key}' (prefix match)")
                        break
    
    if not bank_info or not isinstance(bank_info, dict):
        logger.warning(f"No Peekaboo sourceEntityId found for bank: {bank_code} (tried: {bank_code_normalized})")
        logger.info(f"Available bank codes: {list(BANK_PEEKABOO_IDS.keys())[:10]}...")
        return {'created': 0, 'updated': 0, 'skipped': 0}
    
    source_entity_id = bank_info.get('sourceEntityId')
    entity_id = bank_info.get('entityId')
    
    if not source_entity_id or not entity_id:
        logger.warning(f"Missing Peekaboo IDs for bank {bank_code}: sourceEntityId={source_entity_id}, entityId={entity_id}")
        return {'created': 0, 'updated': 0, 'skipped': 0}
    
    # Get bank object
    bank = Bank.objects.filter(code=bank_code_normalized).first()
    if not bank:
        # Try to find by code variations
        bank = Bank.objects.filter(code__iexact=bank_code).first()
        if not bank:
            logger.warning(f"Bank not found in database: {bank_code} (normalized: {bank_code_normalized})")
            return {'created': 0, 'updated': 0, 'skipped': 0}
    
    # Get city coordinates
    city_info = next((c for c in CITIES if c['name'] == city_name), None)
    if not city_info:
        city_info = {'name': city_name, 'code': city_name.upper(), 'lat': 31.5204, 'long': 74.3587}  # Default to Lahore
    
    city_slug = city_info['name'].lower()
    bank_slug = BANK_SLUG_MAP.get(bank_code_normalized, bank_code_normalized.lower().replace('_', '-'))
    
    total_created = 0
    total_updated = 0
    total_skipped = 0
    
    try:
        # Step 1 (optional): scrape ALL bank deals (bank discounts page count).
        # This is useful for the Bank overview discounts tab, but deals may not link cleanly to cards.
        logger.info(f"🔍 Step 1: Scraping ALL bank deals for {bank.name} in {city_name} (bank-wide)")
        url = f"{PEEKABOO_API_BASE}/api/v8/entity/deals"
        payload = {
            'city': city_info['name'],
            'country': 'Pakistan',
            'entity': 'All',
            'language': 'en',
            'lat': city_info['lat'],
            'long': city_info['long'],
            'limit': 1000,
            'offset': 0,
            'sourceEntityId': str(source_entity_id),
        }

        response = requests.post(url, json=payload, headers=PEEKABOO_HEADERS, timeout=60)
        if response.status_code == 200:
            data = response.json()
            all_deals_list = data.get('deals', []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
            total_deals = data.get('total', len(all_deals_list)) if isinstance(data, dict) else len(all_deals_list)
            logger.info(f"✅ Bank-wide: scraped {total_deals} total deals for {bank.name} (got {len(all_deals_list)} in response)")

            created, updated, skipped = process_peekaboo_deals(
                all_deals_list,
                city_info,
                bank_code=bank.code,  # REAL DB bank.code
                card_id=None,
            )
            total_created += created
            total_updated += updated
            total_skipped += skipped
        else:
            logger.warning(f"❌ Failed bank-wide fetch for {bank.name}: {response.status_code} - {response.text[:200]}")

        # Step 2 (critical): scrape per-card deals like the UI URL:
        # https://peekaboo.guru/karachi/places/_all/all?ai=...&associationTypeId=...&card=...&discounts=...&ei=...&selfDeal=true&sourceEntityId=...
        # These results MUST be linked to the selected card; this is what the user sees.
        logger.info(f"🔍 Step 2: Scraping card-specific deals (selfDeal=true) for {bank.name} in {city_name}")

        # Ensure cards have peekaboo_association_type_id and peekaboo_card_slug
        # If missing, populate from associationType endpoint
        has_any = CreditCard.objects.filter(bank=bank, is_active=True, peekaboo_association_type_id__isnull=False).exclude(peekaboo_association_type_id=0).exists()
        if not has_any:
            logger.info(f"🔍 No cards with Peekaboo associations found for {bank.name}; scraping card associations first...")
            scrape_peekaboo_card_associations(bank_code_normalized, city_name)

        cards_qs = CreditCard.objects.filter(bank=bank, is_active=True).exclude(peekaboo_association_type_id__isnull=True).exclude(peekaboo_association_type_id=0)
        if card_id:
            cards_qs = cards_qs.filter(id=card_id)

        if not cards_qs.exists():
            logger.warning(f"⚠️  No cards with Peekaboo associationTypeId found for {bank.name}; cannot scrape card-specific deals.")
            logger.info(f"✅ TOTAL for {bank.name} ({city_name}): {total_created} created, {total_updated} updated, {total_skipped} skipped")
            return {'created': total_created, 'updated': total_updated, 'skipped': total_skipped}

        # Fetch association list ONCE to map typeId -> associationId (ai)
        assoc_map = {}
        try:
            assoc_url = f"{PEEKABOO_API_BASE}/api/sourceEntity/{entity_id}/associationType/_all"
            assoc_params = {
                'city': city_info['name'],
                'country': 'Pakistan',
                'entity': bank.name,
                'language': 'en',
                'lat': city_info['lat'],
                'long': city_info['long'],
                'limit': 200,
                'offset': 0,
            }
            assoc_response = requests.get(assoc_url, params=assoc_params, headers=PEEKABOO_HEADERS, timeout=30)
            if assoc_response.status_code == 200:
                associations = assoc_response.json()
                if isinstance(associations, list):
                    for assoc in associations:
                        try:
                            type_id = assoc.get('typeId') or assoc.get('associationTypeId')
                            ai = assoc.get('associationId') or assoc.get('id')
                            if type_id and ai:
                                assoc_map[int(type_id)] = int(ai)
                        except Exception:
                            continue
        except Exception as e:
            logger.debug(f"Could not fetch association list for bank {bank.name}: {str(e)}")

        for card in cards_qs:
            try:
                association_type_id = card.peekaboo_association_type_id
                if not association_type_id:
                    continue

                try:
                    ai = assoc_map.get(int(association_type_id), int(association_type_id))
                except Exception:
                    ai = association_type_id

                card_slug = card.peekaboo_card_slug or card.name.lower().replace(' ', '-').replace('card', '').replace('debit', '').replace('credit', '').strip('-')

                card_payload = {
                    'city': city_info['name'],
                    'country': 'Pakistan',
                    'entity': 'All',
                    'language': 'en',
                    'lat': city_info['lat'],
                    'long': city_info['long'],
                    'limit': 1000,
                    'offset': 0,
                    'sourceEntityId': str(source_entity_id),
                    'associationTypeId': str(association_type_id),
                    'ai': str(ai),
                    'card': card_slug,
                    'discounts': bank_slug,
                    'ei': str(entity_id),
                    'selfDeal': True,
                }

                logger.info(f"🔍 Card-specific: {bank.name} - {card.name} (typeId={association_type_id}, ai={ai})")
                
                # Add retry logic for connection errors
                max_retries = 3
                retry_delay = 2
                card_response = None
                
                for attempt in range(max_retries):
                    try:
                        card_response = requests.post(url, json=card_payload, headers=PEEKABOO_HEADERS, timeout=60)
                        break
                    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, ConnectionResetError) as e:
                        if attempt < max_retries - 1:
                            logger.warning(f"⚠️  Connection error for card {card.name} (attempt {attempt + 1}/{max_retries}): {str(e)}. Retrying in {retry_delay}s...")
                            time.sleep(retry_delay)
                            retry_delay *= 2
                        else:
                            logger.error(f"❌ Connection failed for card {card.name} after {max_retries} attempts: {str(e)}")
                            raise
                
                if not card_response:
                    logger.error(f"❌ Failed to get response for card {card.name} after {max_retries} attempts")
                    continue
                
                if card_response.status_code != 200:
                    logger.debug(f"Card-specific fetch failed for {card.name}: {card_response.status_code}")
                    continue

                card_data = card_response.json()
                card_deals_list = card_data.get('deals', []) if isinstance(card_data, dict) else (card_data if isinstance(card_data, list) else [])

                card_created, card_updated, card_skipped = process_peekaboo_deals(
                    card_deals_list,
                    city_info,
                    bank_code=bank.code,  # REAL DB bank.code
                    card_id=card.id,       # force link to this card
                )
                total_created += card_created
                total_updated += card_updated
                total_skipped += card_skipped
            except Exception as e:
                logger.error(f"Error scraping card-specific deals for {card.name}: {str(e)}", exc_info=True)
                continue
        
        logger.info(f"✅ TOTAL for {bank.name} ({city_name}): {total_created} created, {total_updated} updated, {total_skipped} skipped")
        return {'created': total_created, 'updated': total_updated, 'skipped': total_skipped}
            
    except Exception as e:
        logger.error(f"Error scraping deals for {bank_code}: {str(e)}", exc_info=True)
        return {'created': 0, 'updated': 0, 'skipped': 0}

@shared_task
def scrape_peekaboo_entities_by_card(bank_code: str, card_id: int = None, city_name: str = 'Lahore', limit: int = 100, offset: int = 0):
    """
    Scrape entities filtered by bank and card using /api/v8/entities endpoint.
    This matches the behavior when user selects a card on Peekaboo.
    Uses associationTypeId, card slug, and other parameters from the card model.
    """
    if not PeekabooEntity or not Bank or not CreditCard:
        logger.error("Models not available")
        return {'entities': [], 'total': 0, 'nextPage': False}
    
    # Get bank's Peekaboo sourceEntityId
    bank_info = BANK_PEEKABOO_IDS.get(bank_code.upper())
    if not bank_info or not isinstance(bank_info, dict):
        logger.warning(f"No Peekaboo sourceEntityId found for bank: {bank_code}")
        return {'entities': [], 'total': 0, 'nextPage': False}
    source_entity_id = bank_info.get('sourceEntityId')
    
    # Get card information if card_id provided
    card = None
    association_type_id = None
    card_slug = None
    if card_id:
        try:
            card = CreditCard.objects.get(id=card_id)
            association_type_id = card.peekaboo_association_type_id
            card_slug = card.peekaboo_card_slug
            if not card_slug:
                # Generate slug from card name
                card_slug = card.name.lower().replace(' ', '-').replace('card', '').replace('debit', '').replace('credit', '').strip('-')
        except CreditCard.DoesNotExist:
            logger.warning(f"Card with id {card_id} not found")
            return {'entities': [], 'total': 0, 'nextPage': False}
    
    # Get city coordinates
    city_info = next((c for c in CITIES if c['name'] == city_name), None)
    if not city_info:
        city_info = {'name': city_name, 'code': city_name.upper(), 'lat': 31.5204, 'long': 74.3587}
    
    try:
        url = f"{PEEKABOO_API_BASE}/api/v8/entities"
        
        # Build payload according to Peekaboo API requirements
        payload = {
            'sortType': 'trending',
            'targetEntities': '_all',
            'city': city_info['name'],
            'country': 'Pakistan',
            'lat': city_info['lat'],
            'long': city_info['long'],
            'language': 'en',
            'categoryId': '_all',
            'category': 'all',
            'limit': limit,
            'offset': offset,
            'sourceEntityId': str(source_entity_id),  # Bank sourceEntityId
        }
        
        # Add card-specific filters if card is provided
        if card and association_type_id:
            payload['associationTypeId'] = str(association_type_id)
            payload['atlId'] = str(association_type_id)  # Same as associationTypeId
            if card_slug:
                payload['card'] = card_slug
            # Get bank slug for discounts parameter
            bank_slug = BANK_SLUG_MAP.get(bank_code.upper(), bank_code.lower().replace(' ', '-').replace('_', '-'))
            payload['discounts'] = bank_slug
            # ai parameter (association ID) - use association_type_id
            payload['ai'] = str(association_type_id)
            # ei parameter (entity ID) - use entityId from bank_info
            entity_id = bank_info.get('entityId')
            if entity_id:
                payload['ei'] = str(entity_id)
        
        logger.info(f"🔍 Scraping entities with payload: {payload}")
        
        response = requests.post(url, json=payload, headers=PEEKABOO_HEADERS, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            
            # Handle response structure
            if isinstance(data, dict):
                entities_list = data.get('entities', [])
                total_entities = data.get('total', len(entities_list))
                next_page = (offset + limit) < total_entities
            else:
                entities_list = data if isinstance(data, list) else []
                total_entities = len(entities_list)
                next_page = False
            
            logger.info(f"✅ Scraped {total_entities} entities for {bank_code} {'with card ' + card.name if card else ''} in {city_name}")
            
            # Store entities and return them (don't save to DB here, let the view handle it)
            processed_entities = []
            for idx, entity_data in enumerate(entities_list):
                # Add a small delay every 10 entities to reduce database contention
                if idx > 0 and idx % 10 == 0:
                    time.sleep(0.05)  # 50ms pause every 10 entities
                
                try:
                    entity_id = entity_data.get('id')
                    if not entity_id:
                        continue
                    
                    # Add retry logic for SQLite database locks
                    max_retries = 5
                    retry_delay = 0.2  # 200ms initial delay
                    retry_count = 0
                    processed = False
                    
                    while not processed and retry_count < max_retries:
                        try:
                            # Store entity in database with atomic transaction
                            with transaction.atomic():
                                entity, created = PeekabooEntity.objects.update_or_create(
                                    source_entity_id=entity_id,
                                    defaults={
                                        'entity_id': entity_id,
                                        'name': entity_data.get('name', ''),
                                        'description': entity_data.get('description', ''),
                                        'logo': entity_data.get('richContent', {}).get('logo', {}).get('content', '') if entity_data.get('richContent') else '',
                                        'is_active': True,
                                        'last_scraped_at': timezone.now(),
                                    }
                                )
                            
                            # Add entity data with stats
                            stats_data = entity_data.get('stats', {})
                            nearest_branch = entity_data.get('nearestBranch')
                            
                            processed_entities.append({
                                'id': entity.id,
                                'entity_id': entity_id,
                                'name': entity_data.get('name', ''),
                                'slug': entity_data.get('slug', ''),
                                'description': entity_data.get('description', ''),
                                'logo': entity_data.get('richContent', {}).get('logo', {}).get('content', '') if entity_data.get('richContent') else '',
                                'rating': entity_data.get('rating'),
                                'stats': {
                                    'branches': stats_data.get('branches', 0),
                                    'partnerOffers': stats_data.get('partnerOffers', 0),
                                    'brandOffers': stats_data.get('brandOffers', 0),
                                    'maxDiscount': stats_data.get('maxDiscount', 0),
                                    'discountFlag': stats_data.get('discountFlag', None),
                                },
                                'nearestBranch': nearest_branch if nearest_branch else None,
                                'online': entity_data.get('online', False),
                                'openNow': entity_data.get('openNow', False),
                            })
                            
                            processed = True
                            
                        except Exception as e:
                            error_msg = str(e).lower()
                            # Check if it's a database lock error (SQLite specific errors)
                            is_lock_error = (
                                'database is locked' in error_msg or 
                                'locked' in error_msg or
                                'operationalerror' in error_msg or
                                'sqlite3.operationalerror' in error_msg
                            )
                            
                            if is_lock_error:
                                retry_count += 1
                                if retry_count < max_retries:
                                    # Wait before retrying (exponential backoff with jitter)
                                    wait_time = retry_delay * (2 ** retry_count) + (retry_count * 0.1)
                                    # Cap max wait time at 2 seconds
                                    wait_time = min(wait_time, 2.0)
                                    time.sleep(wait_time)
                                    logger.debug(f"Database locked for entity {entity_id}, retrying ({retry_count}/{max_retries}) after {wait_time:.2f}s...")
                                    continue
                                else:
                                    # Max retries reached - log and skip
                                    logger.warning(f"⚠️  Skipping entity {entity_id}: database is locked (max retries {max_retries} reached)")
                                    processed = True  # Mark as processed to exit loop
                            else:
                                # Other error - don't retry
                                logger.error(f"❌ Error processing entity {entity_id}: {str(e)}")
                                processed = True  # Mark as processed to exit loop
                                
                except Exception as e:
                    logger.error(f"Error processing entity: {str(e)}")
                    continue
            
            return {
                'entities': processed_entities,
                'total': total_entities,
                'nextPage': next_page,
            }
        else:
            logger.warning(f"❌ Failed to fetch entities: {response.status_code} - {response.text[:200]}")
            return {'entities': [], 'total': 0, 'nextPage': False}
            
    except Exception as e:
        logger.error(f"Error scraping entities: {str(e)}")
        return {'entities': [], 'total': 0, 'nextPage': False}

@shared_task
def scrape_peekaboo_card_associations(bank_code: str, city_name: str = 'Lahore'):
    """
    Scrape card associations for a bank using /api/sourceEntity/{entityId}/associationType/_all endpoint.
    This populates the peekaboo_association_type_id and peekaboo_card_slug fields in CreditCard model.
    """
    if not Bank or not CreditCard:
        logger.error("Models not available")
        return 0
    
    # Get bank's Peekaboo entityId
    bank_info = BANK_PEEKABOO_IDS.get(bank_code.upper())
    if not bank_info or not isinstance(bank_info, dict):
        logger.warning(f"No Peekaboo entityId found for bank: {bank_code}")
        return 0
    
    entity_id = bank_info.get('entityId')
    source_entity_id = bank_info.get('sourceEntityId')
    
    if not entity_id:
        logger.warning(f"No entityId found for bank: {bank_code}")
        return 0
    
    # Get bank object
    bank = Bank.objects.filter(code=bank_code.upper()).first()
    if not bank:
        logger.warning(f"Bank not found: {bank_code}")
        return 0
    
    # Get city coordinates
    city_info = next((c for c in CITIES if c['name'] == city_name), None)
    if not city_info:
        city_info = {'name': city_name, 'code': city_name.upper(), 'lat': 31.554606, 'long': 74.357158}
    
    try:
        # Use GET request with query parameters
        url = f"{PEEKABOO_API_BASE}/api/sourceEntity/{entity_id}/associationType/_all"
        params = {
            'city': city_info['name'],
            'country': 'Pakistan',
            'entity': bank.name,  # Bank name
            'language': 'en',
            'lat': city_info['lat'],
            'limit': 50,
            'long': city_info['long'],
            'offset': 0,
        }
        
        logger.info(f"🔍 Scraping card associations for {bank_code} (entityId: {entity_id})")
        response = requests.get(url, params=params, headers=PEEKABOO_HEADERS, timeout=30)
        
        if response.status_code == 200:
            associations_data = response.json()
            if not isinstance(associations_data, list):
                associations_data = []
            
            logger.info(f"✅ Scraped {len(associations_data)} card associations for {bank_code}")
            
            created_count = 0
            updated_count = 0
            
            # Track which cards we've seen to avoid duplicates
            seen_cards = set()
            
            with transaction.atomic():
                for assoc_data in associations_data:
                    try:
                        type_id = assoc_data.get('typeId')
                        type_name = assoc_data.get('typeName', '')
                        association_id = assoc_data.get('associationId')
                        card_type = assoc_data.get('cardType', '')
                        
                        if not type_id or not type_name:
                            continue
                        
                        # Generate card slug from typeName
                        card_slug = type_name.lower().replace(' ', '-').replace('card', '').replace('debit', '').replace('credit', '').strip('-')
                        # Clean up multiple dashes and special characters
                        while '--' in card_slug:
                            card_slug = card_slug.replace('--', '-')
                        card_slug = card_slug.replace('&', '').replace('(', '').replace(')', '').strip('-')
                        
                        # Try to find matching CreditCard
                        card = None
                        meaningful_words = []
                        
                        # Strategy 1: Match by typeName (exact or partial)
                        card = CreditCard.objects.filter(
                            bank=bank,
                            name__iexact=type_name
                        ).first()
                        
                        # Strategy 2: Match by key words from typeName
                        if not card:
                            # Extract meaningful words
                            meaningful_words = [
                                w for w in type_name.lower().replace('card', '').split() 
                                if w not in ['debit', 'credit', 'visa', 'mastercard', 'platinum', 'gold', 'silver', 'classic', 'world', 'elite', 'the', 'a', 'an', 'and', 'or']
                            ]
                            
                            if meaningful_words:
                                query = CreditCard.objects.filter(bank=bank)
                                for word in meaningful_words[:3]:  # Use first 3 meaningful words
                                    query = query.filter(name__icontains=word)
                                card = query.first()
                        
                        # Strategy 3: Match by card type and first meaningful word
                        if not card and meaningful_words:
                            card_type_hint = 'DEBIT' if 'debit' in type_name.lower() else 'CREDIT'
                            first_word = meaningful_words[0]
                            card = CreditCard.objects.filter(
                                bank=bank,
                                name__icontains=first_word,
                                card_type=card_type_hint
                            ).first()
                        
                        # Update or create card mapping
                        if card:
                            needs_update = False
                            if card.peekaboo_association_type_id != type_id:
                                card.peekaboo_association_type_id = type_id
                                needs_update = True
                            if card.peekaboo_card_slug != card_slug:
                                card.peekaboo_card_slug = card_slug
                                needs_update = True
                            
                            if needs_update:
                                card.save(update_fields=['peekaboo_association_type_id', 'peekaboo_card_slug'])
                                updated_count += 1
                                logger.debug(f"✅ Updated card {card.name} with associationTypeId: {type_id}, slug: {card_slug}")
                        else:
                            # Create new card from Peekaboo association if it doesn't exist
                            # This ensures all Peekaboo cards are available for selection
                            # Check if we've already created this card in this batch
                            card_key = (bank.id, type_name.lower())
                            if card_key not in seen_cards:
                                card_type = 'DEBIT' if 'debit' in type_name.lower() else 'CREDIT'
                                new_card = CreditCard.objects.create(
                                    name=type_name,
                                    bank=bank,
                                    card_type=card_type,
                                    peekaboo_association_type_id=type_id,
                                    peekaboo_card_slug=card_slug,
                                    is_active=True
                                )
                                created_count += 1
                                seen_cards.add(card_key)
                                logger.info(f"✅ Created new card '{type_name}' for {bank.name} from Peekaboo association (typeId: {type_id})")
                            
                    except Exception as e:
                        logger.error(f"Error processing card association: {str(e)}")
                        continue
            
            logger.info(f"✅ Processed card associations for {bank_code}: {created_count} created, {updated_count} updated")
            return created_count + updated_count
        else:
            logger.warning(f"❌ Failed to fetch card associations: {response.status_code} - {response.text[:200]}")
            return 0
            
    except Exception as e:
        logger.error(f"Error scraping card associations: {str(e)}")
        return 0

@shared_task
@shared_task
def scrape_all_banks_card_deals_async(city: str = 'LAHORE'):
    """
    Async Celery task to scrape Peekaboo deals for ALL banks in a specific city.
    This is called from the admin panel "Scrape All Banks" button.
    """
    city_upper = city.upper() if city else 'LAHORE'
    logger.info(f"🚀 Starting async scraping for ALL banks in {city_upper}...")
    
    total_stats = {'created': 0, 'updated': 0, 'skipped': 0, 'banks_processed': 0}
    
    # Convert city name to proper format (LAHORE -> Lahore)
    city_name = city_upper.capitalize() if len(city_upper) > 1 else city_upper
    
    for bank_code in BANK_PEEKABOO_IDS.keys():
        bank_info = BANK_PEEKABOO_IDS[bank_code]
        if not bank_info or not isinstance(bank_info, dict) or not bank_info.get('sourceEntityId'):
            continue  # Skip banks without known sourceEntityId
        
        try:
            logger.info(f"📊 Scraping deals for {bank_code} in {city_name}...")
            
            # Scrape deals for this bank
            result = scrape_peekaboo_deals_by_bank(bank_code, city_upper)
            total_stats['created'] += result.get('created', 0)
            total_stats['updated'] += result.get('updated', 0)
            total_stats['skipped'] += result.get('skipped', 0)
            total_stats['banks_processed'] += 1
            
            logger.info(f"   ✅ {bank_code}: {result.get('created', 0)} created, {result.get('updated', 0)} updated")
            
        except Exception as e:
            logger.error(f"   ❌ Error scraping {bank_code} in {city_name}: {str(e)}")
            continue
    
    logger.info(f"🎉 COMPLETE: Processed {total_stats['banks_processed']} banks. "
                f"Created: {total_stats['created']}, Updated: {total_stats['updated']}, Skipped: {total_stats['skipped']}")
    
    return {
        'status': 'success',
        'city': city_upper,
        'banks_processed': total_stats['banks_processed'],
        'total_created': total_stats['created'],
        'total_updated': total_stats['updated'],
        'total_skipped': total_stats['skipped'],
    }

def scrape_all_banks_card_deals():
    """
    Scrape deals for all Pakistani banks with card associations.
    This is the main task that should be run to get all bank-specific deals.
    """
    logger.info("Starting comprehensive bank-specific deals scraping...")
    
    total_stats = {'created': 0, 'updated': 0, 'skipped': 0}
    
    # Scrape for all major cities
    major_cities = ['Karachi', 'Lahore', 'Islamabad', 'Rawalpindi', 'Faisalabad']
    
    for bank_code in BANK_PEEKABOO_IDS.keys():
        bank_info = BANK_PEEKABOO_IDS[bank_code]
        if not bank_info or not isinstance(bank_info, dict) or not bank_info.get('sourceEntityId'):
            continue  # Skip banks without known sourceEntityId
        
        logger.info(f"Scraping deals for {bank_code}...")
        
        # First scrape card associations
        logger.info(f"Scraping card associations for {bank_code}...")
        scrape_peekaboo_card_associations(bank_code, 'Lahore')
        
        for city_name in major_cities:
            try:
                result = scrape_peekaboo_deals_by_bank(bank_code, city_name)
                total_stats['created'] += result['created']
                total_stats['updated'] += result['updated']
                total_stats['skipped'] += result['skipped']
                
                # After scraping deals, get the bank object
                bank_obj = Bank.objects.filter(code=bank_code.upper()).first()
                if not bank_obj:
                    logger.warning(f"Bank object not found for code: {bank_code}")
                    continue

                # Get all cards for this bank that have associationTypeId
                bank_cards = CreditCard.objects.filter(
                    bank=bank_obj, 
                    is_active=True,
                    peekaboo_association_type_id__isnull=False
                )
                
                for card in bank_cards:
                    logger.info(f"Scraping entities for {bank_code} (card: {card.name}, typeId: {card.peekaboo_association_type_id}) in {city_name}...")
                    # Scrape entities by card
                    scrape_peekaboo_entities_by_card(bank_code, card.id, city_name)
                    
            except Exception as e:
                logger.error(f"Error scraping {bank_code} in {city_name}: {str(e)}")
                continue
    
    logger.info(f"✅ COMPLETE: {total_stats['created']} created, {total_stats['updated']} updated, {total_stats['skipped']} skipped")
    return total_stats

@shared_task
def scrape_all_user_cards_deals():
    """
    Scrape deals for ALL user cards across ALL users.
    This task runs every 2 hours to keep the database updated with latest deals.
    Only scrapes deals for cards that users have added (UserCard model).
    """
    if not PeekabooDeal or not Bank or not CreditCard:
        logger.error("Models not available")
        return {'created': 0, 'updated': 0, 'skipped': 0, 'users_processed': 0, 'cards_processed': 0}
    
    try:
        from cards.models import UserCard
        
        # Get all active user cards
        user_cards = UserCard.objects.filter(
            is_active=True
        ).select_related('card', 'card__bank', 'user')
        
        if not user_cards.exists():
            logger.info("No active user cards found to scrape")
            return {'created': 0, 'updated': 0, 'skipped': 0, 'users_processed': 0, 'cards_processed': 0}
        
        logger.info(f"🔄 Starting background scraping for {user_cards.count()} user cards across all users...")
        
        total_stats = {'created': 0, 'updated': 0, 'skipped': 0}
        users_processed = set()
        cards_processed = 0
        city = 'Lahore'  # Default city
        
        # Group by user to track users processed
        for user_card in user_cards:
            if not user_card.card or not user_card.card.bank:
                continue
            
            card = user_card.card
            bank = card.bank
            user = user_card.user
            
            users_processed.add(user.id)
            cards_processed += 1
            
            try:
                # STEP 1: Scrape entities for this card (same as get_entities_for_user_cards)
                logger.info(f"   📥 Scraping entities for User {user.id} - {bank.code} - {card.name} (ID: {card.id}) in {city}...")
                entities_result = scrape_peekaboo_entities_by_card(
                    bank_code=bank.code,
                    card_id=card.id,
                    city_name=city,
                    limit=100,
                    offset=0
                )
                entities_count = entities_result.get('total', 0) if isinstance(entities_result, dict) else 0
                logger.info(f"   ✅ Scraped {entities_count} entities for {card.name}")
                
                # STEP 2: Scrape deals for this card
                logger.info(f"   📥 Scraping deals for User {user.id} - {bank.code} - {card.name} (ID: {card.id}) in {city}...")
                result = scrape_peekaboo_deals_by_bank(
                    bank_code=bank.code,
                    city_name=city,
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
                
                total_stats['created'] += created
                total_stats['updated'] += updated
                total_stats['skipped'] += skipped
                
                # Reduced logging - only log if significant changes
                if created > 0 or updated > 10:
                    logger.info(f"   ✅ Scraped {created} new, {updated} updated deals for {card.name} (skipped: {skipped})")
            except Exception as e:
                logger.error(f"   ❌ Error scraping deals for User {user.id} - {card.name}: {str(e)}")
                continue
        
        logger.info(f"✅ Background scraping complete: {total_stats['created']} created, {total_stats['updated']} updated, {total_stats['skipped']} skipped")
        logger.info(f"   Processed {len(users_processed)} users and {cards_processed} cards")
        
        total_stats['users_processed'] = len(users_processed)
        total_stats['cards_processed'] = cards_processed
        return total_stats
        
    except Exception as e:
        logger.error(f"❌ Error in scrape_all_user_cards_deals: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {'created': 0, 'updated': 0, 'skipped': 0, 'users_processed': 0, 'cards_processed': 0}

def process_peekaboo_deals(deals_list: list, city: dict, bank_code: str = None, card_id: int = None) -> tuple:
    """
    Process and save Peekaboo deals with duplicate detection.
    
    Args:
        deals_list: List of deal data from API
        city: City information dict
        bank_code: Optional bank code to help with card linking
        card_id: Optional card ID to link deals to a specific card
    """
    created_count = 0
    updated_count = 0
    skipped_count = 0
    
    # Process each deal in its own atomic transaction
    # This ensures that if one deal fails, it doesn't affect others
    # Add a small delay between deals to reduce SQLite contention
    for idx, deal_data in enumerate(deals_list):
        # Add a small delay every 10 deals to reduce database contention
        if idx > 0 and idx % 10 == 0:
            time.sleep(0.05)  # 50ms pause every 10 deals
        # Each deal gets its own atomic transaction
        # Add retry logic for SQLite database locks
        max_retries = 5  # Increase retries for SQLite
        retry_delay = 0.2  # 200ms initial delay
        retry_count = 0
        processed = False
        
        while retry_count < max_retries and not processed:
            try:
                with transaction.atomic():
                    deal_id = deal_data.get('dealId')
                    if not deal_id:
                        skipped_count += 1
                        processed = True  # Mark as processed to exit loop
                        break
                    
                    # Parse dates - ensure timezone-aware
                    start_date_str = deal_data.get('startDate', '')
                    end_date_str = deal_data.get('endDate', '')
                    
                    try:
                        if start_date_str:
                            # Parse ISO format - handle both with and without timezone
                            date_str = start_date_str.replace('Z', '+00:00')
                            try:
                                parsed_start = datetime.fromisoformat(date_str)
                            except ValueError:
                                # Try without timezone
                                parsed_start = datetime.fromisoformat(start_date_str)
                            
                            # Ensure timezone-aware (convert to UTC)
                            if parsed_start.tzinfo is None:
                                # Naive datetime - assume UTC and make aware
                                start_date = make_aware(parsed_start, pytz.UTC)
                            else:
                                # Already aware - convert to UTC for consistency
                                start_date = parsed_start.astimezone(pytz.UTC)
                        else:
                            start_date = timezone.now()
                        
                        if end_date_str:
                            # Parse ISO format - handle both with and without timezone
                            date_str = end_date_str.replace('Z', '+00:00')
                            try:
                                parsed_end = datetime.fromisoformat(date_str)
                            except ValueError:
                                # Try without timezone
                                parsed_end = datetime.fromisoformat(end_date_str)
                            
                            # Ensure timezone-aware (convert to UTC)
                            if parsed_end.tzinfo is None:
                                # Naive datetime - assume UTC and make aware
                                end_date = make_aware(parsed_end, pytz.UTC)
                            else:
                                # Already aware - convert to UTC for consistency
                                end_date = parsed_end.astimezone(pytz.UTC)
                        else:
                            end_date = timezone.now() + timedelta(days=365)  # Default 1 year
                    except Exception as e:
                        logger.warning(f"Error parsing dates for deal {deal_id}: {str(e)}")
                        # Ensure timezone-aware datetimes (timezone.now() already returns aware datetime)
                        start_date = timezone.now()
                        end_date = timezone.now() + timedelta(days=365)
                        
                        # Double-check: ensure both are timezone-aware
                        if start_date.tzinfo is None:
                            from django.utils.timezone import make_aware
                            import pytz
                            start_date = make_aware(start_date, pytz.UTC)
                        if end_date.tzinfo is None:
                            from django.utils.timezone import make_aware
                            import pytz
                            end_date = make_aware(end_date, pytz.UTC)
                    
                    # Get source entity info
                    source_entity_id_api = deal_data.get('sourceEntityId')
                    source_entity_name = deal_data.get('sourceEntityName', '')
                    
                    # Try to identify bank from deal data
                    bank = None
                    
                    # Strategy 1: Use bank_code parameter if provided (HIGHEST PRIORITY)
                    # This ensures bank is correctly identified when scraping for a specific bank/card
                    if bank_code:
                        bank_code_upper = str(bank_code).upper()
                        bank = Bank.objects.filter(code__iexact=bank_code_upper).first()
                        if not bank:
                            # Handle common variations: AL_BARAKA vs AL_BARAKA_BANK, etc.
                            base_code = (
                                bank_code_upper.replace('_BANK', '')
                                .replace('_LIMITED', '')
                                .replace('_LTD', '')
                                .strip('_')
                            )
                            bank = Bank.objects.filter(code__iexact=base_code).first()
                            if not bank:
                                bank = Bank.objects.filter(code__iexact=f"{base_code}_BANK").first()
                        if bank:
                            logger.debug(f"✅ Matched bank from bank_code parameter: {bank.name}")
                    
                    # Strategy 2: Match by sourceEntityName
                    if not bank and source_entity_name:
                        # Try exact match first
                        bank = Bank.objects.filter(name__iexact=source_entity_name).first()
                        
                        # Try partial match
                        if not bank:
                            for bank_obj in Bank.objects.all():
                                if bank_obj.name.lower() in source_entity_name.lower() or source_entity_name.lower() in bank_obj.name.lower():
                                    bank = bank_obj
                                    break
                    
                    # Fallback: First try to match from sourceEntityId from API response
                    if not bank and source_entity_id_api:
                        try:
                            source_entity_id_int = int(source_entity_id_api)
                            bank_code_from_id = PEEKABOO_ID_TO_BANK.get(source_entity_id_int)
                            if bank_code_from_id:
                                bank = Bank.objects.filter(code__iexact=bank_code_from_id).first()
                        except (ValueError, TypeError):
                            pass
                    
                    # Get associations (cards linked to this deal)
                    associations = deal_data.get('associations', [])
                    linked_card_ids = []
                    
                    if bank and associations:
                        for assoc in associations:
                            card_name = assoc.get('name', '')
                            if not card_name:
                                continue
                            
                            # Try multiple matching strategies
                            card = None
                            
                            # Strategy 1: Exact match
                            card = CreditCard.objects.filter(
                                bank=bank,
                                name__iexact=card_name
                            ).first()
                            
                            # Strategy 2: Normalized match (remove "Card" suffix)
                            if not card:
                                normalized_name = card_name.replace('Card', '').replace('card', '').strip()
                                card = CreditCard.objects.filter(
                                    bank=bank,
                                    name__icontains=normalized_name
                                ).first()
                            
                            # Strategy 3: Keyword-based matching
                            if not card:
                                keywords = [w for w in card_name.lower().split() if w not in ['card', 'debit', 'credit', 'visa', 'mastercard']]
                                if keywords:
                                    query = CreditCard.objects.filter(bank=bank)
                                    for keyword in keywords[:2]:  # Use first 2 keywords
                                        query = query.filter(name__icontains=keyword)
                                    card = query.first()
                            
                            # Strategy 4: Match by card type
                            if not card:
                                card_type_hint = 'DEBIT' if 'debit' in card_name.lower() else 'CREDIT'
                                card = CreditCard.objects.filter(
                                    bank=bank,
                                    card_type=card_type_hint
                                ).first()
                            
                            if card:
                                if card.id not in linked_card_ids:
                                    linked_card_ids.append(card.id)
                                    logger.debug(f"✅ Linked deal {deal_id} to card: {card.name} (from association: {card_name})")
                                    
                                    # Store associationTypeId and card slug in CreditCard for future use
                                    type_id = assoc.get('typeId')
                                    if type_id and not card.peekaboo_association_type_id:
                                        card.peekaboo_association_type_id = type_id
                                        card.save(update_fields=['peekaboo_association_type_id'])
                                    
                                    # Generate card slug if not exists
                                    if not card.peekaboo_card_slug:
                                        card_slug = card_name.lower().replace(' ', '-').replace('card', '').replace('debit', '').replace('credit', '').strip('-')
                                        card.peekaboo_card_slug = card_slug
                                        card.save(update_fields=['peekaboo_card_slug'])
                            else:
                                logger.debug(f"⚠️  Could not match association '{card_name}' to any card for bank {bank.name}")
                    
                    # IMPORTANT: If card_id is provided, ALWAYS link to that card (even if already linked via associations)
                    # This ensures deals scraped in "Bank & Card" tab are linked to the selected card
                    if card_id:
                        if not bank:
                            # Try to get bank from card if bank wasn't found
                            try:
                                card_obj = CreditCard.objects.get(id=card_id)
                                bank = card_obj.bank
                                logger.debug(f"✅ Got bank from card: {bank.name if bank else 'None'}")
                            except CreditCard.DoesNotExist:
                                logger.warning(f"Card ID {card_id} not found")
                        
                        if bank:
                            try:
                                specific_card = CreditCard.objects.get(id=card_id, bank=bank)
                                if specific_card.id not in linked_card_ids:
                                    linked_card_ids.append(specific_card.id)
                                    logger.info(f"✅ Linked deal {deal_id} to specific card {specific_card.name} (card_id={card_id}, bank={bank.name})")
                            except CreditCard.DoesNotExist:
                                logger.warning(f"Card ID {card_id} not found for bank {bank.name}")
                        else:
                            logger.warning(f"Cannot link card {card_id} - bank is None")
                    
                    # Only use bank-level fallback if NO card_id was provided (general scraping)
                    # This prevents linking deals to all cards when user selected a specific card
                    if not linked_card_ids and not card_id and bank:
                        # This is general bank scraping, so link to all active cards from that bank
                        bank_cards = CreditCard.objects.filter(bank=bank, is_active=True)
                        if bank_cards.exists():
                            for bank_card in bank_cards:
                                if bank_card.id not in linked_card_ids:
                                    linked_card_ids.append(bank_card.id)
                            logger.debug(f"✅ Linked deal {deal_id} to {len(linked_card_ids)} cards from bank {bank.name} (general bank scraping)")
                    
                    # Prepare deal data
                    # IMPORTANT: store category so Smart Recommendations can filter like Peekaboo /places/{categoryId}/{slug}
                    raw_category = (
                        deal_data.get('categoryName')
                        or deal_data.get('category')
                        or deal_data.get('dealCategory')
                        or ''
                    )
                    # Sometimes category is an object/dict; try common keys
                    if isinstance(raw_category, dict):
                        raw_category = raw_category.get('name') or raw_category.get('categoryName') or raw_category.get('title') or ''

                    deal_defaults = {
                        'title': deal_data.get('title', ''),
                        'description': deal_data.get('description', ''),
                        'percentage_value': deal_data.get('percentageValue', 0),
                        'discount_amount': deal_data.get('discountAmount', deal_data.get('discount_amount', None)),
                        'start_date': start_date,
                        'end_date': end_date,
                        'target_entity_name': deal_data.get('targetEntityName', ''),
                        'target_entity_logo': deal_data.get('targetEntityLogo', ''),
                        'source_entity_name': source_entity_name,
                        'source_entity_logo': deal_data.get('sourceEntityLogo', ''),
                        'associations': associations,  # Store raw associations JSON
                        'category': (str(raw_category).strip()[:100] if raw_category else None),
                        'city': city.get('name', ''),
                        'last_scraped_at': timezone.now(),
                    }
                    
                    # Only update bank if it was found
                    if bank:
                        deal_defaults['bank'] = bank
                        logger.debug(f"✅ Set bank for deal {deal_id}: {bank.name} (code: {bank.code})")
                    else:
                        logger.warning(f"⚠️  No bank found for deal {deal_id} (bank_code={bank_code}, source_entity_name={source_entity_name})")
                    
                    # Check if deal already exists
                    existing_deal = PeekabooDeal.objects.filter(deal_id=deal_id).first()
                    
                    if existing_deal:
                        # Update only if data has changed
                        needs_update = False
                        for key, value in deal_defaults.items():
                            if key == 'bank' and existing_deal.bank != value:
                                needs_update = True
                                break
                            elif key != 'bank' and getattr(existing_deal, key, None) != value:
                                needs_update = True
                                break
                        
                        if needs_update:
                            for key, value in deal_defaults.items():
                                setattr(existing_deal, key, value)
                            # Always update last_scraped_at when updating deal
                            existing_deal.last_scraped_at = timezone.now()
                            existing_deal.save()
                            updated_count += 1
                            logger.debug(f"✅ Updated deal {deal_id}: {deal_data.get('title', '')[:50]}")
                        else:
                            # Just update last_scraped_at
                            existing_deal.last_scraped_at = timezone.now()
                            existing_deal.save(update_fields=['last_scraped_at'])
                            skipped_count += 1
                        
                        # Update linked cards (always update, even if empty list to clear old links)
                        # IMPORTANT: Always update linked cards, even for existing deals
                        # This ensures deals are linked when card_id is provided
                        existing_deal.linked_cards.set(linked_card_ids)
                        if linked_card_ids:
                            # Reduced logging - only log significant updates
                            if len(linked_card_ids) > 5:
                                try:
                                    card_names = [CreditCard.objects.get(id=cid).name for cid in linked_card_ids]
                                    logger.debug(f"Updated linked cards for deal {deal_id}: {len(linked_card_ids)} cards")
                                except Exception as e:
                                    logger.debug(f"Updated linked cards for deal {deal_id}: {len(linked_card_ids)} cards")
                        else:
                            # Bank-wide deals often don't include usable association data for card linking.
                            # Don't spam terminal for every deal; keep this as debug.
                            logger.debug(f"No cards linked for deal {deal_id} (card_id={card_id}, bank={bank.name if bank else 'None'})")
                    else:
                        # Create new deal
                        deal = PeekabooDeal.objects.create(
                            deal_id=deal_id,
                            **deal_defaults
                        )
                        
                        # Set linked cards (always set, even if empty)
                        deal.linked_cards.set(linked_card_ids)
                        if linked_card_ids:
                            try:
                                card_names = [CreditCard.objects.get(id=cid).name for cid in linked_card_ids]
                                logger.info(f"✅ Created deal {deal_id} with {len(linked_card_ids)} linked cards - {card_names}")
                            except Exception as e:
                                logger.info(f"✅ Created deal {deal_id} with {len(linked_card_ids)} linked cards")
                        else:
                            # Bank-wide deals often don't include usable association data for card linking.
                            # Don't spam terminal for every deal; keep this as debug.
                            logger.debug(f"Created deal {deal_id} with NO linked cards (card_id={card_id}, bank={bank.name if bank else 'None'})")
                        
                        created_count += 1
                        logger.debug(f"✅ Created deal {deal_id}: {deal_data.get('title', '')[:50]}")
                    
                    # Mark as processed successfully
                    processed = True
                    
            except Exception as e:
                error_msg = str(e).lower()
                # Check if it's a database lock error (SQLite specific errors)
                is_lock_error = (
                    'database is locked' in error_msg or 
                    'locked' in error_msg or
                    'operationalerror' in error_msg or
                    'sqlite3.operationalerror' in error_msg
                )
                
                if is_lock_error:
                    retry_count += 1
                    if retry_count < max_retries:
                        # Wait before retrying (exponential backoff with jitter)
                        wait_time = retry_delay * (2 ** retry_count) + (retry_count * 0.1)
                        # Cap max wait time at 2 seconds
                        wait_time = min(wait_time, 2.0)
                        time.sleep(wait_time)
                        logger.debug(f"Database locked for deal {deal_data.get('dealId', 'unknown')}, retrying ({retry_count}/{max_retries}) after {wait_time:.2f}s...")
                        continue
                    else:
                        # Max retries reached - log and skip
                        logger.warning(f"⚠️  Skipping deal {deal_data.get('dealId', 'unknown')}: database is locked (max retries {max_retries} reached)")
                        skipped_count += 1
                        processed = True  # Mark as processed to exit loop
                else:
                    # Other error - don't retry
                    logger.error(f"❌ Error processing deal {deal_data.get('dealId', 'unknown')}: {str(e)}")
                    skipped_count += 1
                    processed = True  # Mark as processed to exit loop
    
    return (created_count, updated_count, skipped_count)
