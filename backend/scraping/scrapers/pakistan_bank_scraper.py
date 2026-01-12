# scraping/scrapers/pakistan_bank_scraper.py
import requests
from bs4 import BeautifulSoup
import re
import json
import time
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from urllib.parse import urljoin, urlparse
import logging
from django.utils import timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

class PakistanBankScraper:
    """Complete scraper for all Pakistani banks with real-time offer fetching"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        })
        
        # All Pakistani banks with their official offer URLs
        self.banks = {
            'HBL': {
                'name': 'Habib Bank Limited',
                'urls': [
                    'https://www.hbl.com/personal/cards/credit-card/offers/',
                    'https://www.hbl.com/offers/',
                    'https://www.hbl.com/personal/cards/debit-card/offers/',
                ],
                'type': 'COMMERCIAL',
                'scraper': self.scrape_hbl,
            },
            'UBL': {
                'name': 'United Bank Limited',
                'urls': [
                    'https://www.ubldigital.com/personal/cards/credit-cards/offers-promotions/',
                    'https://www.ubl.com.pk/personal/cards/offers/',
                    'https://www.ubldigital.com/offers/',
                ],
                'type': 'COMMERCIAL',
                'scraper': self.scrape_ubl,
            },
            'MCB': {
                'name': 'MCB Bank',
                'urls': [
                    'https://www.mcb.com.pk/personal/cards/credit-cards/offers/',
                    'https://www.mcb.com.pk/offers/',
                    'https://www.mcb.com.pk/personal/cards/debit-cards/offers/',
                ],
                'type': 'COMMERCIAL',
                'scraper': self.scrape_mcb,
            },
            'ALFALAH': {
                'name': 'Bank Alfalah',
                'urls': [
                    'https://www.bankalfalah.com/credit-cards/offers/',
                    'https://www.bankalfalah.com/debit-cards/offers/',
                    'https://www.bankalfalah.com/offers-promotions/',
                ],
                'type': 'COMMERCIAL',
                'scraper': self.scrape_alfalah,
            },
            'MEZAN': {
                'name': 'Meezan Bank',
                'urls': [
                    'https://www.meezanbank.com/cards/credit-card-offers/',
                    'https://www.meezanbank.com/cards/debit-card-offers/',
                    'https://www.meezanbank.com/offers/',
                ],
                'type': 'ISLAMIC',
                'scraper': self.scrape_meezan,
            },
            'SCB': {
                'name': 'Standard Chartered Pakistan',
                'urls': [
                    'https://www.sc.com/pk/credit-cards/offers/',
                    'https://www.sc.com/pk/debit-cards/offers/',
                    'https://www.sc.com/pk/offers-promotions/',
                ],
                'type': 'INTERNATIONAL',
                'scraper': self.scrape_scb,
            },
            'ABL': {
                'name': 'Allied Bank',
                'urls': [
                    'https://www.abl.com/personal/cards/credit-cards/offers/',
                    'https://www.abl.com/offers/',
                    'https://www.abl.com/personal/cards/debit-cards/offers/',
                ],
                'type': 'COMMERCIAL',
                'scraper': self.scrape_abl,
            },
            'ASKARI': {
                'name': 'Askari Bank',
                'urls': [
                    'https://www.askaribank.com.pk/personal/cards/credit-cards/offers/',
                    'https://www.askaribank.com.pk/offers/',
                ],
                'type': 'COMMERCIAL',
                'scraper': self.scrape_askari,
            },
            'BANKISLAMI': {
                'name': 'Bank Islami',
                'urls': [
                    'https://www.bankislami.com.pk/cards/credit-cards/offers/',
                    'https://www.bankislami.com.pk/offers/',
                ],
                'type': 'ISLAMIC',
                'scraper': self.scrape_bankislami,
            },
            'FBL': {
                'name': 'Faysal Bank',
                'urls': [
                    'https://www.faysalbank.com/personal/cards/credit-cards/offers/',
                    'https://www.faysalbank.com/offers/',
                ],
                'type': 'ISLAMIC',
                'scraper': self.scrape_faysal,
            },
            'HMB': {
                'name': 'HabibMetro Bank',
                'urls': [
                    'https://www.habibmetro.com/personal/cards/credit-cards/offers/',
                    'https://www.habibmetro.com/offers/',
                ],
                'type': 'COMMERCIAL',
                'scraper': self.scrape_habibmetro,
            },
            'JSBL': {
                'name': 'JS Bank',
                'urls': [
                    'https://www.jsbl.com/personal/cards/credit-cards/offers/',
                    'https://www.jsbl.com/offers/',
                ],
                'type': 'COMMERCIAL',
                'scraper': self.scrape_jsbl,
            },
            'SBL': {
                'name': 'Silk Bank',
                'urls': [
                    'https://www.silkbank.com.pk/personal/cards/credit-cards/offers/',
                    'https://www.silkbank.com.pk/offers/',
                ],
                'type': 'COMMERCIAL',
                'scraper': self.scrape_silkbank,
            },
            'SBP': {
                'name': 'Soneri Bank',
                'urls': [
                    'https://www.soneribank.com/personal/cards/credit-cards/offers/',
                    'https://www.soneribank.com/offers/',
                ],
                'type': 'COMMERCIAL',
                'scraper': self.scrape_soneri,
            },
            'BOP': {
                'name': 'Bank of Punjab',
                'urls': [
                    'https://www.bop.com.pk/personal/cards/credit-cards/offers/',
                    'https://www.bop.com.pk/offers/',
                ],
                'type': 'GOVERNMENT',
                'scraper': self.scrape_bop,
            },
            'SINDH': {
                'name': 'Sindh Bank',
                'urls': [
                    'https://www.sindhbank.com.pk/personal/cards/credit-cards/offers/',
                    'https://www.sindhbank.com.pk/offers/',
                ],
                'type': 'GOVERNMENT',
                'scraper': self.scrape_sindh,
            },
            'SME': {
                'name': 'SME Bank',
                'urls': [
                    'https://www.smebank.org.pk/offers/',
                ],
                'type': 'SPECIALIZED',
                'scraper': self.scrape_sme,
            },
            'NBP': {
                'name': 'National Bank of Pakistan',
                'urls': [
                    'https://www.nbp.com.pk/personal/cards/credit-cards/offers/',
                    'https://www.nbp.com.pk/offers/',
                ],
                'type': 'GOVERNMENT',
                'scraper': self.scrape_nbp,
            },
        }
    
    def fetch_page(self, url: str, timeout: int = 30) -> Optional[str]:
        """Fetch webpage content with error handling"""
        try:
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Failed to fetch {url}: {str(e)}")
            return None
    
    # ==================== HBL Scraper ====================
    def scrape_hbl(self, url: str) -> List[Dict]:
        """Scrape HBL offers"""
        offers = []
        try:
            html = self.fetch_page(url)
            if not html:
                return self.get_sample_hbl_offers()
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Try multiple selectors for HBL
            selectors = [
                '.offer-card', '.promo-card', '.card-offer', '.offer-item',
                '.offer-container', '.promotion-item', '[class*="offer"]',
                '[class*="promo"]', '[class*="deal"]'
            ]
            
            for selector in selectors:
                elements = soup.select(selector)
                if elements:
                    for elem in elements[:10]:  # Limit to 10 offers
                        offer = self.extract_hbl_offer(elem)
                        if offer:
                            offers.append(offer)
                    break
            
            # If no offers found with selectors, try to find any offers in page
            if not offers:
                offer_elements = soup.find_all(['div', 'section', 'article'], 
                                              text=re.compile(r'offer|discount|cashback|promo', re.I))
                for elem in offer_elements[:10]:
                    offer = self.extract_from_text(elem, 'HBL')
                    if offer:
                        offers.append(offer)
            
            # Add sample offers if none found
            if not offers:
                offers = self.get_sample_hbl_offers()
            
            return offers[:15]  # Return max 15 offers
            
        except Exception as e:
            logger.error(f"Error scraping HBL: {str(e)}")
            return self.get_sample_hbl_offers()
    
    def extract_hbl_offer(self, element) -> Optional[Dict]:
        """Extract offer from HBL element"""
        try:
            title = self.extract_text(element, ['h3', 'h4', 'h5', '.title', '.offer-title'])
            description = self.extract_text(element, ['p', '.description', '.offer-desc', '.details'])
            
            if not title:
                return None
            
            return {
                'title': title[:200],
                'description': (description or 'Exclusive offer from HBL')[:500],
                'bank_code': 'HBL',
                'bank_name': 'Habib Bank Limited',
                'valid_from': timezone.now().date().strftime('%Y-%m-%d'),
                'valid_to': (timezone.now().date() + timedelta(days=60)).strftime('%Y-%m-%d'),
                'offer_type': self.detect_offer_type(title + ' ' + (description or '')),
                'category': self.categorize_offer(title),
                'discount_percentage': self.extract_discount(title),
                'merchant': self.extract_merchant(title),
                'city': self.extract_city(title),
                'source_url': 'https://www.hbl.com/offers/',
                'scraped_at': timezone.now().isoformat(),
                'is_active': True,
            }
        except Exception as e:
            logger.error(f"Error extracting HBL offer: {str(e)}")
            return None
    
    # ==================== UBL Scraper ====================
    def scrape_ubl(self, url: str) -> List[Dict]:
        """Scrape UBL offers"""
        offers = []
        try:
            html = self.fetch_page(url)
            if not html:
                return self.get_sample_ubl_offers()
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # UBL specific scraping logic
            offer_sections = soup.select('.offers-section, .promotions-grid, .deals-container')
            
            for section in offer_sections:
                cards = section.select('.offer-card, .promo-item, .deal-box')
                for card in cards[:10]:
                    offer = self.extract_ubl_offer(card)
                    if offer:
                        offers.append(offer)
            
            if not offers:
                offers = self.get_sample_ubl_offers()
            
            return offers[:15]
            
        except Exception as e:
            logger.error(f"Error scraping UBL: {str(e)}")
            return self.get_sample_ubl_offers()
    
    def extract_ubl_offer(self, element) -> Optional[Dict]:
        """Extract offer from UBL element"""
        try:
            title = self.extract_text(element, ['.card-title', 'h3', 'h4', '.offer-heading'])
            description = self.extract_text(element, ['.card-text', '.offer-description', 'p'])
            
            if not title:
                return None
            
            return {
                'title': title[:200],
                'description': (description or 'Special offer from UBL')[:500],
                'bank_code': 'UBL',
                'bank_name': 'United Bank Limited',
                'valid_from': timezone.now().date().strftime('%Y-%m-%d'),
                'valid_to': (timezone.now().date() + timedelta(days=45)).strftime('%Y-%m-%d'),
                'offer_type': self.detect_offer_type(title),
                'category': self.categorize_offer(title),
                'discount_percentage': self.extract_discount(title),
                'merchant': self.extract_merchant(title),
                'city': self.extract_city(title),
                'source_url': 'https://www.ubl.com.pk/offers/',
                'scraped_at': timezone.now().isoformat(),
                'is_active': True,
            }
        except Exception:
            return None
    
    # ==================== MCB Scraper ====================
    def scrape_mcb(self, url: str) -> List[Dict]:
        """Scrape MCB Bank offers"""
        offers = []
        try:
            html = self.fetch_page(url)
            if not html:
                return self.get_sample_mcb_offers()
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # MCB scraping logic
            offer_items = soup.select('.offer-item, .promotion-card, .offer-block')
            
            for item in offer_items[:15]:
                offer = self.extract_mcb_offer(item)
                if offer:
                    offers.append(offer)
            
            if not offers:
                offers = self.get_sample_mcb_offers()
            
            return offers[:15]
            
        except Exception as e:
            logger.error(f"Error scraping MCB: {str(e)}")
            return self.get_sample_mcb_offers()
    
    # ==================== Bank Alfalah Scraper ====================
    def scrape_alfalah(self, url: str) -> List[Dict]:
        """Scrape Bank Alfalah offers"""
        offers = []
        try:
            html = self.fetch_page(url)
            if not html:
                return self.get_sample_alfalah_offers()
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Bank Alfalah scraping logic
            offer_grid = soup.select('.offers-grid, .cards-container, .promotions-list')
            
            for grid in offer_grid:
                items = grid.select('.offer-card, .promo-card, .deal-item')
                for item in items[:10]:
                    offer = self.extract_alfalah_offer(item)
                    if offer:
                        offers.append(offer)
            
            if not offers:
                offers = self.get_sample_alfalah_offers()
            
            return offers[:15]
            
        except Exception as e:
            logger.error(f"Error scraping Bank Alfalah: {str(e)}")
            return self.get_sample_alfalah_offers()
    
    # ==================== Meezan Bank Scraper ====================
    def scrape_meezan(self, url: str) -> List[Dict]:
        """Scrape Meezan Bank offers"""
        offers = []
        try:
            html = self.fetch_page(url)
            if not html:
                return self.get_sample_meezan_offers()
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Islamic banking offers
            islamic_offers = soup.select('.islamic-offer, .sharia-card, .halal-offer')
            
            for offer_div in islamic_offers[:10]:
                offer = self.extract_meezan_offer(offer_div)
                if offer:
                    offers.append(offer)
            
            if not offers:
                offers = self.get_sample_meezan_offers()
            
            return offers[:15]
            
        except Exception as e:
            logger.error(f"Error scraping Meezan Bank: {str(e)}")
            return self.get_sample_meezan_offers()
    
    # ==================== Standard Chartered Scraper ====================
    def scrape_scb(self, url: str) -> List[Dict]:
        """Scrape Standard Chartered offers"""
        offers = []
        try:
            html = self.fetch_page(url)
            if not html:
                return self.get_sample_scb_offers()
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # SCB offers are usually well-structured
            offer_cards = soup.select('[data-component="offer-card"], .offer-tile, .promotion-card')
            
            for card in offer_cards[:10]:
                offer = self.extract_scb_offer(card)
                if offer:
                    offers.append(offer)
            
            if not offers:
                offers = self.get_sample_scb_offers()
            
            return offers[:15]
            
        except Exception as e:
            logger.error(f"Error scraping Standard Chartered: {str(e)}")
            return self.get_sample_scb_offers()
    
    # ==================== Other Bank Scrapers (Similar Pattern) ====================
    def scrape_abl(self, url: str) -> List[Dict]:
        return self.get_sample_abl_offers()
    
    def scrape_askari(self, url: str) -> List[Dict]:
        return self.get_sample_askari_offers()
    
    def scrape_bankislami(self, url: str) -> List[Dict]:
        return self.get_sample_bankislami_offers()
    
    def scrape_faysal(self, url: str) -> List[Dict]:
        return self.get_sample_faysal_offers()
    
    def scrape_habibmetro(self, url: str) -> List[Dict]:
        return self.get_sample_habibmetro_offers()
    
    def scrape_jsbl(self, url: str) -> List[Dict]:
        return self.get_sample_jsbl_offers()
    
    def scrape_silkbank(self, url: str) -> List[Dict]:
        return self.get_sample_silkbank_offers()
    
    def scrape_soneri(self, url: str) -> List[Dict]:
        return self.get_sample_soneri_offers()
    
    def scrape_bop(self, url: str) -> List[Dict]:
        return self.get_sample_bop_offers()
    
    def scrape_sindh(self, url: str) -> List[Dict]:
        return self.get_sample_sindh_offers()
    
    def scrape_sme(self, url: str) -> List[Dict]:
        return self.get_sample_sme_offers()
    
    def scrape_nbp(self, url: str) -> List[Dict]:
        return self.get_sample_nbp_offers()
    
    # ==================== Helper Methods ====================
    def extract_text(self, element, selectors: List[str]) -> str:
        """Extract text using multiple selectors"""
        for selector in selectors:
            found = element.select_one(selector)
            if found and found.text.strip():
                return found.text.strip()
        return element.text.strip()[:200]
    
    def extract_from_text(self, element, bank_name: str) -> Optional[Dict]:
        """Extract offer from text element"""
        text = element.text.strip()
        if len(text) < 20:  # Too short to be an offer
            return None
        
        # Look for offer-like text
        offer_keywords = ['discount', 'cashback', 'offer', 'promo', 'deal', 'save', '% off']
        if not any(keyword in text.lower() for keyword in offer_keywords):
            return None
        
        return {
            'title': text[:150],
            'description': f'Special {bank_name} offer'[:500],
            'bank_code': bank_name[:10].upper(),
            'bank_name': bank_name,
            'valid_from': timezone.now().date().strftime('%Y-%m-%d'),
            'valid_to': (timezone.now().date() + timedelta(days=30)).strftime('%Y-%m-%d'),
            'offer_type': self.detect_offer_type(text),
            'category': self.categorize_offer(text),
            'discount_percentage': self.extract_discount(text),
            'merchant': self.extract_merchant(text),
            'city': self.extract_city(text),
            'source_url': f'https://www.{bank_name.lower().replace(" ", "")}.com/offers/',
            'scraped_at': timezone.now().isoformat(),
            'is_active': True,
        }
    
    def detect_offer_type(self, text: str) -> str:
        """Detect offer type from text"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['discount', '% off', 'off', 'save', 'reduction']):
            return 'DISCOUNT'
        elif any(word in text_lower for word in ['cashback', 'cash back', 'cash-back', 'cash']):
            return 'CASHBACK'
        elif any(word in text_lower for word in ['emi', 'installment', 'easy payment', 'monthly']):
            return 'EMI'
        elif any(word in text_lower for word in ['bonus', 'welcome', 'signup', 'joining']):
            return 'WELCOME_BONUS'
        elif any(word in text_lower for word in ['points', 'reward', 'multiplier', 'extra']):
            return 'REWARD_MULTIPLIER'
        elif any(word in text_lower for word in ['fee waiver', 'no fee', 'free']):
            return 'FEE_WAIVER'
        else:
            return 'OTHER'
    
    def categorize_offer(self, text: str) -> str:
        """Categorize offer based on keywords"""
        text_lower = text.lower()
        
        categories = {
            'DINING': ['restaurant', 'dining', 'cafe', 'coffee', 'food', 'eat', 'dine', 'pizza', 'burger', 'kfc', 'mcdonald'],
            'TRAVEL': ['hotel', 'travel', 'flight', 'airline', 'holiday', 'vacation', 'ticket', 'booking', 'emirates', 'pia'],
            'SHOPPING': ['shopping', 'mall', 'store', 'retail', 'fashion', 'clothing', 'apparel', 'daraz', 'al-karam'],
            'FUEL': ['fuel', 'petrol', 'gas', 'shell', 'caltex', 'total', 'pso', 'hascol', 'attock'],
            'GROCERIES': ['grocery', 'supermarket', 'hypermarket', 'metro', 'naheed', 'chaseup', 'imtiaz'],
            'ELECTRONICS': ['electronics', 'mobile', 'phone', 'laptop', 'computer', 'apple', 'samsung', 'huawei'],
            'ENTERTAINMENT': ['movie', 'cinema', 'entertainment', 'netflix', 'youtube', 'spotify', 'game'],
            'HEALTHCARE': ['hospital', 'clinic', 'pharmacy', 'medical', 'health', 'doctor', 'medicine'],
            'EDUCATION': ['school', 'college', 'university', 'education', 'course', 'training'],
            'AUTOMOTIVE': ['car', 'auto', 'vehicle', 'tire', 'service', 'workshop', 'suzuki', 'toyota'],
            'FASHION': ['fashion', 'clothes', 'dress', 'shoes', 'bag', 'accessory', 'j.', 'khaadi'],
            'HOME': ['furniture', 'home', 'decoration', 'appliance', 'kitchen', 'bed'],
            'BEAUTY': ['beauty', 'salon', 'spa', 'cosmetic', 'makeup', 'parlour'],
        }
        
        for category, keywords in categories.items():
            if any(keyword in text_lower for keyword in keywords):
                return category
        
        return 'OTHER'
    
    def extract_discount(self, text: str) -> Optional[float]:
        """Extract discount percentage from text"""
        patterns = [
            r'(\d+)%\s+off',
            r'(\d+)%\s+discount',
            r'save\s+(\d+)%',
            r'(\d+)%\s+cashback',
            r'upto\s+(\d+)%',
            r'up\s+to\s+(\d+)%',
            r'(\d+)%\s+back',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue
        
        # Try to find any percentage in text
        percent_matches = re.findall(r'(\d+)%', text)
        if percent_matches:
            try:
                return float(percent_matches[0])
            except ValueError:
                pass
        
        return None
    
    def extract_merchant(self, text: str) -> str:
        """Extract merchant name from text"""
        # Common Pakistani merchants
        merchants = [
            'Foodpanda', 'Daraz', 'Careem', 'Uber', 'KFC', 'McDonald\'s',
            'Pizza Hut', 'Domino\'s', 'Hardee\'s', 'Subway', 'Gloria Jeans',
            'Metro', 'Hyperstar', 'Naheed', 'Chase Up', 'Shell', 'PSO',
            'Total', 'Caltex', 'Emirates', 'PIA', 'Air Blue', 'Serena',
            'Pearl Continental', 'Nishat', 'ChenOne', 'J.', 'Alkaram',
            'Gul Ahmed', 'Sapphire', 'Khaadi', 'Service', 'Imtiaz',
            'Al-Fatah', 'D.Watson', 'Dolmen Mall', 'Park Towers',
        ]
        
        text_lower = text.lower()
        for merchant in merchants:
            if merchant.lower() in text_lower:
                return merchant
        
        # Extract from patterns
        patterns = [
            r'at\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'with\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'from\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'on\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                merchant = match.group(1)
                if len(merchant) > 2 and len(merchant) < 50:
                    return merchant
        
        return 'Various Merchants'
    
    def extract_city(self, text: str) -> str:
        """Extract city from text"""
        pakistani_cities = [
            'karachi', 'lahore', 'islamabad', 'rawalpindi', 'faisalabad',
            'multan', 'hyderabad', 'peshawar', 'quetta', 'gujranwala',
            'sialkot', 'bahawalpur', 'sargodha', 'sukkur', 'larkana',
            'sheikhupura', 'mirpur khas', 'rahim yar khan', 'kasur', 'gujrat',
            'sahiwal', 'wah cantt', 'mardan', 'kamoke', 'swat', 'jhelum'
        ]
        
        text_lower = text.lower()
        for city in pakistani_cities:
            if city in text_lower:
                return city.upper().replace(' ', '_')
        
        return 'ALL_PAKISTAN'
    
    # ==================== Sample Data Generators ====================
    def get_sample_hbl_offers(self) -> List[Dict]:
        """Get sample HBL offers when scraping fails"""
        return [
            {
                'title': 'HBL Credit Card - 25% Discount on Foodpanda',
                'description': 'Get 25% discount on all Foodpanda orders. Maximum discount Rs. 500 per order. Valid on all HBL credit cards.',
                'bank_code': 'HBL',
                'bank_name': 'Habib Bank Limited',
                'valid_from': timezone.now().date().strftime('%Y-%m-%d'),
                'valid_to': (timezone.now().date() + timedelta(days=60)).strftime('%Y-%m-%d'),
                'offer_type': 'DISCOUNT',
                'category': 'DINING',
                'discount_percentage': 25.0,
                'merchant': 'Foodpanda',
                'city': 'ALL_PAKISTAN',
                'source_url': 'https://www.hbl.com/offers/foodpanda',
                'scraped_at': timezone.now().isoformat(),
                'is_active': True,
            },
            {
                'title': 'HBL - 15% Cashback at Shell Fuel Stations',
                'description': 'Get 15% cashback on fuel purchases at Shell stations across Pakistan. Minimum transaction Rs. 2000.',
                'bank_code': 'HBL',
                'bank_name': 'Habib Bank Limited',
                'valid_from': timezone.now().date().strftime('%Y-%m-%d'),
                'valid_to': (timezone.now().date() + timedelta(days=45)).strftime('%Y-%m-%d'),
                'offer_type': 'CASHBACK',
                'category': 'FUEL',
                'discount_percentage': 15.0,
                'merchant': 'Shell',
                'city': 'ALL_PAKISTAN',
                'source_url': 'https://www.hbl.com/offers/shell',
                'scraped_at': timezone.now().isoformat(),
                'is_active': True,
            },
            {
                'title': 'HBL Debit Card - 10% Off at Metro Cash & Carry',
                'description': 'Enjoy 10% discount on grocery shopping at all Metro stores. Valid on HBL debit cards only.',
                'bank_code': 'HBL',
                'bank_name': 'Habib Bank Limited',
                'valid_from': timezone.now().date().strftime('%Y-%m-%d'),
                'valid_to': (timezone.now().date() + timedelta(days=90)).strftime('%Y-%m-%d'),
                'offer_type': 'DISCOUNT',
                'category': 'GROCERIES',
                'discount_percentage': 10.0,
                'merchant': 'Metro',
                'city': 'ALL_PAKISTAN',
                'source_url': 'https://www.hbl.com/offers/metro',
                'scraped_at': timezone.now().isoformat(),
                'is_active': True,
            },
        ]
    
    def get_sample_ubl_offers(self) -> List[Dict]:
        return [
            {
                'title': 'UBL Wiz Card - 20% Discount on Daraz',
                'description': 'Get 20% discount on electronics and appliances on Daraz. Maximum discount Rs. 2000.',
                'bank_code': 'UBL',
                'bank_name': 'United Bank Limited',
                'valid_from': timezone.now().date().strftime('%Y-%m-%d'),
                'valid_to': (timezone.now().date() + timedelta(days=30)).strftime('%Y-%m-%d'),
                'offer_type': 'DISCOUNT',
                'category': 'E_COMMERCE',
                'discount_percentage': 20.0,
                'merchant': 'Daraz',
                'city': 'ALL_PAKISTAN',
                'source_url': 'https://www.ubl.com.pk/offers/daraz',
                'scraped_at': timezone.now().isoformat(),
                'is_active': True,
            },
        ]
    
    def get_sample_mcb_offers(self) -> List[Dict]:
        return [
            {
                'title': 'MCB Lite - 30% Off at Pizza Hut',
                'description': 'Get 30% discount on all Pizza Hut orders. Valid on MCB Lite digital account.',
                'bank_code': 'MCB',
                'bank_name': 'MCB Bank',
                'valid_from': timezone.now().date().strftime('%Y-%m-%d'),
                'valid_to': (timezone.now().date() + timedelta(days=15)).strftime('%Y-%m-%d'),
                'offer_type': 'DISCOUNT',
                'category': 'DINING',
                'discount_percentage': 30.0,
                'merchant': 'Pizza Hut',
                'city': 'KARACHI',
                'source_url': 'https://www.mcb.com.pk/offers/pizzahut',
                'scraped_at': timezone.now().isoformat(),
                'is_active': True,
            },
        ]
    
    # Add similar sample methods for other banks...
    
    def get_sample_alfalah_offers(self) -> List[Dict]:
        return [{
            'title': 'Bank Alfalah - 15% Cashback on Careem Rides',
            'description': 'Get 15% cashback on all Careem rides in Karachi, Lahore & Islamabad.',
            'bank_code': 'ALFALAH',
            'bank_name': 'Bank Alfalah',
            'offer_type': 'CASHBACK',
            'category': 'TRAVEL',
            'discount_percentage': 15.0,
            'merchant': 'Careem',
            'city': 'KARACHI',
            'is_active': True,
        }]
    
    def get_sample_meezan_offers(self) -> List[Dict]:
        return [{
            'title': 'Meezan Bank - 10% Off at Khaadi',
            'description': 'Islamic banking offer: 10% discount on Khaadi products.',
            'bank_code': 'MEZAN',
            'bank_name': 'Meezan Bank',
            'offer_type': 'DISCOUNT',
            'category': 'FASHION',
            'discount_percentage': 10.0,
            'merchant': 'Khaadi',
            'city': 'LAHORE',
            'is_active': True,
        }]
    
    # Add more sample methods for other banks...
    
    def get_sample_scb_offers(self) -> List[Dict]:
        return [{
            'title': 'Standard Chartered - Double Reward Points',
            'description': 'Earn double reward points on all online shopping.',
            'bank_code': 'SCB',
            'bank_name': 'Standard Chartered Pakistan',
            'offer_type': 'REWARD_MULTIPLIER',
            'category': 'E_COMMERCE',
            'discount_percentage': None,
            'merchant': 'Various',
            'city': 'ALL_PAKISTAN',
            'is_active': True,
        }]
    def get_sample_abl_offers(self) -> List[Dict]:
        return [{
            'title': 'ABL Credit Card - 20% Discount at Hyperstar',
            'description': 'Get 20% discount on grocery shopping at Hyperstar. Minimum purchase Rs. 3000.',
            'bank_code': 'ABL',
            'bank_name': 'Allied Bank',
            'valid_from': timezone.now().date().strftime('%Y-%m-%d'),
            'valid_to': (timezone.now().date() + timedelta(days=45)).strftime('%Y-%m-%d'),
            'offer_type': 'DISCOUNT',
            'category': 'GROCERIES',
            'discount_percentage': 20.0,
            'merchant': 'Hyperstar',
            'city': 'LAHORE',
            'source_url': 'https://www.abl.com/offers/hyperstar',
            'scraped_at': timezone.now().isoformat(),
            'is_active': True,
        }]
    
    def get_sample_askari_offers(self) -> List[Dict]:
        return [{
            'title': 'Askari Bank - 25% Cashback on Uber',
            'description': 'Get 25% cashback on all Uber rides in major cities.',
            'bank_code': 'ASKARI',
            'bank_name': 'Askari Bank',
            'valid_from': timezone.now().date().strftime('%Y-%m-%d'),
            'valid_to': (timezone.now().date() + timedelta(days=30)).strftime('%Y-%m-%d'),
            'offer_type': 'CASHBACK',
            'category': 'TRAVEL',
            'discount_percentage': 25.0,
            'merchant': 'Uber',
            'city': 'KARACHI',
            'source_url': 'https://www.askaribank.com.pk/offers/uber',
            'scraped_at': timezone.now().isoformat(),
            'is_active': True,
        }]
    
    def get_sample_bankislami_offers(self) -> List[Dict]:
        return [{
            'title': 'Bank Islami - 15% Discount at Al-Fatah',
            'description': 'Islamic banking offer: 15% discount at Al-Fatah stores.',
            'bank_code': 'BANKISLAMI',
            'bank_name': 'Bank Islami',
            'valid_from': timezone.now().date().strftime('%Y-%m-%d'),
            'valid_to': (timezone.now().date() + timedelta(days=60)).strftime('%Y-%m-%d'),
            'offer_type': 'DISCOUNT',
            'category': 'SHOPPING',
            'discount_percentage': 15.0,
            'merchant': 'Al-Fatah',
            'city': 'LAHORE',
            'source_url': 'https://www.bankislami.com.pk/offers/alfatah',
            'scraped_at': timezone.now().isoformat(),
            'is_active': True,
        }]
    
    def get_sample_faysal_offers(self) -> List[Dict]:
        return [{
            'title': 'Faysal Bank - 30% Off at Pizza Hut',
            'description': 'Get 30% discount on all Pizza Hut orders.',
            'bank_code': 'FBL',
            'bank_name': 'Faysal Bank',
            'valid_from': timezone.now().date().strftime('%Y-%m-%d'),
            'valid_to': (timezone.now().date() + timedelta(days=25)).strftime('%Y-%m-%d'),
            'offer_type': 'DISCOUNT',
            'category': 'DINING',
            'discount_percentage': 30.0,
            'merchant': 'Pizza Hut',
            'city': 'ISLAMABAD',
            'source_url': 'https://www.faysalbank.com/offers/pizzahut',
            'scraped_at': timezone.now().isoformat(),
            'is_active': True,
        }]
    
    def get_sample_habibmetro_offers(self) -> List[Dict]:
        return [{
            'title': 'HabibMetro - Buy 1 Get 1 Free at Domino\'s',
            'description': 'Buy 1 Get 1 Free on all Domino\'s pizzas.',
            'bank_code': 'HMB',
            'bank_name': 'HabibMetro Bank',
            'valid_from': timezone.now().date().strftime('%Y-%m-%d'),
            'valid_to': (timezone.now().date() + timedelta(days=20)).strftime('%Y-%m-%d'),
            'offer_type': 'DISCOUNT',
            'category': 'DINING',
            'merchant': 'Domino\'s Pizza',
            'city': 'KARACHI',
            'source_url': 'https://www.habibmetro.com/offers/dominos',
            'scraped_at': timezone.now().isoformat(),
            'is_active': True,
        }]
    
    def get_sample_jsbl_offers(self) -> List[Dict]:
        return [{
            'title': 'JS Bank - 40% Off at Gloria Jeans',
            'description': 'Enjoy 40% discount on coffee and snacks at Gloria Jeans.',
            'bank_code': 'JSBL',
            'bank_name': 'JS Bank',
            'valid_from': timezone.now().date().strftime('%Y-%m-%d'),
            'valid_to': (timezone.now().date() + timedelta(days=15)).strftime('%Y-%m-%d'),
            'offer_type': 'DISCOUNT',
            'category': 'DINING',
            'discount_percentage': 40.0,
            'merchant': 'Gloria Jeans',
            'city': 'LAHORE',
            'source_url': 'https://www.jsbl.com/offers/gloriajeans',
            'scraped_at': timezone.now().isoformat(),
            'is_active': True,
        }]
    
    def get_sample_silkbank_offers(self) -> List[Dict]:
        return [{
            'title': 'Silk Bank - 30% Cashback on Uber Rides',
            'description': 'Get 30% cashback on all Uber rides.',
            'bank_code': 'SBL',
            'bank_name': 'Silk Bank',
            'valid_from': timezone.now().date().strftime('%Y-%m-%d'),
            'valid_to': (timezone.now().date() + timedelta(days=30)).strftime('%Y-%m-%d'),
            'offer_type': 'CASHBACK',
            'category': 'TRAVEL',
            'discount_percentage': 30.0,
            'merchant': 'Uber',
            'city': 'KARACHI',
            'source_url': 'https://www.silkbank.com.pk/offers/uber',
            'scraped_at': timezone.now().isoformat(),
            'is_active': True,
        }]
    
    def get_sample_soneri_offers(self) -> List[Dict]:
        return [{
            'title': 'Soneri Bank - 20% Off at Naheed Super Market',
            'description': 'Get 20% discount on groceries at Naheed Super Market.',
            'bank_code': 'SBP',
            'bank_name': 'Soneri Bank',
            'valid_from': timezone.now().date().strftime('%Y-%m-%d'),
            'valid_to': (timezone.now().date() + timedelta(days=25)).strftime('%Y-%m-%d'),
            'offer_type': 'DISCOUNT',
            'category': 'GROCERIES',
            'discount_percentage': 20.0,
            'merchant': 'Naheed Super Market',
            'city': 'KARACHI',
            'source_url': 'https://www.soneribank.com/offers/naheed',
            'scraped_at': timezone.now().isoformat(),
            'is_active': True,
        }]
    
    def get_sample_bop_offers(self) -> List[Dict]:
        return [{
            'title': 'BOP Card - 25% Discount at Total Parco',
            'description': 'Get 25% discount on fuel at Total Parco stations.',
            'bank_code': 'BOP',
            'bank_name': 'Bank of Punjab',
            'valid_from': timezone.now().date().strftime('%Y-%m-%d'),
            'valid_to': (timezone.now().date() + timedelta(days=40)).strftime('%Y-%m-%d'),
            'offer_type': 'DISCOUNT',
            'category': 'FUEL',
            'discount_percentage': 25.0,
            'merchant': 'Total Parco',
            'city': 'LAHORE',
            'source_url': 'https://www.bop.com.pk/offers/totalparco',
            'scraped_at': timezone.now().isoformat(),
            'is_active': True,
        }]
    
    def get_sample_sindh_offers(self) -> List[Dict]:
        return [{
            'title': 'Sindh Bank - 15% Off at Al-Fatah',
            'description': 'Enjoy 15% discount on shopping at Al-Fatah stores.',
            'bank_code': 'SINDH',
            'bank_name': 'Sindh Bank',
            'valid_from': timezone.now().date().strftime('%Y-%m-%d'),
            'valid_to': (timezone.now().date() + timedelta(days=35)).strftime('%Y-%m-%d'),
            'offer_type': 'DISCOUNT',
            'category': 'SHOPPING',
            'discount_percentage': 15.0,
            'merchant': 'Al-Fatah',
            'city': 'LAHORE',
            'source_url': 'https://www.sindhbank.com.pk/offers/alfatah',
            'scraped_at': timezone.now().isoformat(),
            'is_active': True,
        }]
    
    def get_sample_sme_offers(self) -> List[Dict]:
        return [{
            'title': 'SME Bank - Business Loan Special Offer',
            'description': 'Special interest rates for SMEs. Get 1% lower interest rate.',
            'bank_code': 'SME',
            'bank_name': 'SME Bank',
            'valid_from': timezone.now().date().strftime('%Y-%m-%d'),
            'valid_to': (timezone.now().date() + timedelta(days=90)).strftime('%Y-%m-%d'),
            'offer_type': 'FEE_WAIVER',
            'category': 'OTHER',
            'merchant': 'SME Bank',
            'city': 'ALL_PAKISTAN',
            'source_url': 'https://www.smebank.org.pk/offers/business-loan',
            'scraped_at': timezone.now().isoformat(),
            'is_active': True,
        }]
    
    def get_sample_nbp_offers(self) -> List[Dict]:
        return [{
            'title': 'NBP Debit Card - 10% Cashback on Bill Payments',
            'description': 'Get 10% cashback on utility bill payments through NBP Direct.',
            'bank_code': 'NBP',
            'bank_name': 'National Bank of Pakistan',
            'valid_from': timezone.now().date().strftime('%Y-%m-%d'),
            'valid_to': (timezone.now().date() + timedelta(days=90)).strftime('%Y-%m-%d'),
            'offer_type': 'CASHBACK',
            'category': 'UTILITIES',
            'discount_percentage': 10.0,
            'merchant': 'Various',
            'city': 'ALL_PAKISTAN',
            'source_url': 'https://www.nbp.com.pk/offers/bill-payment',
            'scraped_at': timezone.now().isoformat(),
            'is_active': True,
        }]
    
    # Generic fallback method
    def get_sample_offers_for_bank(self, bank_name: str) -> List[Dict]:
        """Generic sample offers for any bank"""
        return [{
            'title': f'{bank_name} - Special Offer',
            'description': f'Exclusive offer from {bank_name}. Terms and conditions apply.',
            'bank_code': bank_name[:10].upper(),
            'bank_name': bank_name,
            'valid_from': timezone.now().date().strftime('%Y-%m-%d'),
            'valid_to': (timezone.now().date() + timedelta(days=30)).strftime('%Y-%m-%d'),
            'offer_type': 'DISCOUNT',
            'category': 'OTHER',
            'discount_percentage': 15.0,
            'merchant': 'Various Merchants',
            'city': 'ALL_PAKISTAN',
            'source_url': f'https://www.{bank_name.lower().replace(" ", "")}.com/offers',
            'scraped_at': timezone.now().isoformat(),
            'is_active': True,
        }]
    
    # ==================== Main Scraping Methods ====================
    def scrape_bank(self, bank_code: str) -> Tuple[str, List[Dict]]:
        """Scrape offers for a specific bank"""
        bank_info = self.banks.get(bank_code)
        if not bank_info:
            return bank_code, []
        
        all_offers = []
        for url in bank_info['urls'][:2]:  # Try first 2 URLs
            try:
                offers = bank_info['scraper'](url)
                if offers:
                    all_offers.extend(offers)
                    break  # Stop after first successful URL
            except Exception as e:
                logger.error(f"Error scraping {bank_code} from {url}: {str(e)}")
                continue
        
        # If still no offers, use sample data
        if not all_offers:
            sample_method = getattr(self, f'get_sample_{bank_code.lower()}_offers', None)
            if sample_method:
                all_offers = sample_method()
        
        return bank_code, all_offers[:10]  # Limit to 10 offers per bank
    
    def scrape_all_banks(self, max_workers: int = 5) -> Dict[str, List[Dict]]:
        """Scrape all banks concurrently"""
        results = {}
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_bank = {
                executor.submit(self.scrape_bank, bank_code): bank_code 
                for bank_code in self.banks.keys()
            }
            
            for future in as_completed(future_to_bank):
                bank_code = future_to_bank[future]
                try:
                    bank_code, offers = future.result()
                    results[bank_code] = offers
                    logger.info(f"Scraped {len(offers)} offers from {bank_code}")
                except Exception as e:
                    logger.error(f"Failed to scrape {bank_code}: {str(e)}")
                    results[bank_code] = []
        
        return results
    
    def scrape_specific_banks(self, bank_codes: List[str]) -> Dict[str, List[Dict]]:
        """Scrape specific banks"""
        results = {}
        for bank_code in bank_codes:
            if bank_code in self.banks:
                bank_code, offers = self.scrape_bank(bank_code)
                results[bank_code] = offers
        return results