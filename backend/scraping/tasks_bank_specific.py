# scraping/tasks_bank_specific.py
# Celery tasks for scraping bank-specific deals

import logging
from celery import shared_task
from django.db import transaction
from django.utils import timezone

from scraping.scrapers.bank_specific_scraper import BankSpecificScraper

logger = logging.getLogger(__name__)

# Import models
try:
    from offers.models_bank_specific import (
        BankSpecificCity, BankSpecificCategory, 
        BankSpecificEntity, BankSpecificCardAssociation
    )
    from cards.models import Bank, CreditCard
except ImportError as e:
    logger.warning(f"Bank-specific models not found: {e}")
    BankSpecificCity = None
    BankSpecificCategory = None
    BankSpecificEntity = None
    BankSpecificCardAssociation = None
    Bank = None
    CreditCard = None

@shared_task
def scrape_bank_specific_cities(bank_code: str):
    """Scrape cities for a specific bank"""
    if not BankSpecificCity or not Bank:
        logger.error("Models not available")
        return 0
    
    scraper = BankSpecificScraper()
    bank = scraper._get_bank_from_code(bank_code)
    
    if not bank:
        logger.error(f"Bank not found: {bank_code}")
        return 0
    
    cities_data = scraper.scrape_cities(bank_code)
    
    created_count = 0
    updated_count = 0
    
    with transaction.atomic():
        for city_data in cities_data:
            try:
                city_id = city_data.get('id')
                if not city_id:
                    continue
                
                city, created = BankSpecificCity.objects.update_or_create(
                    bank=bank,
                    city_id=city_id,
                    defaults={
                        'name': city_data.get('city', ''),
                        'slug': city_data.get('slug', ''),
                        'country': city_data.get('country', 'Pakistan'),
                        'latitude': city_data.get('latitude'),
                        'longitude': city_data.get('longitude'),
                        'image': city_data.get('image'),
                        'is_active': True,
                    }
                )
                
                if created:
                    created_count += 1
                else:
                    updated_count += 1
            except Exception as e:
                logger.error(f"Error processing city: {str(e)}")
                continue
    
    logger.info(f"✅ Scraped cities for {bank_code}: {created_count} created, {updated_count} updated")
    return created_count + updated_count

@shared_task
def scrape_bank_specific_categories(bank_code: str):
    """Scrape categories for a specific bank"""
    if not BankSpecificCategory or not Bank:
        logger.error("Models not available")
        return 0
    
    scraper = BankSpecificScraper()
    bank = scraper._get_bank_from_code(bank_code)
    
    if not bank:
        logger.error(f"Bank not found: {bank_code}")
        return 0
    
    # Try with Karachi city slug from database if available
    city_slug = 'karachi'  # Default
    try:
        karachi_city = BankSpecificCity.objects.filter(bank=bank, name__icontains='Karachi').first()
        if karachi_city and karachi_city.slug:
            city_slug = karachi_city.slug
        elif not karachi_city:
            # If Karachi not found, try to get any city slug
            any_city = BankSpecificCity.objects.filter(bank=bank).first()
            if any_city and any_city.slug:
                city_slug = any_city.slug
    except Exception as e:
        logger.debug(f"Could not get city slug from DB: {e}")
    
    categories_data = scraper.scrape_categories(bank_code, city=city_slug)
    
    created_count = 0
    updated_count = 0
    
    with transaction.atomic():
        for cat_data in categories_data:
            try:
                category_id = cat_data.get('id')
                if not category_id:
                    continue
                
                category, created = BankSpecificCategory.objects.update_or_create(
                    bank=bank,
                    category_id=category_id,
                    defaults={
                        'name': cat_data.get('name', ''),
                        'order': cat_data.get('order', 0),
                        'category_logo_url': cat_data.get('categoryLogoUrl'),
                        'image': cat_data.get('image'),
                        'is_active': True,
                    }
                )
                
                if created:
                    created_count += 1
                else:
                    updated_count += 1
            except Exception as e:
                logger.error(f"Error processing category: {str(e)}")
                continue
    
    logger.info(f"✅ Scraped categories for {bank_code}: {created_count} created, {updated_count} updated")
    return created_count + updated_count

