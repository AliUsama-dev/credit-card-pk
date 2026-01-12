# scraping/scrapers/peekaboo_scraper.py
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path

import requests
from django.utils import timezone

logger = logging.getLogger(__name__)

# City coordinates for Peekaboo API
CITY_COORDINATES = {
    'KARACHI': {'lat': 24.8607, 'long': 67.0011},
    'LAHORE': {'lat': 31.5204, 'long': 74.3587},
    'ISLAMABAD': {'lat': 33.7294, 'long': 73.0931},
    'RAWALPINDI': {'lat': 33.5651, 'long': 73.0169},
    'FAISALABAD': {'lat': 31.4504, 'long': 73.1350},
    'MULTAN': {'lat': 30.1575, 'long': 71.5249},
    'HYDERABAD': {'lat': 25.3960, 'long': 68.3578},
    'PESHAWAR': {'lat': 34.0151, 'long': 71.5249},
    'QUETTA': {'lat': 30.1798, 'long': 66.9750},
    'GUJRANWALA': {'lat': 32.1617, 'long': 74.1883},
    'SIALKOT': {'lat': 32.4945, 'long': 74.5229},
    'BAHAWALPUR': {'lat': 29.4000, 'long': 71.6833},
    'SARGODHA': {'lat': 32.0836, 'long': 72.6711},
    'SUKKUR': {'lat': 27.7025, 'long': 68.8567},
    'LARKANA': {'lat': 27.5590, 'long': 68.2120},
}

# Bank Peekaboo IDs (from the URL pattern you provided)
BANK_PEEKABOO_IDS = {
    'MEZAN': 'klaoshcjanaij2ktnbjkmiasvtafoabxtenstn5',  # Meezan Bank
    'HBL': 'klaoshcjanaij2ktnbjkmiasvtafoabxtenstn5',  # May need different IDs
    'UBL': 'klaoshcjanaij2ktnbjkmiasvtafoabxtenstn5',
    'MCB': 'klaoshcjanaij2ktnbjkmiasvtafoabxtenstn5',
    'BAFL': 'klaoshcjanaij2ktnbjkmiasvtafoabxtenstn5',
    'SCB': 'klaoshcjanaij2ktnbjkmiasvtafoabxtenstn5',
    'ABL': 'klaoshcjanaij2ktnbjkmiasvtafoabxtenstn5',
}

