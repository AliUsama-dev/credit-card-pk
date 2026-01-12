import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
import time
from django.utils import timezone

class PakistanBankScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        self.session = requests.Session()
    
    def scrape_hbl_offers(self) -> List[Dict]:
        """Scrape HBL offers from their website"""
        offers = []
        try:
            # HBL credit card offers page
            url = "https://www.hbl.com/credit-cards/offers"
            response = self.session.get(url, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find offer cards (adjust selectors based on actual HTML structure)
                offer_cards = soup.select('.offer-card, .promotion-item, .deal-box')
                
                for card in offer_cards:
                    try:
                        title = card.select_one('.title, h3, .offer-title')
                        description = card.select_one('.description, p, .offer-desc')
                        validity = card.select_one('.validity, .date-range, .expiry')
                        
                        if title and description:
                            offer = {
                                'title': title.text.strip(),
                                'description': description.text.strip(),
                                'bank': 'HBL',
                                'validity': self.parse_validity(validity.text if validity else ''),
                                'offer_type': self.detect_offer_type(title.text + description.text),
                                'category': self.categorize_offer(title.text),
                                'source_url': url,
                                'scraped_at': timezone.now()
                            }
                            offers.append(offer)
                    except Exception as e:
                        print(f"Error parsing HBL offer: {e}")
                        continue
        except Exception as e:
            print(f"Error scraping HBL: {e}")
        
        return offers
    
    def scrape_ubl_offers(self) -> List[Dict]:
        """Scrape UBL offers"""
        offers = []
        try:
            url = "https://www.ubldigital.com/offers"
            response = self.session.get(url, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for offer elements
                offer_sections = soup.select('.offer-container, .promo-section, .deals-grid')
                
                for section in offer_sections:
                    # Extract offers based on common patterns
                    titles = section.select('h2, h3, h4')
                    descriptions = section.select('p, .desc, .details')
                    
                    for title, desc in zip(titles, descriptions):
                        offer = {
                            'title': title.text.strip(),
                            'description': desc.text.strip()[:500],
                            'bank': 'UBL',
                            'validity': self.extract_validity_from_text(desc.text),
                            'offer_type': self.detect_offer_type(title.text),
                            'category': self.categorize_offer(title.text),
                            'source_url': url,
                            'scraped_at': timezone.now()
                        }
                        offers.append(offer)
        except Exception as e:
            print(f"Error scraping UBL: {e}")
        
        return offers
    
    def scrape_bank_alfalah_offers(self) -> List[Dict]:
        """Scrape Bank Alfalah offers"""
        offers = []
        try:
            # Bank Alfalah credit card offers page
            url = "https://www.bankalfalah.com/credit-cards/offers-promotions/"
            response = self.session.get(url, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Parse offers - adjust selectors based on actual page structure
                offer_items = soup.select('.offer-item, .promotion-card, .deal-item')
                
                for item in offer_items:
                    title = item.select_one('.offer-title, h3, .title')
                    desc = item.select_one('.offer-desc, .description, p')
                    dates = item.select_one('.valid-dates, .expiry-date, .duration')
                    
                    if title:
                        offer = {
                            'title': title.text.strip(),
                            'description': desc.text.strip()[:500] if desc else '',
                            'bank': 'Bank Alfalah',
                            'validity': self.parse_date_range(dates.text if dates else ''),
                            'offer_type': 'DISCOUNT',
                            'category': self.categorize_offer(title.text),
                            'source_url': url,
                            'scraped_at': timezone.now()
                        }
                        offers.append(offer)
        except Exception as e:
            print(f"Error scraping Bank Alfalah: {e}")
        
        return offers
    
    def scrape_meezan_bank_offers(self) -> List[Dict]:
        """Scrape Meezan Bank offers"""
        offers = []
        try:
            url = "https://www.meezanbank.com/credit-card-offers/"
            response = self.session.get(url, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for Islamic banking offers
                islamic_offers = soup.select('.islamic-offer, .sharia-compliant-offer, .offer-box')
                
                for offer_div in islamic_offers:
                    title = offer_div.select_one('h3, h4, .offer-heading')
                    details = offer_div.select_one('.offer-details, .description, p')
                    
                    if title:
                        offer = {
                            'title': title.text.strip(),
                            'description': details.text.strip()[:500] if details else '',
                            'bank': 'Meezan Bank',
                            'validity': self.get_default_validity(),
                            'offer_type': 'CASHBACK',
                            'category': 'ISLAMIC_BANKING',
                            'source_url': url,
                            'scraped_at': timezone.now()
                        }
                        offers.append(offer)
        except Exception as e:
            print(f"Error scraping Meezan Bank: {e}")
        
        return offers
    
    def scrape_standard_chartered_offers(self) -> List[Dict]:
        """Scrape Standard Chartered Pakistan offers"""
        offers = []
        try:
            url = "https://www.sc.com/pk/credit-cards/offers/"
            response = self.session.get(url, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # SC typically has well-structured offer pages
                offers_grid = soup.select('.offers-grid, .cards-container, .promotions-list')
                
                for grid in offers_grid:
                    cards = grid.select('.card, .offer-card, .promo-item')
                    
                    for card in cards:
                        title = card.select_one('.card-title, h3, .title')
                        desc = card.select_one('.card-text, .description, p')
                        validity = card.select_one('.valid-until, .expiry, .date')
                        
                        if title:
                            offer = {
                                'title': title.text.strip(),
                                'description': desc.text.strip()[:500] if desc else '',
                                'bank': 'Standard Chartered',
                                'validity': self.parse_validity(validity.text if validity else ''),
                                'offer_type': 'DISCOUNT',
                                'category': self.categorize_offer(title.text),
                                'source_url': url,
                                'scraped_at': timezone.now()
                            }
                            offers.append(offer)
        except Exception as e:
            print(f"Error scraping Standard Chartered: {e}")
        
        return offers
    
    def parse_validity(self, text: str) -> Dict:
        """Parse validity dates from text"""
        # Extract dates using regex patterns
        date_patterns = [
            r'(\d{1,2})\s*(?:st|nd|rd|th)?\s*(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*\d{4}',
            r'\d{1,2}/\d{1,2}/\d{4}',
            r'\d{4}-\d{2}-\d{2}',
        ]
        
        dates = []
        for pattern in date_patterns:
            dates.extend(re.findall(pattern, text, re.IGNORECASE))
        
        if len(dates) >= 2:
            return {'from': dates[0], 'to': dates[1]}
        elif len(dates) == 1:
            return {'from': datetime.now().strftime('%Y-%m-%d'), 'to': dates[0]}
        
        # Default: 30 days from now
        default_from = datetime.now()
        default_to = default_from + timedelta(days=30)
        return {'from': default_from.strftime('%Y-%m-%d'), 'to': default_to.strftime('%Y-%m-%d')}
    
    def detect_offer_type(self, text: str) -> str:
        """Detect offer type from text"""
        text = text.lower()
        if any(word in text for word in ['discount', '% off', 'off', 'reduction']):
            return 'DISCOUNT'
        elif any(word in text for word in ['cashback', 'cash back', 'cash-back']):
            return 'CASHBACK'
        elif any(word in text for word in ['emi', 'installment', 'easy payment']):
            return 'EMI'
        elif any(word in text for word in ['bonus', 'welcome', 'signup']):
            return 'WELCOME_BONUS'
        else:
            return 'REWARD_MULTIPLIER'
    
    def categorize_offer(self, text: str) -> str:
        """Categorize offer based on keywords"""
        text = text.lower()
        categories = {
            'DINING': ['restaurant', 'dining', 'cafe', 'food', 'eat', 'dine'],
            'TRAVEL': ['hotel', 'travel', 'flight', 'airline', 'holiday', 'vacation'],
            'SHOPPING': ['shopping', 'mall', 'store', 'retail', 'fashion'],
            'FUEL': ['fuel', 'petrol', 'gas', 'shell', 'caltex'],
            'GROCERIES': ['grocery', 'supermarket', 'hypermarket', 'foodpanda'],
            'ENTERTAINMENT': ['movie', 'cinema', 'entertainment', 'netflix'],
        }
        
        for category, keywords in categories.items():
            if any(keyword in text for keyword in keywords):
                return category
        
        return 'OTHER'
    
    def get_default_validity(self) -> Dict:
        """Get default validity period"""
        from_date = datetime.now()
        to_date = from_date + timedelta(days=90)
        return {
            'from': from_date.strftime('%Y-%m-%d'),
            'to': to_date.strftime('%Y-%m-%d')
        }
    
    def scrape_all_banks(self) -> List[Dict]:
        """Scrape offers from all Pakistani banks"""
        all_offers = []
        
        # Scrape each bank
        scrapers = [
            self.scrape_hbl_offers,
            self.scrape_ubl_offers,
            self.scrape_bank_alfalah_offers,
            self.scrape_meezan_bank_offers,
            self.scrape_standard_chartered_offers,
        ]
        
        for scraper in scrapers:
            try:
                offers = scraper()
                all_offers.extend(offers)
                time.sleep(2)  # Be respectful to servers
            except Exception as e:
                print(f"Error in scraper {scraper.__name__}: {e}")
                continue
        
        return all_offers