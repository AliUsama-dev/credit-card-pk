# scraping/scrapers/partners_scraper.py
# Scraper for Peekaboo Partners Offers (bank detail pages)

from datetime import time
import json
import logging
import re
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from django.utils import timezone
from cards.models import Bank

logger = logging.getLogger(__name__)

class PartnersOffersScraper:
    """Scraper for Peekaboo Partners Offers bank detail pages"""
    
    def __init__(self):
        self.base_url = 'https://peekaboo.guru'
        self.api_base = 'https://peekaboo.guru'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            # IMPORTANT: don't request brotli ("br") here. Python `requests` does not reliably decode br
            # unless optional dependencies are installed, which causes garbled responses / JSONDecodeError.
            'Accept-Encoding': 'gzip, deflate',
            'Referer': 'https://peekaboo.guru/',
            'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpZCI6NzIsInJvbGUiOiJndWVzdCIsImlhdCI6MTU1MzcwMDgwNiwianRpIjoiUEpJMXFTb2ktQzRBZFJWcm9nb3RNV2UzV3VXcFdXTm0ifQ.2mb26xL4Qt7FfBQZ-XQvp-fhecMpaVUVXWp_GEST_6U',
            'medium': 'WEB',
            'version': '2.1.0.2',
            'Content-Type': 'application/json',
        }
    
    def get_all_partner_banks(self, city: str = 'karachi') -> List[Dict]:
        """Get all partner banks from city page - try API first, then HTML fallback"""
        banks = []
        city_capitalized = city.capitalize()
        
        # Try API endpoint v6/sourceEntities (POST method)
        try:
            api_url = f"{self.api_base}/api/v6/sourceEntities"
            payload = {
                'city': city_capitalized,
                'country': 'Pakistan',
                'language': 'en',
                'limit': 1000,
                'offset': 0,
            }
            
            response = requests.post(api_url, json=payload, headers=self.headers, timeout=30)
            if response.status_code == 200:
                data = response.json()
                entities = data if isinstance(data, list) else data.get('entities', []) or data.get('sourceEntities', [])
                
                for entity in entities:
                    # Filter for banks
                    entity_name = entity.get('name', '').lower()
                    if any(keyword in entity_name for keyword in ['bank', 'limited', 'ltd']):
                        entity_id = entity.get('entityId') or entity.get('id') or entity.get('sourceEntityId')
                        if entity_id:
                            banks.append({
                                'entity_id': entity_id,
                                'slug': self._slugify(entity.get('name', '')),
                                'name': entity.get('name', ''),
                                'url': f"{self.base_url}/{city}/detail/{entity_id}/{self._slugify(entity.get('name', ''))}",
                            })
                logger.info(f"Found {len(banks)} partner banks from API v6")
                if banks:
                    return banks
        except Exception as e:
            logger.debug(f"API v6 method failed: {str(e)}")
        
        # Try API endpoint v5 (GET method)
        try:
            # Get city coordinates (approximate)
            city_coords = {
                'karachi': {'lat': 24.8607, 'long': 67.0011},
                'lahore': {'lat': 31.5204, 'long': 74.3587},
                'islamabad': {'lat': 33.6844, 'long': 73.0479},
            }
            coords = city_coords.get(city.lower(), {'lat': 30.3753, 'long': 69.3451})
            
            api_url = f"{self.api_base}/api/v5/entity/_all/branch/_all/sourceEntities/_all"
            params = {
                'city': city_capitalized,
                'country': 'Pakistan',
                'entity': 'All',
                'language': 'en',
                'lat': coords['lat'],
                'long': coords['long'],
                'limit': 1000,
                'offset': 0,
            }
            
            response = requests.get(api_url, params=params, headers=self.headers, timeout=30)
            if response.status_code == 200:
                data = response.json()
                entities = data if isinstance(data, list) else []
                
                for entity in entities:
                    # Filter for banks
                    entity_name = entity.get('name', '').lower()
                    if any(keyword in entity_name for keyword in ['bank', 'limited', 'ltd']):
                        entity_id = entity.get('entityId') or entity.get('id') or entity.get('sourceEntityId')
                        if entity_id:
                            banks.append({
                                'entity_id': entity_id,
                                'slug': self._slugify(entity.get('name', '')),
                                'name': entity.get('name', ''),
                                'url': f"{self.base_url}/{city}/detail/{entity_id}/{self._slugify(entity.get('name', ''))}",
                            })
                logger.info(f"Found {len(banks)} partner banks from API v5")
                if banks:
                    return banks
        except Exception as e:
            logger.debug(f"API v5 method failed: {str(e)}")
        
        # Fallback to HTML parsing - try to find bank links in the page
        url = f"{self.base_url}/{city}"
        logger.info(f"Fetching partner banks from HTML: {url}")
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all links that match bank detail pattern
            bank_links = soup.find_all('a', href=re.compile(r'/detail/\d+/'))
            
            # Also try to find links in script tags (JSON data)
            script_tags = soup.find_all('script', type=re.compile(r'application/json|text/javascript', re.I))
            for script in script_tags:
                try:
                    script_content = script.string
                    if script_content and ('bank' in script_content.lower() or 'entity' in script_content.lower()):
                        # Try to extract JSON data
                        json_match = re.search(r'\{.*"entities?":\s*\[.*\]', script_content, re.DOTALL)
                        if json_match:
                            try:
                                json_data = json.loads(json_match.group(0))
                                entities = json_data.get('entities', []) or json_data.get('sourceEntities', [])
                                for entity in entities:
                                    entity_name = entity.get('name', '').lower()
                                    if any(keyword in entity_name for keyword in ['bank', 'limited', 'ltd']):
                                        entity_id = entity.get('entityId') or entity.get('id') or entity.get('sourceEntityId')
                                        if entity_id:
                                            banks.append({
                                                'entity_id': entity_id,
                                                'slug': self._slugify(entity.get('name', '')),
                                                'name': entity.get('name', ''),
                                                'url': f"{self.base_url}/{city}/detail/{entity_id}/{self._slugify(entity.get('name', ''))}",
                                            })
                            except (json.JSONDecodeError, KeyError):
                                pass
                except Exception:
                    pass
            
            # Process HTML links
            for link in bank_links:
                href = link.get('href', '')
                if '/detail/' in href:
                    # Extract entity ID and slug from URL
                    match = re.search(r'/detail/(\d+)/([^/\?]+)', href)
                    if match:
                        entity_id = int(match.group(1))
                        slug = match.group(2)
                        
                        bank_name = link.get_text(strip=True)
                        if not bank_name:
                            bank_name = slug.replace('-', ' ').title()
                        
                        # Check if we already have this bank
                        if not any(b['entity_id'] == entity_id for b in banks):
                            banks.append({
                                'entity_id': entity_id,
                                'slug': slug,
                                'name': bank_name,
                                'url': urljoin(self.base_url, href) if not href.startswith('http') else href,
                            })
            
            logger.info(f"Found {len(banks)} partner banks from HTML")
            return banks
            
        except Exception as e:
            logger.error(f"Error fetching partner banks: {str(e)}", exc_info=True)
            return []
    
    def scrape_bank_detail(self, entity_id: int, slug: str, city: str = 'karachi') -> Optional[Dict]:
        """Scrape bank detail page and extract cards and offers - try API first, then HTML"""
        url = f"{self.base_url}/{city}/detail/{entity_id}/{slug}"
        logger.info(f"Scraping bank detail: {url}")
        
        city_capitalized = city.capitalize()
        city_coords = {
            'karachi': {'lat': 24.8607, 'long': 67.0011},
            'lahore': {'lat': 31.5204, 'long': 74.3587},
            'islamabad': {'lat': 33.6844, 'long': 73.0479},
            'rawalpindi': {'lat': 33.5651, 'long': 73.0169},
            'faisalabad': {'lat': 31.4504, 'long': 73.1350},
            'multan': {'lat': 30.1575, 'long': 71.5249},
            'hyderabad': {'lat': 25.3960, 'long': 68.3578},
            'peshawar': {'lat': 34.0151, 'long': 71.5249},
            'quetta': {'lat': 30.1798, 'long': 66.9750},
        }
        coords = city_coords.get(city.lower(), {'lat': 30.3753, 'long': 69.3451})
        
        bank_data = {
            'entity_id': entity_id,
            'slug': slug,
            'name': slug.replace('-', ' ').title(),
            'description': '',
            'logo': '',
            'website': '',
            'cards': [],
            'offers': [],
        }
        
        # Try to get card associations from API
        # Note: entity_id might be entityId, but associationType endpoint needs sourceEntityId
        # Try both entity_id as sourceEntityId and also try to get sourceEntityId from bank info
        source_entity_id = entity_id  # Default to entity_id
        
        # First, try to get bank info to find the correct sourceEntityId
        try:
            # Try v6 sourceEntity endpoint to get bank details
            api_url = f"{self.api_base}/api/v6/sourceEntity/{entity_id}"
            params = {
                'city': city_capitalized,
                'country': 'Pakistan',
                'language': 'en',
            }
            response = requests.get(api_url, headers=self.headers, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict):
                    bank_data['name'] = data.get('name', bank_data['name'])
                    bank_data['description'] = data.get('description', '')
                    bank_data['logo'] = data.get('logo', '')
                    # Try to get sourceEntityId if different from entityId
                    source_entity_id = data.get('sourceEntityId') or data.get('id') or entity_id
        except Exception as e:
            logger.debug(f"v6 sourceEntity API failed: {str(e)}")
        
        # Now try to get card associations using sourceEntityId
        try:
            api_url = f"{self.api_base}/api/sourceEntity/{source_entity_id}/associationType/_all"
            params = {
                'city': city_capitalized,
                'country': 'Pakistan',
                'entity': bank_data['name'],
                'language': 'en',
                'lat': coords['lat'],
                'long': coords['long'],
                'limit': 50,
                'offset': 0,
            }
            
            # Add retry logic for connection errors
            max_retries = 3
            retry_delay = 2
            response = None
            
            for attempt in range(max_retries):
                try:
                    response = requests.get(api_url, params=params, headers=self.headers, timeout=60)
                    break
                except (requests.exceptions.ChunkedEncodingError,
                        requests.exceptions.ConnectionError,
                        requests.exceptions.Timeout,
                        requests.exceptions.ProtocolError,
                        ConnectionResetError) as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"⚠️  Connection error for associationType API (attempt {attempt + 1}/{max_retries}): {str(e)[:100]}. Retrying in {retry_delay}s...")
                        time.sleep(retry_delay)
                        retry_delay *= 2
                    else:
                        logger.error(f"❌ Connection failed for associationType API after {max_retries} attempts: {str(e)[:200]}")
                        raise
            
            if not response:
                logger.error(f"❌ Failed to get response for associationType API after {max_retries} attempts")
                # We're not inside a loop over cards/banks here, so just abort this bank detail scrape.
                return None
            
            if response.status_code == 200:
                # Some banks return HTML or empty responses here, which breaks response.json()
                try:
                    associations_data = response.json()
                except Exception as e:
                    logger.warning(
                        f"AssociationType API returned non-JSON for {bank_data.get('name')} "
                        f"(status={response.status_code}, content_type={response.headers.get('content-type')}): "
                        f"{response.text[:200]}"
                    )
                    associations_data = []
                logger.info(f"AssociationType API response: {len(associations_data) if isinstance(associations_data, list) else 'not a list'} items")
                if isinstance(associations_data, list):
                    for assoc in associations_data:
                        if isinstance(assoc, dict):
                            card_name = assoc.get('typeName', '') or assoc.get('name', '') or assoc.get('cardName', '')
                            if card_name and len(card_name) > 3:
                                association_id = assoc.get('associationId') or assoc.get('id') or assoc.get('association_id')
                                association_type_id = assoc.get('typeId') or assoc.get('associationTypeId') or assoc.get('association_type_id')
                                
                                # Generate card slug
                                card_slug = assoc.get('slug', '') or self._slugify(card_name)
                                
                                # Log if missing IDs
                                if not association_id or not association_type_id:
                                    logger.warning(f"Card {card_name} missing IDs: association_id={association_id}, association_type_id={association_type_id}")
                                    logger.debug(f"Full association data: {assoc}")
                                
                                bank_data['cards'].append({
                                    'name': card_name,
                                    'slug': card_slug,
                                    'description': assoc.get('description', ''),
                                    'image': assoc.get('image', '') or assoc.get('logo', ''),
                                    'card_type': self._detect_card_type(card_name),
                                    'association_id': association_id,  # Store for scraping deals
                                    'association_type_id': association_type_id,  # Store for scraping deals
                                    # IMPORTANT: Deals endpoint uses Peekaboo "sourceEntityId" (not entityId).
                                    # associationType API returns sourceEntityId; prefer it if present.
                                    'source_entity_id': assoc.get('sourceEntityId') or source_entity_id,  # Store for scraping deals
                                })
                    logger.info(f"Scraped {len(bank_data['cards'])} cards from associationType API for {bank_data['name']}")
                else:
                    logger.warning(f"AssociationType API returned non-list data: {type(associations_data)}")
        except Exception as e:
            logger.error(f"AssociationType API method failed: {str(e)}", exc_info=True)
        
        # Scrape deals for each card using the places URL pattern
        # For each card, we need to scrape deals using: /places/_all/all?ai={association_id}&associationTypeId={association_type_id}&card={card_slug}&discounts={bank_slug}&ei={entity_id}&sourceEntityId={source_entity_id}
        cards_with_ids = 0
        cards_without_ids = 0
        
        for card_data in bank_data['cards']:
            association_id = card_data.get('association_id')
            association_type_id = card_data.get('association_type_id')
            
            if not association_id or not association_type_id:
                cards_without_ids += 1
                logger.warning(f"Card {card_data.get('name', 'Unknown')} missing required IDs: association_id={association_id}, association_type_id={association_type_id}")
                continue
            
            cards_with_ids += 1
            
            try:
                # Construct places URL (matching Peekaboo UI exactly)
                places_url = f"{self.base_url}/{city}/places/_all/all"
                places_params = {
                    'ai': str(association_id),
                    'associationTypeId': str(association_type_id),
                    'card': card_data['slug'],
                    'discounts': slug,  # Bank slug
                    'ei': str(entity_id),
                    'sourceEntityId': str(card_data.get('source_entity_id', source_entity_id)),
                    'selfDeal': 'true',  # CRITICAL: Match Peekaboo UI URL exactly
                }
                
                # Try v8/entity/deals API first (more reliable)
                # IMPORTANT: Peekaboo UI uses selfDeal=true in the places URL for card-specific views.
                # Without this, the API returns extra deals that don't match the UI.
                api_url = f"{self.api_base}/api/v8/entity/deals"
                payload = {
                    'city': city_capitalized,
                    'country': 'Pakistan',
                    'entity': 'All',
                    'language': 'en',
                    'lat': coords['lat'],
                    'long': coords['long'],
                    'limit': 1000,  # Increased from 100 to get all deals
                    'offset': 0,
                    'sourceEntityId': str(card_data.get('source_entity_id', source_entity_id)),
                    'associationTypeId': str(association_type_id),
                    'ai': str(association_id),
                    'card': card_data['slug'],
                    'discounts': slug,
                    'ei': str(entity_id),
                    'selfDeal': True,  # CRITICAL: Match Peekaboo UI behavior (same as places URL)
                }
                
                logger.info(f"Scraping deals for card {card_data['name']} with payload: {payload}")
                
                # Add retry logic for connection errors (ChunkedEncodingError, IncompleteRead, etc.)
                max_retries = 3
                retry_delay = 2
                response = None
                
                for attempt in range(max_retries):
                    try:
                        response = requests.post(api_url, json=payload, headers=self.headers, timeout=60)  # Increased timeout
                        break  # Success, exit retry loop
                    except (requests.exceptions.ChunkedEncodingError, 
                            requests.exceptions.ConnectionError,
                            requests.exceptions.Timeout,
                            requests.exceptions.ProtocolError,
                            ConnectionResetError) as e:
                        if attempt < max_retries - 1:
                            logger.warning(f"⚠️  Connection error for card {card_data['name']} (attempt {attempt + 1}/{max_retries}): {str(e)[:100]}. Retrying in {retry_delay}s...")
                            time.sleep(retry_delay)
                            retry_delay *= 2  # Exponential backoff
                        else:
                            logger.error(f"❌ Connection failed for card {card_data['name']} after {max_retries} attempts: {str(e)[:200]}")
                            raise
                
                if not response:
                    logger.error(f"❌ Failed to get response for card {card_data['name']} after {max_retries} attempts")
                    continue
                
                card_offers_count = 0
                
                if response.status_code == 200:
                    # Check if response is JSON
                    try:
                        data = response.json()
                        # v8/entity/deals returns deals directly, not entities
                        deals_list = data if isinstance(data, list) else data.get('deals', []) or data.get('entities', [])
                        logger.info(f"API returned {len(deals_list)} deals for card {card_data['name']}")
                        
                        for deal in deals_list:
                            if isinstance(deal, dict):
                                deal_id = deal.get('dealId') or deal.get('id')
                                # Source URL should be UNIQUE per deal. Using only the places URL would
                                # collapse all offers into a single row during update_or_create.
                                places_full_url = f"{places_url}?{'&'.join([f'{k}={v}' for k, v in places_params.items()])}"
                                source_url = places_full_url
                                if deal_id:
                                    source_url = f"{places_full_url}&dealId={deal_id}"

                                # Extract merchant info - Peekaboo API returns targetEntityName and targetEntityLogo
                                merchant_name = deal.get('targetEntityName', '') or deal.get('merchantName', '')
                                merchant_logo = deal.get('targetEntityLogo', '') or deal.get('merchantLogo', '')
                                
                                # Use merchant logo as deal image if no direct image field exists
                                # This matches Peekaboo UI where each deal shows the merchant's logo/image
                                deal_image = deal.get('image', '') or deal.get('dealImage', '') or merchant_logo
                                
                                # Extract category from deal or merchant info
                                # Try multiple fields: category, targetEntityCategory, categoryName, dealCategory
                                category = (
                                    deal.get('category', '') or 
                                    deal.get('targetEntityCategory', '') or 
                                    deal.get('categoryName', '') or 
                                    deal.get('dealCategory', '') or
                                    deal.get('categoryName', '') or
                                    ''
                                )
                                # If category is a dict, extract the name
                                if isinstance(category, dict):
                                    category = category.get('name', '') or category.get('categoryName', '') or ''
                                
                                # CRITICAL: Extract associations array - this tells us which cards this deal is available on
                                # The associations array contains cards like:
                                # [{"typeId": 640, "name": "Askari Classic Credit Card", ...}, ...]
                                associations = deal.get('associations', [])
                                if not isinstance(associations, list):
                                    associations = []
                                
                                # Extract card names and typeIds from associations for linking
                                available_on_card_names = []
                                available_on_card_type_ids = []
                                available_on_card_slugs = []
                                available_on_associations = []
                                
                                for assoc in associations:
                                    if isinstance(assoc, dict):
                                        card_name = assoc.get('name', '')
                                        type_id = assoc.get('typeId')
                                        source_entity_association_id = assoc.get('sourceEntityAssociationId')
                                        
                                        if card_name:
                                            available_on_card_names.append(card_name)
                                        if type_id:
                                            available_on_card_type_ids.append(type_id)
                                        
                                        # Try to extract slug from card name or use a generated one
                                        card_slug = assoc.get('slug', '')
                                        if not card_slug and card_name:
                                            # Generate slug from name (similar to how we do it elsewhere)
                                            card_slug = self._slugify(card_name)
                                        if card_slug:
                                            available_on_card_slugs.append(card_slug)
                                        
                                        # Store full association data for matching
                                        available_on_associations.append({
                                            'typeId': type_id,
                                            'name': card_name,
                                            'slug': card_slug,
                                            'sourceEntityAssociationId': source_entity_association_id,
                                        })
                                
                                offer_data = {
                                    'title': deal.get('title', ''),
                                    'description': deal.get('description', ''),
                                    'discount_percentage': deal.get('percentageValue') or deal.get('discount_percentage'),
                                    'discount_amount': deal.get('discountAmount') or deal.get('discount_amount'),
                                    'merchant_name': merchant_name,
                                    'merchant_logo': merchant_logo,
                                    'image': deal_image,  # Use merchant logo as image if deal image not available
                                    'category': category,
                                    'source_url': source_url,
                                    'terms_conditions': deal.get('terms', '') or deal.get('termsConditions', ''),
                                    'deal_id': deal_id,  # Store dealId for deduplication
                                    # CRITICAL: Store associations data for linking to multiple cards
                                    'available_on_card_names': available_on_card_names,
                                    'available_on_card_type_ids': available_on_card_type_ids,
                                    'available_on_card_slugs': available_on_card_slugs,
                                    'available_on_associations': available_on_associations,
                                    # Keep card_name for backward compatibility (but we'll link to all cards in associations)
                                    'card_name': card_data['name'],
                                    'card_slug': card_data['slug'],
                                }
                                bank_data['offers'].append(offer_data)
                                card_offers_count += 1
                        
                        # If we got deals, skip HTML fallback
                        if card_offers_count > 0:
                            logger.info(f"Scraped {card_offers_count} offers for card {card_data['name']}")
                            continue
                    except (ValueError, requests.exceptions.JSONDecodeError) as e:
                        logger.warning(f"API returned non-JSON response for card {card_data['name']}: {response.text[:200]}")
                        # Try to scrape from places URL directly
                        try:
                            places_full_url = f"{places_url}?{'&'.join([f'{k}={v}' for k, v in places_params.items()])}"
                            logger.info(f"Trying to scrape from places URL: {places_full_url}")
                            places_response = requests.get(places_full_url, headers=self.headers, timeout=30)
                            if places_response.status_code == 200:
                                # Try to parse JSON from script tags or API response
                                soup = BeautifulSoup(places_response.content, 'html.parser')
                                
                                # Look for JSON data in script tags
                                scripts = soup.find_all('script', type=re.compile(r'application/json', re.I))
                                for script in scripts:
                                    if script.string:
                                        try:
                                            json_data = json.loads(script.string)
                                            entities = json_data.get('entities', []) if isinstance(json_data, dict) else []
                                            for entity in entities:
                                                deals = entity.get('deals', [])
                                                for deal in deals:
                                                    offer_data = {
                                                        'title': deal.get('title', ''),
                                                        'description': deal.get('description', ''),
                                                        'discount_percentage': deal.get('percentageValue'),
                                                        'merchant_name': entity.get('name', ''),
                                                        'merchant_logo': entity.get('logo', ''),
                                                        'image': deal.get('image', ''),
                                                        'category': entity.get('category', ''),
                                                        'source_url': places_full_url,
                                                        'card_name': card_data['name'],
                                                        'card_slug': card_data['slug'],
                                                    }
                                                    bank_data['offers'].append(offer_data)
                                                    card_offers_count += 1
                                            break
                                        except (json.JSONDecodeError, KeyError):
                                            continue
                        except Exception as e2:
                            logger.debug(f"Failed to scrape from places URL: {str(e2)}")
                else:
                    logger.warning(f"API returned status {response.status_code} for card {card_data['name']}: {response.text[:200]}")
                
                logger.info(f"Scraped {card_offers_count} offers for card {card_data['name']}")
            except Exception as e:
                logger.error(f"Failed to scrape deals for card {card_data.get('name', 'Unknown')}: {str(e)}", exc_info=True)
                continue
        
        logger.info(f"Cards with IDs: {cards_with_ids}, Cards without IDs: {cards_without_ids}")
        
        logger.info(f"Total scraped {len(bank_data['offers'])} offers for {bank_data['name']}")
        
        # Fallback to HTML parsing
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Update bank information from HTML if not already set from API
            if not bank_data.get('name') or bank_data['name'] == slug.replace('-', ' ').title():
                title_elem = soup.find('h1') or soup.find('title')
                if title_elem:
                    bank_data['name'] = title_elem.get_text(strip=True)
            
            # Try to find logo (if not already set from API)
            if not bank_data.get('logo'):
                logo_elem = soup.find('img', class_=re.compile(r'logo|brand', re.I))
                if logo_elem:
                    bank_data['logo'] = logo_elem.get('src', '')
                    if bank_data['logo'] and not bank_data['logo'].startswith('http'):
                        bank_data['logo'] = urljoin(self.base_url, bank_data['logo'])
            
            # Try to find description (if not already set from API)
            if not bank_data.get('description'):
                desc_elem = soup.find('div', class_=re.compile(r'description|about|info', re.I))
                if desc_elem:
                    bank_data['description'] = desc_elem.get_text(strip=True)
            
            # Scrape membership cards from HTML (if not already found from API)
            if not bank_data.get('cards'):
                # Look for membership links: /membership/{entity_id}/{slug}/{association_id}/{card_slug}
                membership_links = soup.find_all('a', href=re.compile(r'/membership/\d+/'))
                for link in membership_links:
                    href = link.get('href', '')
                    # Extract: /membership/{entity_id}/{slug}/{association_id}/{card_slug}
                    match = re.search(r'/membership/(\d+)/([^/]+)/(\d+)/([^/\?]+)', href)
                    if match:
                        link_entity_id = int(match.group(1))
                        link_slug = match.group(2)
                        association_id = int(match.group(3))
                        card_slug = match.group(4)
                        
                        # Only process if it matches our bank
                        if link_entity_id == entity_id:
                            card_name = link.get_text(strip=True)
                            if not card_name:
                                card_name = card_slug.replace('-', ' ').title()
                            
                            # Visit membership page to get associationTypeId
                            membership_url = urljoin(self.base_url, href)
                            try:
                                membership_response = requests.get(membership_url, headers=self.headers, timeout=30)
                                if membership_response.status_code == 200:
                                    membership_soup = BeautifulSoup(membership_response.content, 'html.parser')
                                    
                                    # Try to find associationTypeId in script tags or data attributes
                                    association_type_id = None
                                    scripts = membership_soup.find_all('script')
                                    for script in scripts:
                                        if script.string:
                                            # Look for associationTypeId in JSON
                                            type_id_match = re.search(r'associationTypeId["\']?\s*[:=]\s*(\d+)', script.string)
                                            if type_id_match:
                                                association_type_id = int(type_id_match.group(1))
                                                break
                                    
                                    # If not found, try to extract from deals button/link
                                    if not association_type_id:
                                        deals_link = membership_soup.find('a', href=re.compile(r'/places/.*associationTypeId'))
                                        if deals_link:
                                            href_match = re.search(r'associationTypeId=(\d+)', deals_link.get('href', ''))
                                            if href_match:
                                                association_type_id = int(href_match.group(1))
                            except Exception as e:
                                logger.debug(f"Failed to get associationTypeId from membership page: {str(e)}")
                            
                            card_data = {
                                'name': card_name,
                                'slug': card_slug,
                                'description': '',
                                'image': '',
                                'card_type': self._detect_card_type(card_name),
                                'association_id': association_id,
                                'association_type_id': association_type_id,
                                'source_entity_id': source_entity_id,
                            }
                            
                            # Try to find card image
                            card_img = link.find('img') or link.find_parent().find('img')
                            if card_img:
                                card_data['image'] = card_img.get('src', '')
                                if card_data['image'] and not card_data['image'].startswith('http'):
                                    card_data['image'] = urljoin(self.base_url, card_data['image'])
                            
                            bank_data['cards'].append(card_data)
                
                # Also try to find cards in card sections
                if not bank_data.get('cards'):
                    card_sections = soup.find_all(['div', 'section'], class_=re.compile(r'card|membership', re.I))
                    for section in card_sections:
                        card_name_elem = section.find(['h2', 'h3', 'h4', 'span'], class_=re.compile(r'title|name', re.I))
                        if card_name_elem:
                            card_name = card_name_elem.get_text(strip=True)
                            if card_name and len(card_name) > 3:
                                card_data = {
                                    'name': card_name,
                                    'slug': self._slugify(card_name),
                                    'description': '',
                                    'image': '',
                                    'card_type': self._detect_card_type(card_name),
                                }
                                
                                # Try to find card image
                                card_img = section.find('img')
                                if card_img:
                                    card_data['image'] = card_img.get('src', '')
                                    if card_data['image'] and not card_data['image'].startswith('http'):
                                        card_data['image'] = urljoin(self.base_url, card_data['image'])
                                
                                # Try to find card description
                                card_desc = section.find(['p', 'div'], class_=re.compile(r'description|info', re.I))
                                if card_desc:
                                    card_data['description'] = card_desc.get_text(strip=True)
                                
                                bank_data['cards'].append(card_data)
                
                # Now scrape deals for cards found from HTML
                if bank_data.get('cards'):
                    for card_data in bank_data['cards']:
                        if card_data.get('association_id') and card_data.get('association_type_id'):
                            # Scrape deals using the same method as API cards
                            try:
                                api_url = f"{self.api_base}/api/v8/entities"
                                payload = {
                                    'sortType': 'trending',
                                    'targetEntities': '_all',
                                    'city': city_capitalized,
                                    'country': 'Pakistan',
                                    'lat': coords['lat'],
                                    'long': coords['long'],
                                    'language': 'en',
                                    'categoryId': '_all',
                                    'category': 'all',
                                    'limit': 100,
                                    'offset': 0,
                                    'sourceEntityId': str(card_data.get('source_entity_id', source_entity_id)),
                                    'associationTypeId': str(card_data['association_type_id']),
                                    'ai': str(card_data['association_id']),
                                    'card': card_data['slug'],
                                    'discounts': slug,
                                    'ei': str(entity_id),
                                }
                                
                                response = requests.post(api_url, json=payload, headers=self.headers, timeout=30)
                                if response.status_code == 200:
                                    data = response.json()
                                    entities = data if isinstance(data, list) else data.get('entities', [])
                                    
                                    for entity in entities:
                                        deals = entity.get('deals', [])
                                        for deal in deals:
                                            offer_data = {
                                                'title': deal.get('title', ''),
                                                'description': deal.get('description', ''),
                                                'discount_percentage': deal.get('percentageValue') or deal.get('discount_percentage'),
                                                'discount_amount': deal.get('discountAmount') or deal.get('discount_amount'),
                                                'merchant_name': entity.get('name', '') or deal.get('targetEntityName', ''),
                                                'merchant_logo': entity.get('logo', '') or deal.get('targetEntityLogo', ''),
                                                'image': deal.get('image', '') or entity.get('image', ''),
                                                'category': deal.get('category', '') or entity.get('category', ''),
                                                'source_url': f"{self.base_url}/{city}/places/_all/all?ai={card_data['association_id']}&associationTypeId={card_data['association_type_id']}&card={card_data['slug']}&discounts={slug}&ei={entity_id}&sourceEntityId={card_data.get('source_entity_id', source_entity_id)}",
                                                'terms_conditions': deal.get('terms', '') or deal.get('termsConditions', ''),
                                                'card_name': card_data['name'],
                                                'card_slug': card_data['slug'],
                                            }
                                            bank_data['offers'].append(offer_data)
                            except Exception as e:
                                logger.debug(f"Failed to scrape deals for HTML card {card_data.get('name', 'Unknown')}: {str(e)}")
                                continue
            
            # Scrape offers/deals - look for offer sections
            offer_sections = soup.find_all(['div', 'article'], class_=re.compile(r'offer|deal|discount|promo', re.I))
            for section in offer_sections:
                offer_title_elem = section.find(['h2', 'h3', 'h4', 'span'], class_=re.compile(r'title|name', re.I))
                if offer_title_elem:
                    offer_title = offer_title_elem.get_text(strip=True)
                    if offer_title and len(offer_title) > 3:
                        offer_data = {
                            'title': offer_title,
                            'description': '',
                            'discount_percentage': None,
                            'discount_amount': None,
                            'merchant_name': '',
                            'merchant_logo': '',
                            'image': '',
                            'category': '',
                            'terms_conditions': '',
                            'source_url': url,
                        }
                        
                        # Try to find discount percentage
                        discount_elem = section.find(text=re.compile(r'\d+%'))
                        if discount_elem:
                            match = re.search(r'(\d+)%', discount_elem)
                            if match:
                                offer_data['discount_percentage'] = float(match.group(1))
                        
                        # Try to find merchant name
                        merchant_elem = section.find(['span', 'div'], class_=re.compile(r'merchant|store|brand', re.I))
                        if merchant_elem:
                            offer_data['merchant_name'] = merchant_elem.get_text(strip=True)
                        
                        # Try to find offer image
                        offer_img = section.find('img')
                        if offer_img:
                            offer_data['image'] = offer_img.get('src', '')
                            if offer_data['image'] and not offer_data['image'].startswith('http'):
                                offer_data['image'] = urljoin(self.base_url, offer_data['image'])
                        
                        # Try to find description
                        offer_desc = section.find(['p', 'div'], class_=re.compile(r'description|details', re.I))
                        if offer_desc:
                            offer_data['description'] = offer_desc.get_text(strip=True)
                        
                        bank_data['offers'].append(offer_data)
            
            # Also try to scrape from places URL if available
            places_url = f"{self.base_url}/{city}/places/_all/all?ei={entity_id}&discounts={slug}"
            self._scrape_places_offers(places_url, bank_data)
            
            logger.info(f"Scraped {len(bank_data['cards'])} cards and {len(bank_data['offers'])} offers for {bank_data['name']}")
            return bank_data
            
        except Exception as e:
            logger.error(f"Error scraping bank detail {entity_id}: {str(e)}", exc_info=True)
            return None
    
    def _scrape_places_offers(self, url: str, bank_data: Dict) -> None:
        """Scrape offers from places URL - extract entity_id and use API"""
        try:
            # Extract entity_id from URL parameters
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            entity_id = params.get('ei', [None])[0] or params.get('sourceEntityId', [None])[0]
            
            if entity_id:
                # Use API to get deals for this entity
                try:
                    api_url = f"{self.api_base}/v5/entities"
                    api_params = {
                        'sourceEntityId': entity_id,
                        'city': parsed.path.split('/')[1].capitalize() if len(parsed.path.split('/')) > 1 else 'Karachi',
                        'country': 'Pakistan',
                        'language': 'en',
                        'limit': 100,
                        'offset': 0,
                    }
                    
                    response = requests.get(api_url, headers=self.headers, params=api_params, timeout=30)
                    if response.status_code == 200:
                        data = response.json()
                        if isinstance(data, list):
                            for entity in data:
                                for deal in entity.get('deals', []):
                                    offer_data = {
                                        'title': deal.get('title', ''),
                                        'description': deal.get('description', ''),
                                        'discount_percentage': deal.get('percentage_value'),
                                        'merchant_name': entity.get('name', ''),
                                        'merchant_logo': entity.get('logo', ''),
                                        'image': deal.get('image', ''),
                                        'category': deal.get('category', ''),
                                        'source_url': url,
                                    }
                                    bank_data['offers'].append(offer_data)
                        elif isinstance(data, dict) and 'entities' in data:
                            for entity in data.get('entities', []):
                                for deal in entity.get('deals', []):
                                    offer_data = {
                                        'title': deal.get('title', ''),
                                        'description': deal.get('description', ''),
                                        'discount_percentage': deal.get('percentage_value'),
                                        'merchant_name': entity.get('name', ''),
                                        'merchant_logo': entity.get('logo', ''),
                                        'image': deal.get('image', ''),
                                        'category': deal.get('category', ''),
                                        'source_url': url,
                                    }
                                    bank_data['offers'].append(offer_data)
                        return
                except Exception as e:
                    logger.debug(f"API method failed for places: {str(e)}")
            
            # Fallback to HTML parsing
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            # Try to parse JSON if it's an API response
            try:
                data = response.json()
                if isinstance(data, dict) and 'entities' in data:
                    for entity in data.get('entities', []):
                        for deal in entity.get('deals', []):
                            offer_data = {
                                'title': deal.get('title', ''),
                                'description': deal.get('description', ''),
                                'discount_percentage': deal.get('percentage_value'),
                                'merchant_name': entity.get('name', ''),
                                'merchant_logo': entity.get('logo', ''),
                                'image': deal.get('image', ''),
                                'category': deal.get('category', ''),
                                'source_url': url,
                            }
                            bank_data['offers'].append(offer_data)
            except (ValueError, KeyError):
                # If not JSON, try HTML parsing
                soup = BeautifulSoup(response.content, 'html.parser')
                # Add HTML parsing logic here if needed
                
        except Exception as e:
            logger.debug(f"Error scraping places offers from {url}: {str(e)}")
    
    def _slugify(self, text: str) -> str:
        """Convert text to URL-friendly slug"""
        text = text.lower()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[-\s]+', '-', text)
        return text.strip('-')
    
    def _detect_card_type(self, card_name: str) -> str:
        """Detect card type from card name"""
        name_lower = card_name.lower()
        if 'debit' in name_lower:
            return 'DEBIT'
        elif 'credit' in name_lower:
            return 'CREDIT'
        elif 'platinum' in name_lower:
            return 'PLATINUM'
        elif 'gold' in name_lower:
            return 'GOLD'
        elif 'premium' in name_lower:
            return 'PREMIUM'
        else:
            return 'CREDIT'  # Default
