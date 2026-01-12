# scraping/scrapers/enhanced_scraper.py
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
import time
from django.utils import timezone
from urllib.parse import urljoin
import logging

logger = logging.getLogger(__name__)

class EnhancedPakistanBankScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # Pakistani banks with their offer URLs
        self.banks = {
            'HBL': {
                'name': 'Habib Bank Limited',
                'url': 'https://www.hbl.com/personal/credit-cards/offers',
                'logo': 'https://www.hbl.com/assets/images/logo.png',
            },
            'UBL': {
                'name': 'United Bank Limited',
                'url': 'https://www.ubldigital.com/offers-promotions',
                'logo': 'https://www.ubl.com.pk/images/logo.png',
            },
            'MCB': {
                'name': 'MCB Bank',
                'url': 'https://www.mcb.com.pk/offers',
                'logo': 'https://www.mcb.com.pk/images/logo.png',
            },
            'ABL': {
                'name': 'Allied Bank',
                'url': 'https://www.abl.com/offers',
                'logo': 'https://www.abl.com/images/logo.png',
            },
            'Bank Alfalah': {
                'name': 'Bank Alfalah',
                'url': 'https://www.bankalfalah.com/credit-cards/offers',
                'logo': 'https://www.bankalfalah.com/images/logo.png',
            },
            'Meezan Bank': {
                'name': 'Meezan Bank',
                'url': 'https://www.meezanbank.com/cards/offers',
                'logo': 'https://www.meezanbank.com/images/logo.png',
            },
            'Standard Chartered': {
                'name': 'Standard Chartered Pakistan',
                'url': 'https://www.sc.com/pk/credit-cards/offers',
                'logo': 'https://www.sc.com/pk/images/logo.png',
            },
            'Faysal Bank': {
                'name': 'Faysal Bank',
                'url': 'https://www.faysalbank.com/offers',
                'logo': 'https://www.faysalbank.com/images/logo.png',
            },
            'Askari Bank': {
                'name': 'Askari Bank',
                'url': 'https://www.askaribank.com.pk/offers',
                'logo': 'https://www.askaribank.com.pk/images/logo.png',
            },
            'Bank Islami': {
                'name': 'Bank Islami',
                'url': 'https://www.bankislami.com.pk/offers',
                'logo': 'https://www.bankislami.com.pk/images/logo.png',
            },
            'Soneri Bank': {
                'name': 'Soneri Bank',
                'url': 'https://www.soneribank.com/offers',
                'logo': 'https://www.soneribank.com/images/logo.png',
            },
            'JS Bank': {
                'name': 'JS Bank',
                'url': 'https://www.jsbl.com/offers',
                'logo': 'https://www.jsbl.com/images/logo.png',
            },
            'Bank of Punjab': {
                'name': 'Bank of Punjab',
                'url': 'https://www.bop.com.pk/offers',
                'logo': 'https://www.bop.com.pk/images/logo.png',
            },
            'Silk Bank': {
                'name': 'Silk Bank',
                'url': 'https://www.silkbank.com.pk/offers',
                'logo': 'https://www.silkbank.com.pk/images/logo.png',
            },
            'Sindh Bank': {
                'name': 'Sindh Bank',
                'url': 'https://www.sindhbank.com.pk/offers',
                'logo': 'https://www.sindhbank.com.pk/images/logo.png',
            },
        }
    
    def scrape_hbl_offers(self) -> List[Dict]:
        """Scrape HBL offers"""
        offers = []
        try:
            url = "https://www.hbl.com/personal/credit-cards/offers"
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for offers in different sections
                offer_sections = soup.find_all(['div', 'section'], class_=re.compile(r'offer|promo|deal|campaign', re.I))
                
                for section in offer_sections:
                    title_elem = section.find(['h2', 'h3', 'h4', 'h5'], class_=re.compile(r'title|heading', re.I))
                    desc_elem = section.find('p', class_=re.compile(r'desc|text|detail', re.I))
                    image_elem = section.find('img')
                    
                    if title_elem:
                        offer = {
                            'title': title_elem.text.strip(),
                            'description': desc_elem.text.strip()[:500] if desc_elem else '',
                            'bank': 'HBL',
                            'bank_name': 'Habib Bank Limited',
                            'valid_from': datetime.now().strftime('%Y-%m-%d'),
                            'valid_to': (datetime.now() + timedelta(days=60)).strftime('%Y-%m-%d'),
                            'offer_type': self.detect_offer_type(title_elem.text),
                            'category': self.categorize_offer(title_elem.text),
                            'image_url': image_elem.get('src') if image_elem else '',
                            'source_url': url,
                            'scraped_at': timezone.now(),
                        }
                        offers.append(offer)
                        
        except Exception as e:
            logger.error(f"Error scraping HBL: {str(e)}")
        
        return offers
    
    def scrape_ubl_offers(self) -> List[Dict]:
        """Scrape UBL offers"""
        offers = []
        try:
            url = "https://www.ubldigital.com/offers-promotions"
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # UBL specific selectors
                cards = soup.select('.offer-card, .promotion-item, .deal-card')
                
                for card in cards:
                    title = card.select_one('.card-title, .title, h3, h4')
                    description = card.select_one('.card-text, .description, p')
                    
                    if title:
                        offer = {
                            'title': title.text.strip(),
                            'description': description.text.strip()[:500] if description else '',
                            'bank': 'UBL',
                            'bank_name': 'United Bank Limited',
                            'valid_from': datetime.now().strftime('%Y-%m-%d'),
                            'valid_to': (datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d'),
                            'offer_type': self.detect_offer_type(title.text),
                            'category': self.categorize_offer(title.text),
                            'source_url': url,
                            'scraped_at': timezone.now(),
                        }
                        offers.append(offer)
                        
        except Exception as e:
            logger.error(f"Error scraping UBL: {str(e)}")
        
        return offers
    
    def scrape_mcb_offers(self) -> List[Dict]:
        """Scrape MCB Bank offers"""
        offers = []
        try:
            url = "https://www.mcb.com.pk/offers"
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # MCB specific parsing
                offer_items = soup.find_all('div', class_=re.compile(r'offer|promotion', re.I))
                
                for item in offer_items:
                    title = item.find(['h3', 'h4', 'h5'])
                    details = item.find(['p', 'div'], class_=re.compile(r'desc|detail|text', re.I))
                    
                    if title:
                        offer = {
                            'title': title.text.strip(),
                            'description': details.text.strip()[:500] if details else '',
                            'bank': 'MCB',
                            'bank_name': 'MCB Bank',
                            'valid_from': datetime.now().strftime('%Y-%m-%d'),
                            'valid_to': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
                            'offer_type': 'DISCOUNT',
                            'category': self.categorize_offer(title.text),
                            'source_url': url,
                            'scraped_at': timezone.now(),
                        }
                        offers.append(offer)
                        
        except Exception as e:
            logger.error(f"Error scraping MCB: {str(e)}")
        
        return offers
    
    def scrape_bank_alfalah_offers(self) -> List[Dict]:
        """Scrape Bank Alfalah offers"""
        offers = []
        try:
            url = "https://www.bankalfalah.com/credit-cards/offers"
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Bank Alfalah specific selectors
                offers_div = soup.select('.offers-container, .promotions-grid, .deals-wrapper')
                
                for offer_div in offers_div:
                    items = offer_div.select('.offer-item, .promo-card, .deal-box')
                    
                    for item in items:
                        title = item.select_one('.offer-title, h3, h4')
                        desc = item.select_one('.offer-desc, .description')
                        terms = item.select_one('.terms, .conditions')
                        
                        if title:
                            offer = {
                                'title': title.text.strip(),
                                'description': desc.text.strip()[:500] if desc else '',
                                'bank': 'Bank Alfalah',
                                'bank_name': 'Bank Alfalah',
                                'valid_from': datetime.now().strftime('%Y-%m-%d'),
                                'valid_to': (datetime.now() + timedelta(days=45)).strftime('%Y-%m-%d'),
                                'offer_type': self.detect_offer_type(title.text),
                                'category': self.categorize_offer(title.text),
                                'terms_conditions': terms.text.strip() if terms else '',
                                'source_url': url,
                                'scraped_at': timezone.now(),
                            }
                            offers.append(offer)
                            
        except Exception as e:
            logger.error(f"Error scraping Bank Alfalah: {str(e)}")
        
        return offers
    
    def scrape_meezan_bank_offers(self) -> List[Dict]:
        """Scrape Meezan Bank offers"""
        offers = []
        try:
            url = "https://www.meezanbank.com/cards/offers"
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Islamic banking offers
                islamic_offers = soup.find_all(['div', 'section'], id=re.compile(r'offer|promo|islamic', re.I))
                
                for offer_section in islamic_offers:
                    headings = offer_section.find_all(['h2', 'h3', 'h4'])
                    paragraphs = offer_section.find_all('p')
                    
                    for i, heading in enumerate(headings[:3]):  # Limit to 3 offers per section
                        if i < len(paragraphs):
                            offer = {
                                'title': heading.text.strip(),
                                'description': paragraphs[i].text.strip()[:500],
                                'bank': 'Meezan Bank',
                                'bank_name': 'Meezan Bank',
                                'valid_from': datetime.now().strftime('%Y-%m-%d'),
                                'valid_to': (datetime.now() + timedelta(days=60)).strftime('%Y-%m-%d'),
                                'offer_type': 'CASHBACK',
                                'category': 'ISLAMIC_BANKING',
                                'source_url': url,
                                'scraped_at': timezone.now(),
                            }
                            offers.append(offer)
                            
        except Exception as e:
            logger.error(f"Error scraping Meezan Bank: {str(e)}")
        
        return offers
    
    def scrape_standard_chartered_offers(self) -> List[Dict]:
        """Scrape Standard Chartered offers"""
        offers = []
        try:
            url = "https://www.sc.com/pk/credit-cards/offers"
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # International bank offers
                offer_cards = soup.select('[class*="offer"], [class*="promo"], [class*="deal"]')
                
                for card in offer_cards:
                    title = card.select_one('[class*="title"], [class*="heading"]')
                    description = card.select_one('[class*="desc"], [class*="text"]')
                    
                    if title:
                        offer = {
                            'title': title.text.strip(),
                            'description': description.text.strip()[:500] if description else '',
                            'bank': 'Standard Chartered',
                            'bank_name': 'Standard Chartered Pakistan',
                            'valid_from': datetime.now().strftime('%Y-%m-%d'),
                            'valid_to': (datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d'),
                            'offer_type': self.detect_offer_type(title.text),
                            'category': 'INTERNATIONAL',
                            'source_url': url,
                            'scraped_at': timezone.now(),
                        }
                        offers.append(offer)
                        
        except Exception as e:
            logger.error(f"Error scraping Standard Chartered: {str(e)}")
        
        return offers
    
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
            'DINING': ['restaurant', 'dining', 'cafe', 'coffee', 'food', 'eat', 'dine', 'pizza', 'burger'],
            'TRAVEL': ['hotel', 'travel', 'flight', 'airline', 'holiday', 'vacation', 'ticket', 'booking'],
            'SHOPPING': ['shopping', 'mall', 'store', 'retail', 'fashion', 'clothing', 'apparel'],
            'FUEL': ['fuel', 'petrol', 'gas', 'shell', 'caltex', 'total', 'pso', 'hascol'],
            'GROCERIES': ['grocery', 'supermarket', 'hypermarket', 'metro', 'naheed', 'chaseup'],
            'ELECTRONICS': ['electronics', 'mobile', 'phone', 'laptop', 'computer', 'apple', 'samsung'],
            'ENTERTAINMENT': ['movie', 'cinema', 'entertainment', 'netflix', 'youtube', 'spotify'],
            'HEALTHCARE': ['hospital', 'clinic', 'pharmacy', 'medical', 'health', 'doctor'],
            'EDUCATION': ['school', 'college', 'university', 'education', 'course', 'training'],
            'AUTOMOTIVE': ['car', 'auto', 'vehicle', 'tire', 'service', 'workshop'],
        }
        
        for category, keywords in categories.items():
            if any(keyword in text_lower for keyword in keywords):
                return category
        
        return 'OTHER'
    
    def extract_city_from_offer(self, text: str) -> str:
        """Extract city from offer text"""
        pakistani_cities = [
            'karachi', 'lahore', 'islamabad', 'rawalpindi', 'faisalabad',
            'multan', 'hyderabad', 'peshawar', 'quetta', 'gujranwala',
            'sialkot', 'bahawalpur', 'sargodha', 'sukkur', 'larkana',
            'sheikhupura', 'mirpur', 'rahim yar khan', 'kasur', 'gujrat'
        ]
        
        text_lower = text.lower()
        for city in pakistani_cities:
            if city in text_lower:
                return city.upper()
        
        return 'ALL_PAKISTAN'
    
    def scrape_all_banks(self) -> Dict[str, List[Dict]]:
        """Scrape all Pakistani banks"""
        all_offers = {}
        
        scrapers = {
            'HBL': self.scrape_hbl_offers,
            'UBL': self.scrape_ubl_offers,
            'MCB': self.scrape_mcb_offers,
            'Bank Alfalah': self.scrape_bank_alfalah_offers,
            'Meezan Bank': self.scrape_meezan_bank_offers,
            'Standard Chartered': self.scrape_standard_chartered_offers,
        }
        
        for bank_name, scraper in scrapers.items():
            try:
                logger.info(f"Scraping offers from {bank_name}...")
                offers = scraper()
                all_offers[bank_name] = offers
                logger.info(f"Found {len(offers)} offers from {bank_name}")
                
                # Be respectful to servers
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error scraping {bank_name}: {str(e)}")
                all_offers[bank_name] = []
                continue
        
        return all_offers
    
    def save_to_database(self, bank_name: str, offers: List[Dict]):
        """Save scraped offers to database"""
        from offers.models import Offer, Merchant, Bank as BankModel
        from cards.models import CreditCard
        
        try:
            bank = BankModel.objects.filter(name__icontains=bank_name).first()
            if not bank:
                logger.warning(f"Bank {bank_name} not found in database")
                return
            
            for offer_data in offers:
                # Create or get merchant
                merchant_name = self.extract_merchant_name(offer_data['title'])
                merchant, _ = Merchant.objects.get_or_create(
                    name=merchant_name,
                    defaults={
                        'merchant_type': offer_data.get('category', 'OTHER'),
                        'city': self.extract_city_from_offer(offer_data['title']),
                        'is_active': True,
                    }
                )
                
                # Create offer
                Offer.objects.update_or_create(
                    title=offer_data['title'][:255],
                    bank=bank,
                    merchant=merchant,
                    defaults={
                        'description': offer_data.get('description', ''),
                        'offer_type': offer_data.get('offer_type', 'OTHER'),
                        'discount_percentage': self.extract_discount_percentage(offer_data['title']),
                        'valid_from': offer_data.get('valid_from'),
                        'valid_to': offer_data.get('valid_to'),
                        'terms_conditions': offer_data.get('terms_conditions', ''),
                        'scraping_source': offer_data.get('source_url', ''),
                        'is_active': True,
                    }
                )
                
        except Exception as e:
            logger.error(f"Error saving offers to database: {str(e)}")
    
    def extract_merchant_name(self, text: str) -> str:
        """Extract merchant name from offer text"""
        # Common Pakistani merchants
        merchants = [
            'Foodpanda', 'Daraz', 'Careem', 'Uber', 'KFC', 'McDonald\'s',
            'Pizza Hut', 'Domino\'s', 'Hardee\'s', 'Subway', 'Gloria Jeans',
            'Metro', 'Hyperstar', 'Naheed', 'Chase Up', 'Shell', 'PSO',
            'Total', 'Caltex', 'Emirates', 'PIA', 'Air Blue', 'Serena',
            'Pearl Continental', 'Nishat', 'ChenOne', 'J.', 'Alkaram',
            'Gul Ahmed', 'Sapphire', 'Khaadi', 'Service',
        ]
        
        for merchant in merchants:
            if merchant.lower() in text.lower():
                return merchant
        
        # Extract from patterns like "at [Merchant]" or "with [Merchant]"
        patterns = [
            r'at\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'with\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'from\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return 'Various Merchants'
    
    def extract_discount_percentage(self, text: str) -> Optional[float]:
        """Extract discount percentage from text"""
        patterns = [
            r'(\d+)%\s+off',
            r'(\d+)%\s+discount',
            r'save\s+(\d+)%',
            r'(\d+)%\s+cashback',
            r'upto\s+(\d+)%',
            r'up\s+to\s+(\d+)%',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue
        
        return None