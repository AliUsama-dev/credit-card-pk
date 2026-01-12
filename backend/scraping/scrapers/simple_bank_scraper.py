# scraping/scrapers/simple_bank_scraper.py
import json
import re
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from django.utils import timezone

logger = logging.getLogger(__name__)

class SimpleBankScraper:
    """Simple HTTP-based scraper for Pakistani bank offers"""
    
    def __init__(self, context: Optional[Dict] = None):
        self.context = context or {}
        
        # Load verified URLs
        base_dir = Path(__file__).parent.parent.parent
        urls_file = base_dir / 'data' / 'verified_bank_urls.json'
        
        try:
            with open(urls_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.banks = {bank['code']: bank for bank in data['banks']}
        except Exception as e:
            logger.error(f"Failed to load bank URLs: {str(e)}")
            self.banks = {}
        
        # Setup session with SSL verification disabled for now
        # (Some Pakistani bank websites have SSL issues)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })
        
        # Suppress SSL warnings
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        self.session.verify = False  # Disable SSL verification for now
    
    def _get_city_mapping(self, city_code: str) -> str:
        """Get city name from code"""
        city_mapping = {
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
            'ALL_PAKISTAN': 'All Pakistan'
        }
        
        city_code = city_code.upper().replace(' ', '_')
        return city_mapping.get(city_code, 'Karachi')
    
    def scrape_bank_with_filters(self, bank_code: str, filters: Dict[str, Any]) -> List[Dict]:
        """Scrape bank offers with filters"""
        if not self.banks:
            logger.error("No banks loaded from configuration")
            return []
            
        city_code = filters.get('city', 'ALL_PAKISTAN')
        merchant_type = filters.get('merchant_type')
        search_term = filters.get('search', '')
        
        # Get city info
        city_name = self._get_city_mapping(city_code)
        
        if bank_code not in self.banks:
            logger.error(f"Bank {bank_code} not found in configuration")
            return []
        
        bank = self.banks[bank_code]
        all_offers = []
        
        logger.info(f"Scraping {bank['name']} with filters: city={city_name}")
        
        for url in bank['offer_urls']:
            try:
                offers = self._scrape_url(url, bank, city_name)
                if offers:
                    all_offers.extend(offers)
                    logger.info(f"Found {len(offers)} offers from {url}")
                    
            except Exception as e:
                logger.error(f"Error scraping {url}: {str(e)}")
                continue
        
        # Apply additional filters
        filtered_offers = []
        for offer in all_offers:
            # Filter by merchant type if specified
            if merchant_type and merchant_type != 'ALL':
                if not self._matches_merchant_type(offer, merchant_type):
                    continue
            
            # Filter by search term if specified
            if search_term:
                search_lower = search_term.lower()
                if not (search_lower in offer.get('title', '').lower() or 
                       search_lower in offer.get('description', '').lower() or
                       search_lower in offer.get('merchant', '').lower()):
                    continue
            
            filtered_offers.append(offer)
        
        return filtered_offers
    
    def _scrape_url(self, url: str, bank: Dict, city_name: str) -> List[Dict]:
        """Scrape a single URL"""
        try:
            logger.info(f"Fetching URL: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for offers
            offers = []
            
            # Try multiple selectors
            selectors = [
                '.offer-card', '.deal-card', '.discount-card', '.card',
                '.offer', '.deal', '.discount', '.promotion',
                '[class*="offer"]', '[class*="deal"]', '[class*="discount"]',
                'article', 'section', '.item', '.product'
            ]
            
            for selector in selectors:
                elements = soup.select(selector)
                for element in elements:
                    try:
                        offer = self._extract_offer(element, bank, city_name, url)
                        if offer:
                            offers.append(offer)
                    except Exception as e:
                        logger.debug(f"Error extracting from element: {str(e)}")
                        continue
            
            # If no structured offers found, look for text patterns
            if not offers:
                offers = self._extract_from_text(soup, bank, city_name, url)
            
            logger.info(f"Found {len(offers)} offers from {url}")
            return offers
            
        except Exception as e:
            logger.error(f"Error scraping URL {url}: {str(e)}")
            return []
    
    def _extract_offer(self, element, bank: Dict, city_name: str, base_url: str) -> Optional[Dict]:
        """Extract offer from HTML element"""
        try:
            text = element.get_text(' ', strip=True)
            if len(text) < 20:
                return None
            
            # Extract title
            title = ''
            title_elements = element.find_all(['h3', 'h4', 'h5', 'strong', 'b', '.title', '[class*="title"]'])
            if title_elements:
                title = title_elements[0].get_text(strip=True)
            
            if not title:
                lines = text.split('.')
                if lines:
                    title = lines[0].strip()[:200]
            
            if not title:
                return None
            
            # Extract merchant
            merchant = self._extract_merchant(text, title)
            
            # Extract discount
            discount = self._extract_discount(text)
            
            # Determine offer type
            offer_type = self._determine_offer_type(text)
            
            # Determine category
            category = self._categorize_offer(text)
            
            # Get link
            link = ''
            a_tag = element.find('a', href=True)
            if a_tag:
                href = a_tag['href']
                link = urljoin(base_url, href) if href.startswith('/') else href
            
            offer = {
                'title': title[:200],
                'description': text[:500],
                'bank_code': bank['code'],
                'bank_name': bank['name'],
                'valid_from': timezone.now().date(),
                'valid_to': (timezone.now() + timedelta(days=60)).date(),
                'offer_type': offer_type,
                'category': category,
                'discount_percentage': discount,
                'merchant': merchant[:100],
                'city': city_name.upper().replace(' ', '_'),
                'source_url': link or base_url,
                'scraped_at': timezone.now(),
                'is_active': True,
                'terms_conditions': f"Valid for {bank['name']} cardholders in {city_name}. Terms apply.",
            }
            
            return offer
            
        except Exception as e:
            logger.debug(f"Error extracting offer: {str(e)}")
            return None
    
    def _extract_from_text(self, soup: BeautifulSoup, bank: Dict, city_name: str, url: str) -> List[Dict]:
        """Extract offers from text content"""
        offers = []
        
        try:
            # Look for offer sections
            offer_sections = soup.find_all(['section', 'article', 'div'], class_=re.compile(r'offer|deal|discount|promotion', re.I))
            
            for section in offer_sections[:10]:  # Limit to 10 sections
                try:
                    text = section.get_text(' ', strip=True)
                    if len(text) < 50:  # Too short
                        continue
                    
                    # Extract title
                    title = ''
                    title_elements = section.find_all(['h2', 'h3', 'h4', 'h5', 'strong', 'b'])
                    if title_elements:
                        title = title_elements[0].get_text(strip=True)
                    
                    if not title:
                        # Look for common patterns
                        title_patterns = [
                            r'(?:Get|Save|Enjoy|Avail)\s+(\d+%?\s+(?:off|discount|cashback)[^.!?]+)',
                            r'(?:Discount|Offer|Deal)\s+on\s+([^.!?]+)',
                        ]
                        
                        for pattern in title_patterns:
                            match = re.search(pattern, text, re.IGNORECASE)
                            if match:
                                title = match.group(1).strip()
                                break
                    
                    if not title:
                        continue
                    
                    # Extract merchant
                    merchant = self._extract_merchant(text, title)
                    
                    # Extract discount
                    discount = self._extract_discount(text)
                    
                    # Get description (first 2-3 sentences)
                    sentences = re.split(r'[.!?]+', text)
                    description = ' '.join(sentences[:3]).strip()[:500]
                    
                    offer = {
                        'title': title[:200],
                        'description': description,
                        'bank_code': bank['code'],
                        'bank_name': bank['name'],
                        'valid_from': timezone.now().date(),
                        'valid_to': (timezone.now() + timedelta(days=60)).date(),
                        'offer_type': 'DISCOUNT',
                        'category': self._categorize_offer(text),
                        'discount_percentage': discount,
                        'merchant': merchant[:100],
                        'city': city_name.upper().replace(' ', '_'),
                        'source_url': url,
                        'scraped_at': timezone.now(),
                        'is_active': True,
                        'terms_conditions': f"Valid for {bank['name']} cardholders in {city_name}. Terms and conditions apply.",
                    }
                    
                    offers.append(offer)
                    
                except Exception as e:
                    logger.debug(f"Error processing section: {str(e)}")
                    continue
        
        except Exception as e:
            logger.error(f"Error extracting from text: {str(e)}")
        
        return offers

    def _extract_merchant(self, text: str, title: str) -> str:
        """Extract merchant name from text"""
        # Common Pakistani merchants
        pakistani_merchants = [
            'Foodpanda', 'Daraz', 'Careem', 'Bykea', 'Uber',
            'KFC', 'McDonald\'s', 'Pizza Hut', 'Domino\'s', 'Hardee\'s',
            'Subway', 'Gloria Jeans', 'Cup & Cino', 'Java',
            'Metro', 'Hyperstar', 'Chase Up', 'Naheed', 'Imtiaz',
            'Shell', 'PSO', 'Total', 'Attock', 'Hascol',
        ]
        
        text_lower = text.lower()
        for merchant in pakistani_merchants:
            if merchant.lower() in text_lower:
                return merchant
        
        # Try to extract from patterns
        patterns = [
            r'at\s+([A-Z][a-zA-Z\s&]+(?:Mall|Store|Shop|Restaurant|Hotel|Cafe))',
            r'with\s+([A-Z][a-zA-Z\s&]+)',
            r'on\s+([A-Z][a-zA-Z\s&]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                merchant = match.group(1).strip()
                if 2 < len(merchant) < 50:
                    return merchant
        
        # Try to get from title
        if ' at ' in title.lower():
            parts = title.lower().split(' at ')
            if len(parts) > 1:
                merchant = parts[1].strip().title()
                if len(merchant) > 2:
                    return merchant
        
        return "Various Merchants"
    
    def _extract_discount(self, text: str) -> Optional[float]:
        """Extract discount percentage from text"""
        patterns = [
            r'(\d{1,3})%\s*(?:off|discount|save|cashback)',
            r'save\s*(\d{1,3})%',
            r'(\d{1,3})%\s*saving',
            r'upto\s*(\d{1,3})%',
            r'up to\s*(\d{1,3})%',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except:
                    continue
        
        # Try generic percentage pattern
        percent_matches = re.findall(r'(\d{1,3})%', text)
        if percent_matches:
            try:
                return float(percent_matches[0])
            except:
                pass
        
        return None
    
    def _determine_offer_type(self, text: str) -> str:
        """Determine offer type from text"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['discount', '% off', 'off', 'save']):
            return 'DISCOUNT'
        elif any(word in text_lower for word in ['cashback', 'cash back']):
            return 'CASHBACK'
        elif any(word in text_lower for word in ['emi', 'installment']):
            return 'EMI'
        elif any(word in text_lower for word in ['bonus', 'welcome']):
            return 'WELCOME_BONUS'
        else:
            return 'OTHER'
    
    def _categorize_offer(self, text: str) -> str:
        """Categorize offer based on text"""
        text_lower = text.lower()
        
        categories = {
            'DINING': ['restaurant', 'cafe', 'coffee', 'food', 'pizza', 'burger', 'bbq', 'dining', 'eat'],
            'SHOPPING': ['shopping', 'mall', 'store', 'retail', 'fashion', 'clothing', 'apparel'],
            'FUEL': ['fuel', 'petrol', 'gas', 'shell', 'pso', 'total', 'attock'],
            'GROCERIES': ['grocery', 'supermarket', 'metro', 'naheed', 'imtiaz', 'hyperstar'],
            'TRAVEL': ['hotel', 'travel', 'flight', 'airline', 'booking', 'ticket'],
            'ELECTRONICS': ['electronics', 'mobile', 'phone', 'laptop', 'computer'],
            'ENTERTAINMENT': ['movie', 'cinema', 'entertainment', 'game'],
            'HEALTHCARE': ['hospital', 'clinic', 'pharmacy', 'medical'],
        }
        
        for category, keywords in categories.items():
            if any(keyword in text_lower for keyword in keywords):
                return category
        
        return 'OTHER'
    
    def _matches_merchant_type(self, offer: Dict, merchant_type: str) -> bool:
        """Check if offer matches merchant type"""
        category = offer.get('category', '').upper()
        
        # Map categories to merchant types
        category_to_merchant = {
            'DINING': 'RESTAURANT',
            'TRAVEL': 'TRAVEL',
            'SHOPPING': 'RETAIL',
            'GROCERIES': 'SUPERMARKET',
            'FUEL': 'FUEL_STATION',
            'ELECTRONICS': 'ELECTRONICS',
            'ENTERTAINMENT': 'ENTERTAINMENT',
            'HEALTHCARE': 'HEALTHCARE',
        }
        
        offer_merchant_type = category_to_merchant.get(category, 'OTHER')
        return offer_merchant_type == merchant_type.upper()
    
    def scrape_all_banks_with_filters(self, filters: Dict[str, Any]) -> Dict[str, List[Dict]]:
        """Scrape all banks with filters"""
        results = {}
        
        for bank_code in self.banks.keys():
            try:
                offers = self.scrape_bank_with_filters(bank_code, filters)
                results[bank_code] = offers
                logger.info(f"Scraped {len(offers)} offers from {bank_code}")
                
            except Exception as e:
                logger.error(f"Error scraping {bank_code}: {str(e)}")
                results[bank_code] = []
        
        return results

# Synchronous wrapper
def scrape_banks_with_filters_sync_simple(filters: Dict[str, Any]) -> Dict[str, List[Dict]]:
    """Synchronous wrapper for simple scraper"""
    scraper = SimpleBankScraper()
    return scraper.scrape_all_banks_with_filters(filters)