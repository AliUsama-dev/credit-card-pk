# scraping/scrapers/bank_specific_scraper.py
# Scraper for bank-specific Peekaboo SDK endpoints (secure-sdk.peekaboo.guru)

import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

import requests
from django.utils import timezone
from cards.models import Bank

logger = logging.getLogger(__name__)

# Bank-specific SDK endpoint IDs (from secure-sdk.peekaboo.guru)
# Each bank has unique endpoint paths
BANK_SDK_ENDPOINTS = {
    'MEEZAN': {
        'cities': 'klaoshcjanaij2ktnbjkmiasvtafoabxtenstn5',
        'entities': 'uljin2s3nitoi89njkhklgkj5',
        'categories': 'kcjaastndoeauisgjod78oqnkkasrd7asAsky5',
        'card_associations': 'saovrumensjlqdsaiocassasdasociasdasdtns',
        'base_url': 'https://meezan-web.peekaboo.guru',
    },
    'HBL': {
        # HBL endpoints - will need to be discovered from https://www.hbl.com/personal/cards/hbl-deals-and-discounts
        # For now using same as Meezan (will need to update when HBL endpoints are found)
        'cities': 'klaoshcjanaij2ktnbjkmiasvtafoabxtenstn5',
        'entities': 'uljin2s3nitoi89njkhklgkj5',
        'categories': 'kcjaastndoeauisgjod78oqnkkasrd7asAsky5',
        'card_associations': 'saovrumensjlqdsaiocassasdasociasdasdtns',
        'base_url': 'https://hbl-web.peekaboo.guru',
    },
}