@shared_task
def scrape_bank_specific_entities(bank_code: str, city_id: int = None, city_slug: str = None, city_name: str = None):
    """Scrape entities/merchants for a specific bank and city"""
    if not BankSpecificEntity or not Bank:
        logger.error("Models not available")
        return 0
    
    scraper = BankSpecificScraper()
    bank = scraper._get_bank_from_code(bank_code)
    
    if not bank:
        logger.error(f"Bank not found: {bank_code}")
        return 0
    
    # Get city name from database if not provided
    if not city_name and city_slug:
        try:
            city_obj = BankSpecificCity.objects.filter(bank=bank, slug=city_slug).first()
            if city_obj:
                city_name = city_obj.name
        except:
            pass
    
    entities_data = scraper.scrape_entities(bank_code, city_id=city_id, city_slug=city_slug, city_name=city_name or 'Karachi')
    
    created_count = 0
    updated_count = 0
    
    with transaction.atomic():
        for entity_data in entities_data:
            try:
                entity_id = entity_data.get('entityId')
                if not entity_id:
                    continue
                
                # Parse gallery and menu (comma-separated strings to arrays)
                gallery = entity_data.get('gallery', '')
                if isinstance(gallery, str):
                    gallery = [url.strip() for url in gallery.split(',') if url.strip()]
                
                menu = entity_data.get('menu', '')
                if isinstance(menu, str):
                    menu = [url.strip() for url in menu.split(',') if url.strip()]
                
                # Parse tags
                tags = entity_data.get('tags', [])
                if not isinstance(tags, list):
                    tags = []
                
                entity, created = BankSpecificEntity.objects.update_or_create(
                    bank=bank,
                    entity_id=entity_id,
                    defaults={
                        'name': entity_data.get('name', ''),
                        'slug': entity_data.get('slug', ''),
                        'description': entity_data.get('description'),
                        'package': entity_data.get('package'),
                        'contact_number': entity_data.get('contactNumber'),
                        'keywords': entity_data.get('keywords'),
                        'entity_rating': entity_data.get('entityRating'),
                        'cover': entity_data.get('cover'),
                        'logo': entity_data.get('logo'),
                        'gallery': gallery,
                        'menu': menu,
                        'facebook': entity_data.get('facebook'),
                        'instagram': entity_data.get('instagram'),
                        'website': entity_data.get('website'),
                        'email': entity_data.get('email'),
                        'whatsapp': entity_data.get('whatsapp'),
                        'android': entity_data.get('android'),
                        'ios': entity_data.get('ios'),
                        'total_branches': entity_data.get('totalBranches', 0),
                        'total_open_branches': entity_data.get('totalOpenBranches', 0),
                        'total_associated_deals': entity_data.get('totalAssociatedDeals', 0),
                        'max_discount': entity_data.get('maxDiscount', 0),
                        'wishlist_count': entity_data.get('wishlistCount', 0),
                        'review_counts': entity_data.get('reviewCounts', 0),
                        'tags': tags,
                        'nearest_branch_id': entity_data.get('nearestbranchId'),
                        'nearest_branch_name': entity_data.get('nearestBranchName'),
                        'nearest_branch_lat_long': entity_data.get('nearestBranchLatLong'),
                        'nearest_branch_distance': entity_data.get('nearestBranchDistance'),
                        'nearest_branch_open_now': entity_data.get('nearestBranchOpenNow') == 'true',
                        'nearest_branch_contact_number': entity_data.get('nearestBranchContactNumber'),
                        'branches': entity_data.get('branches'),
                        'online_service_available': entity_data.get('onlineServiceAvailable', False),
                        'is_active': True,
                        'last_scraped_at': timezone.now(),
                    }
                )
                
                if created:
                    created_count += 1
                else:
                    updated_count += 1
            except Exception as e:
                logger.error(f"Error processing entity: {str(e)}")
                continue
    
    logger.info(f"✅ Scraped entities for {bank_code}: {created_count} created, {updated_count} updated")
    return created_count + updated_count