class PeekabooGuruScraper:
    """Professional scraper for Pakistani bank offers via Peekaboo Guru API"""
    
    def __init__(self, use_async: bool = False):
        self.use_async = use_async
        self.api_base = 'https://peekaboo.guru'
        
        # Load bank config
        base_dir = Path(__file__).parent.parent.parent
        urls_file = base_dir / 'scraping' / 'data' / 'verified_bank_urls.json'
        
        try:
            with open(urls_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except Exception as e:
            logger.warning(f"Could not load bank config: {e}")
            self.config = {'banks': []}
        
        # Default headers matching browser request
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Content-Type': 'application/json',
            'Origin': 'https://peekaboo.guru',
            'Referer': 'https://peekaboo.guru/',
            'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpZCI6NzIsInJvbGUiOiJndWVzdCIsImlhdCI6MTU1MzcwMDgwNiwianRpIjoiUEpJMXFTb2ktQzRBZFJWcm9nb3RNV2UzV3VXcFdXTm0ifQ.2mb26xL4Qt7FfBQZ-XQvp-fhecMpaVUVXWp_GEST_6U',
            'medium': 'WEB',
            'version': '2.1.0.2',
            'sec-ch-ua': '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
        }
    
    def _map_city_to_peekaboo(self, city_code: str) -> Dict[str, Any]:
        """Map city code to Peekaboo city name and coordinates"""
        city_upper = city_code.upper().replace(' ', '_')
        
        city_names = {
            'KARACHI': 'Karachi',
            'LAHORE': 'Lahore',
            'ISLAMABAD': 'Islamabad',
            'RAWALPINDI': 'Rawalpindi',
            'FAISALABAD': 'Faisalabad',
            'MULTAN': 'Multan',
            'HYDERABAD': 'Hyderabad',
            'PESHAWAR': 'Peshawar',
            'QUETTA': 'Quetta',
            'GUJRANWALA': 'Gujranwala',
            'SIALKOT': 'Sialkot',
            'BAHAWALPUR': 'Bahawalpur',
            'SARGODHA': 'Sargodha',
            'SUKKUR': 'Sukkur',
            'LARKANA': 'Larkana',
        }
        
        city_name = city_names.get(city_upper, city_code)
        coords = CITY_COORDINATES.get(city_upper, {'lat': 30.3753, 'long': 69.3451})  # Default: Pakistan center
        
        return {
            'name': city_name,
            'code': city_upper,
            **coords
        }
    
    def _get_bank_peekaboo_id(self, bank_code: str) -> str:
        """Get Peekaboo ID for a bank"""
        return BANK_PEEKABOO_IDS.get(bank_code.upper(), BANK_PEEKABOO_IDS.get('MEZAN', ''))
    
    def _get_bank_config(self, bank_code: str) -> Optional[Dict]:
        """Get bank configuration"""
        for bank in self.config.get('banks', []):
            if bank.get('code') == bank_code.upper():
                return bank
        return None
    
    def scrape_bank_offers_sync(self, bank_code: str, filters: Dict[str, Any] = None) -> List[Dict]:
        """Scrape bank offers synchronously using Peekaboo API"""
        filters = filters or {}
        bank_config = self._get_bank_config(bank_code)
        
        if not bank_config:
            logger.warning(f"Bank {bank_code} not found in config, using defaults")
            bank_config = {'code': bank_code, 'name': bank_code}
        
        # Get city info
        city_info = self._map_city_to_peekaboo(filters.get('city', 'KARACHI'))
        
        logger.info(f"Scraping {bank_config.get('name', bank_code)} for city {city_info['name']} with filters: {filters}")
        
        offers = []
        
        try:
            # Step 1: Get entities/deals from v5 API
            v5_offers = self._fetch_v5_entities(city_info, filters)
            offers.extend(v5_offers)
            
            # Step 2: Get deals from v8 API
            v8_offers = self._fetch_v8_deals(city_info, filters)
            offers.extend(v8_offers)
            
            # Step 3: Get widget data from v6 API (if needed)
            # v6_offers = self._fetch_v6_widget(city_info, filters)
            # offers.extend(v6_offers)
            
            # Add bank info to each offer
            for offer in offers:
                offer['bank_code'] = bank_code.upper()
                offer['bank_name'] = bank_config.get('name', bank_code)
            
            # Deduplicate by title + merchant
            seen = set()
            unique_offers = []
            for offer in offers:
                key = (offer.get('title', ''), offer.get('merchant', ''))
                if key not in seen and key[0]:
                    seen.add(key)
                    unique_offers.append(offer)
            
            logger.info(f"Found {len(unique_offers)} unique offers for {bank_code}")
            return unique_offers
                    
        except Exception as e:
            logger.error(f"Error scraping {bank_code}: {str(e)}", exc_info=True)
            return []
    
    def _fetch_v5_entities(self, city_info: Dict, filters: Dict) -> List[Dict]:
        """Fetch offers from v5 entity API"""
        offers = []
        
        try:
            url = f"{self.api_base}/api/v5/entity/_all/branch/_all/sourceEntities/_all"
            
            params = {
                'city': city_info['name'],
                'country': 'Pakistan',
                'entity': filters.get('entity', 'All'),
                'language': 'en',
                'lat': city_info['lat'],
                'long': city_info['long'],
                'limit': filters.get('limit', 100),
                'offset': filters.get('offset', 0),
            }
            
            # Add merchant type filter if provided
            if filters.get('merchant_type'):
                # Map merchant type to entity/category
                params['entity'] = self._map_merchant_type_to_entity(filters['merchant_type'])
            
            response = requests.get(url, params=params, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ REAL DATA from Peekaboo API v5: Received {len(data) if isinstance(data, list) else 'dict'} items")
                offers = self._parse_v5_response(data, city_info, filters)
                logger.info(f"✅ Parsed {len(offers)} REAL offers from Peekaboo API v5")
                if offers:
                    logger.info(f"✅ Sample REAL offer: {offers[0].get('title', 'N/A')[:50]}...")
            else:
                logger.warning(f"❌ API returned status {response.status_code}: {response.text[:200]}")
                
        except Exception as e:
            logger.error(f"Error fetching v5 entities: {str(e)}")
        
        return offers
    
    def _fetch_v8_deals(self, city_info: Dict, filters: Dict) -> List[Dict]:
        """Fetch deals from v8 deals API"""
        offers = []
        
        try:
            url = f"{self.api_base}/api/v8/entity/deals"
            
            payload = {
                'city': city_info['name'],
                'country': 'Pakistan',
                'entity': filters.get('entity', 'All'),
                'language': 'en',
                'lat': city_info['lat'],
                'long': city_info['long'],
                'limit': filters.get('limit', 100),
                'offset': filters.get('offset', 0),
            }
            
            # Add filters
            if filters.get('merchant_type'):
                payload['category'] = self._map_merchant_type_to_category(filters['merchant_type'])
            
            if filters.get('search'):
                payload['search'] = filters['search']
            
            response = requests.post(url, json=payload, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ REAL DATA from Peekaboo API v8: Received {len(data) if isinstance(data, list) else 'dict'} items")
                offers = self._parse_v8_response(data, city_info, filters)
                logger.info(f"✅ Parsed {len(offers)} REAL offers from Peekaboo API v8")
                if offers:
                    logger.info(f"✅ Sample REAL offer: {offers[0].get('title', 'N/A')[:50]}...")
            else:
                logger.warning(f"❌ API returned status {response.status_code}: {response.text[:200]}")
            
        except Exception as e:
            logger.error(f"Error fetching v8 deals: {str(e)}")
        
        return offers
    
    def _parse_v5_response(self, data: Dict, city_info: Dict, filters: Dict) -> List[Dict]:
        """Parse v5 API response"""
        offers = []
        
        # Response structure may vary - adapt based on actual response
        entities = []
        
        if isinstance(data, list):
            entities = data
        elif isinstance(data, dict):
            entities = data.get('entities', []) or data.get('data', []) or data.get('results', [])
        
        for item in entities:
            try:
                if not isinstance(item, dict):
                    continue
                offer = self._parse_entity_item(item, city_info, filters)
                if offer:
                    offers.append(offer)
            except Exception as e:
                logger.error(f"Error parsing v5 item: {str(e)}")
                continue
                
        return offers
    
    def _parse_v8_response(self, data: Dict, city_info: Dict, filters: Dict) -> List[Dict]:
        """Parse v8 deals API response"""
        offers = []
        
        deals = []
        
        if isinstance(data, list):
            deals = data
        elif isinstance(data, dict):
            deals = data.get('deals', []) or data.get('data', []) or data.get('results', []) or data.get('items', [])
        
        for item in deals:
            try:
                if not isinstance(item, dict):
                    continue
                offer = self._parse_deal_item(item, city_info, filters)
                if offer:
                    offers.append(offer)
            except Exception as e:
                logger.error(f"Error parsing v8 item: {str(e)}")
                continue
        
        return offers
    
    def _parse_entity_item(self, item: Dict, city_info: Dict, filters: Dict) -> Optional[Dict]:
        """Parse a single entity item from v5 API"""
        try:
            title = item.get('name') or item.get('title') or item.get('entityName', '').strip()
            if not title:
                return None
            
            description = item.get('description') or item.get('details', '').strip()
            merchant_name = item.get('merchantName') or item.get('merchant', '') or title
            
            # Extract discount
            discount_text = item.get('discount') or item.get('discountText') or item.get('offer', '')
            discount_percentage = self._extract_discount_percentage(discount_text)
            
            # Extract validity
            valid_from, valid_to = self._extract_validity_from_item(item)
            
            # Extract category
            category = item.get('category') or item.get('entityType', 'OTHER')
            
            # Build offer
            return {
                'title': title[:255],
                'description': description[:500] or f"Offer at {merchant_name}",
                'merchant': merchant_name[:100],
                'discount_percentage': discount_percentage,
                'valid_from': valid_from,
                'valid_to': valid_to,
                'category': self._map_category_to_merchant_type(category),
                'offer_type': 'DISCOUNT',
                'city': city_info['code'],
                'source_url': item.get('url') or item.get('link', ''),
                'image_url': item.get('image') or item.get('logo', ''),
                'terms_conditions': item.get('terms', '')[:1000],
                'scraped_at': timezone.now(),
                'is_active': True,
            }
        except Exception as e:
            logger.error(f"Error parsing entity item: {str(e)}")
            return None
    
    def _parse_deal_item(self, item: Dict, city_info: Dict, filters: Dict) -> Optional[Dict]:
        """Parse a single deal item from v8 API"""
        try:
            title = item.get('title') or item.get('name') or item.get('dealTitle') or item.get('deal_name', '').strip()
            if not title:
                return None
            
            description = item.get('description') or item.get('details') or item.get('dealDescription', '').strip()
            merchant_name = item.get('merchantName') or item.get('merchant') or item.get('partner') or item.get('merchant_name', '') or title
            
            # Extract discount from multiple possible fields
            discount_text = (
                item.get('discount') or 
                item.get('discountText') or 
                item.get('offerText') or 
                item.get('discount_percentage') or
                item.get('discountValue') or
                item.get('offer') or
                description
            )
            discount_percentage = self._extract_discount_percentage(discount_text)
            
            # Also check if discount is directly in the item
            if discount_percentage is None and item.get('discountPercentage'):
                try:
                    discount_percentage = float(item.get('discountPercentage'))
                except:
                    pass
            
            # Extract validity
            valid_from, valid_to = self._extract_validity_from_item(item)
            
            # Extract category
            category = item.get('category') or item.get('dealCategory') or item.get('categoryName', 'OTHER')
            
            # Build offer
            return {
                'title': title[:255],
                'description': description[:500] or f"Deal at {merchant_name}",
                'merchant': merchant_name[:100],
                'discount_percentage': discount_percentage,
                'valid_from': valid_from,
                'valid_to': valid_to,
                'category': self._map_category_to_merchant_type(category),
                'offer_type': self._determine_offer_type(discount_text or description),
                'city': city_info['code'],
                'source_url': item.get('url') or item.get('dealUrl') or item.get('link', ''),
                'image_url': item.get('image') or item.get('dealImage') or item.get('imageUrl', ''),
                'terms_conditions': (item.get('terms') or item.get('termsConditions') or '')[:1000],
                'scraped_at': timezone.now(),
                'is_active': True,
            }
        except Exception as e:
            logger.error(f"Error parsing deal item: {str(e)}")
            return None
    
    def _extract_discount_percentage(self, text: str) -> Optional[float]:
        """Extract discount percentage from text"""
        if not text:
            return None
        
        # Try patterns
        patterns = [
            r'(\d{1,3})\s*%',
            r'(\d{1,3})%\s*(?:off|discount|save)',
            r'save\s*(\d{1,3})%',
            r'upto\s*(\d{1,3})%',
            r'up to\s*(\d{1,3})%',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, str(text), re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except:
                    continue
        
        return None
    
    def _extract_validity_from_item(self, item: Dict) -> tuple:
        """Extract validity dates from item"""
        today = timezone.now().date()
        
        valid_from = item.get('validFrom') or item.get('startDate')
        valid_to = item.get('validTo') or item.get('endDate') or item.get('expiryDate')
        
        try:
            if valid_from:
                if isinstance(valid_from, str):
                    valid_from = datetime.fromisoformat(valid_from.replace('Z', '+00:00')).date()
                else:
                    valid_from = today
            else:
                valid_from = today
        except:
            valid_from = today
        
        try:
            if valid_to:
                if isinstance(valid_to, str):
                    valid_to = datetime.fromisoformat(valid_to.replace('Z', '+00:00')).date()
                else:
                    valid_to = today + timedelta(days=60)
            else:
                valid_to = today + timedelta(days=60)
        except:
            valid_to = today + timedelta(days=60)
        
        return valid_from, valid_to
    
    def _determine_offer_type(self, discount_text: str) -> str:
        """Determine offer type from discount text"""
        if not discount_text:
            return 'DISCOUNT'
        
        text_lower = str(discount_text).lower()
        
        if any(word in text_lower for word in ['cashback', 'cash back']):
            return 'CASHBACK'
        elif any(word in text_lower for word in ['emi', 'installment']):
            return 'EMI'
        elif any(word in text_lower for word in ['bonus', 'welcome']):
            return 'WELCOME_BONUS'
        else:
            return 'DISCOUNT'
    
    def _map_category_to_merchant_type(self, category: str) -> str:
        """Map category to merchant type"""
        if not category:
            return 'OTHER'
        
        mapping = {
            'dining': 'RESTAURANT',
            'restaurant': 'RESTAURANT',
            'food': 'RESTAURANT',
            'cafe': 'RESTAURANT',
            'shopping': 'RETAIL',
            'retail': 'RETAIL',
            'ecommerce': 'E_COMMERCE',
            'travel': 'TRAVEL',
            'hotel': 'HOTEL',
            'fuel': 'FUEL_STATION',
            'groceries': 'SUPERMARKET',
            'supermarket': 'SUPERMARKET',
            'entertainment': 'ENTERTAINMENT',
            'health': 'HEALTHCARE',
            'beauty': 'BEAUTY',
            'electronics': 'ELECTRONICS',
            'fashion': 'FASHION',
            'education': 'EDUCATION',
            'automotive': 'AUTOMOTIVE',
        }
        
        return mapping.get(str(category).lower(), 'OTHER')
    
    def _map_merchant_type_to_entity(self, merchant_type: str) -> str:
        """Map merchant type to Peekaboo entity"""
        mapping = {
            'RESTAURANT': 'Dining',
            'HOTEL': 'Travel',
            'RETAIL': 'Shopping',
            'E_COMMERCE': 'Shopping',
            'TRAVEL': 'Travel',
            'FUEL_STATION': 'Fuel',
            'SUPERMARKET': 'Groceries',
            'ENTERTAINMENT': 'Entertainment',
        }
        return mapping.get(merchant_type, 'All')
    
    def _map_merchant_type_to_category(self, merchant_type: str) -> str:
        """Map merchant type to Peekaboo category"""
        mapping = {
            'RESTAURANT': 'dining',
            'HOTEL': 'travel',
            'RETAIL': 'shopping',
            'E_COMMERCE': 'shopping',
            'TRAVEL': 'travel',
            'FUEL_STATION': 'fuel',
            'SUPERMARKET': 'groceries',
            'ENTERTAINMENT': 'entertainment',
        }
        return mapping.get(merchant_type, 'all')
    
    def scrape_all_banks_sync(self, filters: Dict[str, Any] = None) -> Dict[str, List[Dict]]:
        """Scrape all banks synchronously"""
        filters = filters or {}
        results = {}
        
        for bank in self.config.get('banks', []):
            bank_code = bank.get('code', '').upper()
            if not bank_code:
                continue
            
            try:
                offers = self.scrape_bank_offers_sync(bank_code, filters)
                results[bank_code] = offers
                logger.info(f"Scraped {len(offers)} offers from {bank_code}")
            except Exception as e:
                logger.error(f"Error scraping {bank_code}: {str(e)}")
                results[bank_code] = []
        
        return results


# Sync wrapper for Celery
def scrape_peekaboo_banks_sync(filters: Dict[str, Any] = None) -> Dict[str, List[Dict]]:
    """Synchronous wrapper for Peekaboo scraper"""
    scraper = PeekabooGuruScraper(use_async=False)
    return scraper.scrape_all_banks_sync(filters)