class BankSpecificScraper:
    """Scraper for bank-specific Peekaboo SDK endpoints"""
    
    def __init__(self):
        self.sdk_base = 'https://secure-sdk.peekaboo.guru'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Content-Type': 'application/json',
            'Origin': None,  # Will be set per bank
            'Referer': None,  # Will be set per bank
            'medium': 'IFRAME',
            'version': '1.0.0',
            'ownerkey': 'af085488ba0578c025f03fc7fae7b25d',
            'priority': 'u=1, i',
            'sec-ch-ua': '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
        }
    
    def _get_bank_config(self, bank_code: str) -> Optional[Dict]:
        """Get bank SDK configuration"""
        bank_code_upper = bank_code.upper()
        if bank_code_upper == 'MEZAN':
            bank_code_upper = 'MEEZAN'
        return BANK_SDK_ENDPOINTS.get(bank_code_upper)
    
    def _get_bank_from_code(self, bank_code: str) -> Optional[Bank]:
        """Get Bank model from code"""
        try:
            if bank_code.upper() == 'MEZAN':
                return Bank.objects.filter(code='MEEZAN').first()
            return Bank.objects.filter(code=bank_code.upper()).first()
        except Exception as e:
            logger.error(f"Error getting bank: {e}")
            return None
    
    def scrape_cities(self, bank_code: str) -> List[Dict]:
        """Scrape cities for a bank"""
        config = self._get_bank_config(bank_code)
        if not config:
            logger.error(f"No config found for bank: {bank_code}")
            return []
        
        endpoint = config['cities']
        url = f"{self.sdk_base}/{endpoint}"
        
        # Set origin/referer based on bank
        headers = self.headers.copy()
        headers['Origin'] = config['base_url']
        headers['Referer'] = f"{config['base_url']}/"
        
        try:
            # Try empty payload first (as per user's example)
            payload = {}
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            # If 422 error, try with required parameters
            if response.status_code == 422:
                logger.warning(f"Got 422 for cities, trying with parameters...")
                payload = {
                    'country': 'Pakistan',
                }
                response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                cities = data if isinstance(data, list) else []
                logger.info(f"✅ Scraped {len(cities)} cities for {bank_code}")
                return cities
            else:
                logger.error(f"❌ Failed to fetch cities: {response.status_code} - {response.text[:200]}")
                return []
        except Exception as e:
            logger.error(f"Error scraping cities: {str(e)}")
            return []
    
    def scrape_categories(self, bank_code: str, city: str = 'Karachi') -> List[Dict]:
        """
        Scrape categories for a bank.
        NOTE: This endpoint may not be available for all banks.
        Returns empty list if endpoint is not accessible.
        """
        config = self._get_bank_config(bank_code)
        if not config:
            return []
        
        endpoint = config['categories']
        url = f"{self.sdk_base}/{endpoint}"
        
        headers = self.headers.copy()
        headers['Origin'] = config['base_url']
        headers['Referer'] = f"{config['base_url']}/"
        
        try:
            # Try empty payload first
            payload = {}
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            # If 418 or 422 error, the endpoint likely doesn't support this operation
            if response.status_code in [418, 422]:
                logger.warning(f"⚠️  Categories endpoint not available for {bank_code} (status: {response.status_code})")
                logger.info(f"Response: {response.text[:200]}")
                logger.info(f"💡 Categories may be embedded in entities data or not available via this endpoint")
                return []  # Gracefully return empty list
            
            if response.status_code == 200:
                data = response.json()
                categories = data if isinstance(data, list) else []
                logger.info(f"✅ Scraped {len(categories)} categories for {bank_code}")
                return categories
            else:
                logger.warning(f"⚠️  Categories endpoint returned {response.status_code}: {response.text[:200]}")
                return []
        except Exception as e:
            logger.error(f"Error scraping categories: {str(e)}")
            return []
    
    def scrape_entities(self, bank_code: str, city_id: Optional[int] = None, city_slug: Optional[str] = None, city_name: Optional[str] = None) -> List[Dict]:
        """Scrape entities/merchants for a bank and city"""
        config = self._get_bank_config(bank_code)
        if not config:
            return []
        
        endpoint = config['entities']
        url = f"{self.sdk_base}/{endpoint}"
        
        headers = self.headers.copy()
        headers['Origin'] = config['base_url']
        headers['Referer'] = f"{config['base_url']}/"
        
        # Payload for entities endpoint (based on user's example)
        # When city is selected (e.g., Lahore), payload should include city slug
        # API might require limit and offset as well
        payload = {}
        
        if city_slug:
            # Use city slug format as shown in user's example
            payload = {
                'city': city_slug,
                'country': 'Pakistan',
                'limit': 100,
                'offset': 0,
            }
        elif city_name:
            # Use city name if slug not available
            payload = {
                'city': city_name,
                'country': 'Pakistan',
                'limit': 100,
                'offset': 0,
            }
        elif city_id:
            # Fallback to city ID if slug/name not available
            payload = {
                'cityId': city_id,
                'country': 'Pakistan',
                'limit': 100,
                'offset': 0,
            }
        else:
            # Default to Karachi if no city provided
            payload = {
                'city': 'Karachi',
                'country': 'Pakistan',
                'limit': 100,
                'offset': 0,
            }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            
            # If 422 error, try with city name (not slug)
            if response.status_code == 422:
                logger.warning(f"Got 422 for entities, trying with city name instead of slug...")
                logger.info(f"Response text: {response.text[:500]}")
                
                # Get city name from database if we have slug
                city_name_to_use = None
                if city_slug:
                    try:
                        from offers.models_bank_specific import BankSpecificCity
                        bank_obj = self._get_bank_from_code(bank_code)
                        if bank_obj:
                            city_obj = BankSpecificCity.objects.filter(bank=bank_obj, slug=city_slug).first()
                            if city_obj:
                                city_name_to_use = city_obj.name
                                logger.info(f"Found city name '{city_name_to_use}' for slug '{city_slug}'")
                    except Exception as e:
                        logger.debug(f"Could not get city name: {e}")
                
                # Try with city name (not slug) and additional required params
                if city_name_to_use:
                    # Try with limit and offset
                    payloads_to_try = [
                        {'city': city_name_to_use, 'country': 'Pakistan', 'limit': 100, 'offset': 0},
                        {'city': city_name_to_use.lower(), 'country': 'Pakistan', 'limit': 100, 'offset': 0},
                        {'city': city_name_to_use, 'country': 'Pakistan'},
                        {'city': city_name_to_use.lower(), 'country': 'Pakistan'},
                    ]
                    
                    for idx, payload in enumerate(payloads_to_try):
                        logger.info(f"Trying entities payload #{idx+1}: {payload}")
                        response = requests.post(url, json=payload, headers=headers, timeout=60)
                        logger.info(f"Response status: {response.status_code}, text: {response.text[:200]}")
                        if response.status_code == 200:
                            logger.info(f"✅ Success with payload: {payload}")
                            break
                elif city_name:
                    # Use provided city name
                    payloads_to_try = [
                        {'city': city_name, 'country': 'Pakistan', 'limit': 100, 'offset': 0},
                        {'city': city_name.lower(), 'country': 'Pakistan', 'limit': 100, 'offset': 0},
                        {'city': city_name, 'country': 'Pakistan'},
                    ]
                    
                    for idx, payload in enumerate(payloads_to_try):
                        logger.info(f"Trying entities payload #{idx+1}: {payload}")
                        response = requests.post(url, json=payload, headers=headers, timeout=60)
                        logger.info(f"Response status: {response.status_code}, text: {response.text[:200]}")
                        if response.status_code == 200:
                            logger.info(f"✅ Success with payload: {payload}")
                            break
                else:
                    # Default to Karachi with limit/offset
                    payloads_to_try = [
                        {'city': 'Karachi', 'country': 'Pakistan', 'limit': 100, 'offset': 0},
                        {'city': 'karachi', 'country': 'Pakistan', 'limit': 100, 'offset': 0},
                        {'city': 'Karachi', 'country': 'Pakistan'},
                    ]
                    
                    for idx, payload in enumerate(payloads_to_try):
                        logger.info(f"Trying entities payload #{idx+1}: {payload}")
                        response = requests.post(url, json=payload, headers=headers, timeout=60)
                        logger.info(f"Response status: {response.status_code}, text: {response.text[:200]}")
                        if response.status_code == 200:
                            logger.info(f"✅ Success with payload: {payload}")
                            break
            
            if response.status_code == 200:
                data = response.json()
                entities = data if isinstance(data, list) else []
                logger.info(f"✅ Scraped {len(entities)} entities for {bank_code} (city: {city_slug or city_name or city_id or 'Karachi'})")
                return entities
            else:
                logger.error(f"❌ Failed to fetch entities: {response.status_code} - {response.text[:200]}")
                return []
        except Exception as e:
            logger.error(f"Error scraping entities: {str(e)}")
            return []
    
    def scrape_card_associations(self, bank_code: str, city: str = 'karachi') -> List[Dict]:
        """
        Scrape card associations for a bank.
        NOTE: This endpoint may not be available for all banks.
        Returns empty list if endpoint is not accessible.
        Card associations may be embedded in deal/entity data instead.
        """
        config = self._get_bank_config(bank_code)
        if not config:
            return []
        
        endpoint = config['card_associations']
        url = f"{self.sdk_base}/{endpoint}"
        
        headers = self.headers.copy()
        headers['Origin'] = config['base_url']
        headers['Referer'] = f"{config['base_url']}/"
        
        try:
            # Try empty payload first
            payload = {}
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            # If 418 or 422 error, the endpoint likely doesn't support this operation
            if response.status_code in [418, 422]:
                logger.warning(f"⚠️  Card associations endpoint not available for {bank_code} (status: {response.status_code})")
                logger.info(f"Response: {response.text[:200]}")
                logger.info(f"💡 Card associations may be embedded in deals/entities data instead")
                return []  # Gracefully return empty list
            
            if response.status_code == 200:
                data = response.json()
                associations = data if isinstance(data, list) else []
                logger.info(f"✅ Scraped {len(associations)} card associations for {bank_code}")
                return associations
            else:
                logger.warning(f"⚠️  Card associations endpoint returned {response.status_code}: {response.text[:200]}")
                return []
        except Exception as e:
            logger.error(f"Error scraping card associations: {str(e)}")
            return []