@shared_task
def scrape_bank_specific_card_associations(bank_code: str):
    """Scrape card associations for a specific bank"""
    if not BankSpecificCardAssociation or not Bank or not CreditCard:
        logger.error("Models not available")
        return 0
    
    scraper = BankSpecificScraper()
    bank = scraper._get_bank_from_code(bank_code)
    
    if not bank:
        logger.error(f"Bank not found: {bank_code}")
        return 0
    
    # Try with Karachi city slug from database if available
    city_slug = 'karachi'  # Default
    try:
        karachi_city = BankSpecificCity.objects.filter(bank=bank, name__icontains='Karachi').first()
        if karachi_city and karachi_city.slug:
            city_slug = karachi_city.slug
        elif not karachi_city:
            # If Karachi not found, try to get any city slug
            any_city = BankSpecificCity.objects.filter(bank=bank).first()
            if any_city and any_city.slug:
                city_slug = any_city.slug
    except Exception as e:
        logger.debug(f"Could not get city slug from DB: {e}")
    
    associations_data = scraper.scrape_card_associations(bank_code, city=city_slug)
    
    created_count = 0
    updated_count = 0
    
    with transaction.atomic():
        for assoc_data in associations_data:
            try:
                association_id = assoc_data.get('associationId')
                if not association_id:
                    continue
                
                type_name = assoc_data.get('typeName', '')
                card_type = assoc_data.get('cardType', '')
                
                # Try to match with CreditCard
                linked_card = None
                if type_name and bank:
                    # Try to find matching card
                    card_name_words = type_name.lower().replace('card', '').strip().split()
                    for word in card_name_words:
                        if word not in ['debit', 'credit', 'visa', 'mastercard', 'platinum', 'gold', 'silver', 'classic', 'world', 'elite']:
                            linked_card = CreditCard.objects.filter(
                                bank=bank,
                                name__icontains=word
                            ).first()
                            if linked_card:
                                break
                
                association, created = BankSpecificCardAssociation.objects.update_or_create(
                    bank=bank,
                    association_id=association_id,
                    defaults={
                        'type_id': assoc_data.get('typeId', 0),
                        'type_name': type_name,
                        'card_type': card_type,
                        'image': assoc_data.get('image'),
                        'description': assoc_data.get('description'),
                        'additional_info': assoc_data.get('additionalInfo'),
                        'amenities': assoc_data.get('amenities', {}),
                        'amenity_count': assoc_data.get('amenityCount', 0),
                        'deal_count': assoc_data.get('dealCount', 0),
                        'linked_card': linked_card,
                        'is_active': True,
                        'last_scraped_at': timezone.now(),
                    }
                )
                
                if created:
                    created_count += 1
                else:
                    updated_count += 1
            except Exception as e:
                logger.error(f"Error processing card association: {str(e)}")
                continue
    
    logger.info(f"✅ Scraped card associations for {bank_code}: {created_count} created, {updated_count} updated")
    return created_count + updated_count

@shared_task
def scrape_bank_specific_all(bank_code: str, city_id: int = None, city_slug: str = None):
    """Scrape all data for a bank (cities, categories, entities, card associations)"""
    logger.info(f"Starting comprehensive scrape for {bank_code}")
    
    # Scrape cities
    scrape_bank_specific_cities(bank_code)
    
    # Scrape categories
    scrape_bank_specific_categories(bank_code)
    
    # Scrape card associations
    scrape_bank_specific_card_associations(bank_code)
    
    # Scrape entities (for all cities or specific city)
    if city_id or city_slug:
        scrape_bank_specific_entities(bank_code, city_id=city_id, city_slug=city_slug)
    else:
        # Scrape for all cities - get city names from database
        scraper = BankSpecificScraper()
        bank = scraper._get_bank_from_code(bank_code)
        if bank:
            try:
                cities = BankSpecificCity.objects.filter(bank=bank)[:10]
                for city_obj in cities:
                    city_slug = city_obj.slug
                    city_name = city_obj.name
                    if city_slug or city_name:
                        scrape_bank_specific_entities(bank_code, city_slug=city_slug, city_name=city_name)
            except Exception as e:
                logger.warning(f"Could not get cities from DB, using default: {e}")
                # Fallback: scrape for Karachi
                scrape_bank_specific_entities(bank_code, city_slug='karachi', city_name='Karachi')
        else:
            # Fallback: scrape for Karachi
            scrape_bank_specific_entities(bank_code, city_slug='karachi', city_name='Karachi')
    
    logger.info(f"✅ Completed comprehensive scrape for {bank_code}")

