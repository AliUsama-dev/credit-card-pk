# scraping/scrapers/verified_bank_scraper.py
import asyncio
import json
import re
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urljoin, urlparse

from playwright.async_api import async_playwright, Browser, Page, Response
from bs4 import BeautifulSoup
import requests
from django.utils import timezone
from django.db import transaction
import aiohttp
import urllib3

logger = logging.getLogger(__name__)

class ProfessionalBankScraper:
    """Professional scraper for Pakistani bank offers with advanced features"""
    
    def __init__(self, use_browser: bool = True, context: Optional[Dict] = None):
        self.use_browser = use_browser
        self.context = context or {}
        self.playwright = None
        self.browser = None
        self.browser_context = None
        
        # Load verified URLs
        base_dir = Path(__file__).parent.parent.parent
        urls_file = base_dir / 'data' / 'verified_bank_urls.json'
        
        with open(urls_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.banks = {bank['code']: bank for bank in data['banks']}
        
        # Setup for debugging
        self.dump_dir = base_dir / 'data' / 'scraping_dumps'
        self.dump_dir.mkdir(parents=True, exist_ok=True)
        
        # User agent rotation
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]
    
    async def setup_browser(self):
        """Setup Playwright browser if not already setup"""
        if not self.use_browser:
            return
        
        try:
            if not self.playwright:
                self.playwright = await async_playwright().start()
            
            if not self.browser:
                self.browser = await self.playwright.chromium.launch(
                    headless=True,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage',
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-web-security',
                        '--disable-features=IsolateOrigins,site-per-process',
                    ]
                )
            
            if not self.browser_context:
                self.browser_context = await self.browser.new_context(
                    user_agent=self.user_agents[0],
                    viewport={'width': 1920, 'height': 1080},
                    java_script_enabled=True,
                    ignore_https_errors=True,
                )
            
            logger.info("Browser setup completed successfully")
            
        except Exception as e:
            logger.error(f"Failed to setup browser: {str(e)}")
            self.use_browser = False
    
    async def cleanup(self):
        """Cleanup resources"""
        try:
            if self.browser_context:
                await self.browser_context.close()
                self.browser_context = None
            
            if self.browser:
                await self.browser.close()
                self.browser = None
            
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
                
            logger.info("Browser cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
    
    def _get_city_mapping(self, city_code: str) -> Tuple[str, str]:
        """Get city name and code mapping"""
        city_mapping = {
            'KARACHI': ('Karachi', 'KHI'),
            'LAHORE': ('Lahore', 'LHR'),
            'ISLAMABAD': ('Islamabad', 'ISB'),
            'RAWALPINDI': ('Rawalpindi', 'RWP'),
            'FAISALABAD': ('Faisalabad', 'FSD'),
            'MULTAN': ('Multan', 'MUX'),
            'HYDERABAD': ('Hyderabad', 'HYD'),
            'PESHAWAR': ('Peshawar', 'PEW'),
            'QUETTA': ('Quetta', 'UET'),
            'GUJRANWALA': ('Gujranwala', 'GJR'),
            'SIALKOT': ('Sialkot', 'SKT'),
            'BAHAWALPUR': ('Bahawalpur', 'BWP'),
            'SARGODHA': ('Sargodha', 'SGD'),
            'SUKKUR': ('Sukkur', 'SKR'),
            'LARKANA': ('Larkana', 'LRK'),
            'ALL_PAKISTAN': ('All Pakistan', 'ALL')
        }
        
        city_code = city_code.upper().replace(' ', '_')
        return city_mapping.get(city_code, ('Karachi', 'KHI'))
    
    async def scrape_bank_with_filters(self, bank_code: str, filters: Dict[str, Any]) -> List[Dict]:
        """Scrape bank offers with filters"""
        try:
            await self.setup_browser()
        except Exception as e:
            logger.error(f"Failed to setup browser for {bank_code}: {str(e)}")
            self.use_browser = False
        
        city_code = filters.get('city', 'ALL_PAKISTAN')
        merchant_type = filters.get('merchant_type')
        search_term = filters.get('search', '')
        
        # Get city info
        city_name, city_short = self._get_city_mapping(city_code)
        
        if bank_code not in self.banks:
            logger.error(f"Bank {bank_code} not found")
            return []
        
        bank = self.banks[bank_code]
        all_offers = []
        
        logger.info(f"Scraping {bank['name']} with filters: city={city_name}, merchant_type={merchant_type}")
        
        for url in bank['offer_urls']:
            try:
                # Special handling for Meezan Peekaboo
                if bank_code == 'MEZAN' and 'card-discounts' in url:
                    offers = await self._scrape_meezan_peekaboo_with_filters(
                        url, bank, city_name, merchant_type, search_term
                    )
                else:
                    offers = await self._scrape_generic_bank_with_filters(
                        url, bank, city_name, merchant_type, search_term
                    )
                
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
            
            # Filter by city if specified and not "ALL_PAKISTAN"
            if city_code != 'ALL_PAKISTAN':
                offer_city = offer.get('city', '').upper().replace(' ', '_')
                if offer_city != city_code and not any(
                    city_code in tag for tag in [offer.get('title', ''), offer.get('description', '')]
                ):
                    # Check if offer is for specific city or all Pakistan
                    if 'ALL_PAKISTAN' not in offer.get('city', '') and 'NATIONWIDE' not in offer.get('city', ''):
                        continue
            
            filtered_offers.append(offer)
        
        # Remove duplicates
        unique_offers = []
        seen_titles = set()
        
        for offer in filtered_offers:
            title_key = offer.get('title', '').lower().strip()[:100]
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_offers.append(offer)
        
        return unique_offers
    
    async def _scrape_meezan_peekaboo_with_filters(self, url: str, bank: Dict, city_name: str, 
                                                  merchant_type: Optional[str], search_term: str) -> List[Dict]:
        """Scrape Meezan Peekaboo with filters"""
        if not self.browser_context:
            logger.error("Browser context not initialized for Meezan scraping")
            return []
        
        offers = []
        
        try:
            # Create new page for each scrape
            page = await self.browser_context.new_page()
            
            # Set longer timeout for Meezan
            page.set_default_timeout(120000)
            
            # Block unnecessary resources to speed up
            await page.route("**/*.{png,jpg,jpeg,gif,svg,ico,webp}", lambda route: route.abort())
            await page.route("**/*.{css,woff,woff2,eot,ttf,otf}", lambda route: route.abort())
            
            logger.info(f"Navigating to Meezan URL: {url}")
            
            # Navigate to URL
            try:
                response = await page.goto(url, wait_until='domcontentloaded', timeout=90000)
                if response and response.status != 200:
                    logger.warning(f"HTTP {response.status} for {url}")
                    await page.close()
                    return []
            except Exception as e:
                logger.error(f"Navigation error for {url}: {str(e)}")
                await page.close()
                return []
            
            # Wait for page to load
            await page.wait_for_timeout(5000)
            
            # Try to find Peekaboo iframe
            frame = None
            try:
                # Wait for iframe to appear
                await page.wait_for_selector('iframe', timeout=30000)
                iframes = await page.query_selector_all('iframe')
                
                for iframe in iframes:
                    src = await iframe.get_attribute('src') or ''
                    if 'peekaboo' in src or 'guru' in src:
                        frame = await iframe.content_frame()
                        logger.info("Found Peekaboo iframe")
                        break
            except Exception as e:
                logger.warning(f"Could not find Peekaboo iframe: {str(e)}")
            
            if not frame:
                # Try direct scraping without iframe
                logger.info("Trying direct scraping for Meezan")
                offers = await self._scrape_meezan_direct(page, bank, city_name)
                await page.close()
                return offers
            
            # Select city in Peekaboo
            await self._select_peekaboo_city(frame, city_name)
            
            # Wait for offers to load
            await frame.wait_for_timeout(5000)
            
            # Try to load more offers
            await self._load_more_peekaboo_offers(frame)
            
            # Extract offers
            offers = await self._extract_peekaboo_offers(frame, bank, city_name)
            
            # Save screenshot for debugging
            try:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                screenshot_path = self.dump_dir / f"meezan_{timestamp}.png"
                await page.screenshot(path=str(screenshot_path), full_page=False)
                logger.info(f"Screenshot saved: {screenshot_path}")
            except Exception as e:
                logger.debug(f"Could not save screenshot: {str(e)}")
            
            await page.close()
            
        except Exception as e:
            logger.error(f"Error scraping Meezan Peekaboo: {str(e)}")
            try:
                await page.close()
            except:
                pass
        
        return offers
    
    async def _scrape_meezan_direct(self, page: Page, bank: Dict, city_name: str) -> List[Dict]:
        """Try direct scraping for Meezan without iframe"""
        offers = []
        
        try:
            # Get all text content
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Look for offer elements
            offer_selectors = [
                '.offer-card', '.discount-card', '.card', '.deal',
                '[class*="offer"]', '[class*="discount"]', '[class*="deal"]'
            ]
            
            all_elements = []
            for selector in offer_selectors:
                elements = soup.select(selector)
                if elements:
                    all_elements.extend(elements)
            
            logger.info(f"Found {len(all_elements)} potential offer elements")
            
            for element in all_elements[:50]:  # Limit to 50 elements
                try:
                    text = element.get_text(' ', strip=True)
                    if len(text) < 20:
                        continue
                    
                    # Extract title
                    title = ''
                    title_elements = element.find_all(['h3', 'h4', 'h5', 'strong', 'b'])
                    if title_elements:
                        title = title_elements[0].get_text(strip=True)
                    
                    if not title:
                        # Try to extract title from first line
                        lines = text.split('.')
                        if lines:
                            title = lines[0].strip()[:200]
                    
                    if not title:
                        continue
                    
                    # Extract merchant
                    merchant = self._extract_merchant(text, title)
                    
                    # Extract discount
                    discount = self._extract_discount(text)
                    
                    offer = {
                        'title': title[:200],
                        'description': text[:500],
                        'bank_code': bank['code'],
                        'bank_name': bank['name'],
                        'valid_from': timezone.now().date(),
                        'valid_to': (timezone.now() + timedelta(days=90)).date(),
                        'offer_type': 'DISCOUNT',
                        'category': self._categorize_offer(text),
                        'discount_percentage': discount,
                        'merchant': merchant[:100],
                        'city': city_name.upper().replace(' ', '_'),
                        'source_url': bank['offer_urls'][0],
                        'scraped_at': timezone.now(),
                        'is_active': True,
                        'terms_conditions': f"Valid for {bank['name']} cardholders in {city_name}. Terms apply.",
                    }
                    
                    offers.append(offer)
                    
                except Exception as e:
                    logger.debug(f"Error processing Meezan element: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error in direct Meezan scraping: {str(e)}")
        
        return offers
    
    async def _select_peekaboo_city(self, frame, city_name: str):
        """Select city in Peekaboo interface"""
        try:
            # Try multiple approaches to select city
            city_selectors = [
                f'text="{city_name}"',
                f'text/i="{city_name}"',
                f'button:has-text("{city_name}")',
                f'[aria-label*="{city_name}"]',
                '.city-selector',
                '.location-selector',
                '[class*="city"]',
                '[class*="location"]'
            ]
            
            selected = False
            
            for selector in city_selectors:
                try:
                    elements = await frame.query_selector_all(selector)
                    if elements:
                        for element in elements:
                            try:
                                text = await element.text_content()
                                if city_name.lower() in text.lower():
                                    await element.click(timeout=5000)
                                    await frame.wait_for_timeout(3000)
                                    logger.info(f"Selected city: {city_name} using selector: {selector}")
                                    selected = True
                                    break
                            except:
                                continue
                    if selected:
                        break
                except:
                    continue
            
            if not selected:
                logger.warning(f"Could not select city {city_name}, using default")
                
        except Exception as e:
            logger.error(f"Error selecting city: {str(e)}")
    
    async def _load_more_peekaboo_offers(self, frame, max_clicks: int = 5):
        """Click 'Load More' or similar buttons"""
        for attempt in range(max_clicks):
            try:
                load_more_selectors = [
                    'button:has-text("Load More")',
                    'button:has-text("Show More")',
                    'button:has-text("View More")',
                    '.load-more',
                    '.see-more',
                    '[class*="load"]',
                    '[class*="more"]'
                ]
                
                clicked = False
                for selector in load_more_selectors:
                    try:
                        button = await frame.query_selector(selector)
                        if button and await button.is_visible():
                            await button.scroll_into_view_if_needed()
                            await button.click(timeout=3000)
                            await frame.wait_for_timeout(2000)
                            clicked = True
                            logger.info(f"Clicked 'Load More' button (attempt {attempt + 1})")
                            break
                    except:
                        continue
                
                if not clicked:
                    break
                    
            except Exception as e:
                logger.debug(f"Error loading more offers: {str(e)}")
                break
    
    async def _extract_peekaboo_offers(self, frame, bank: Dict, city_name: str) -> List[Dict]:
        """Extract offers from Peekaboo interface"""
        offers = []
        
        try:
            # Try multiple selectors for offer cards
            card_selectors = [
                '.card',
                '.offer-card',
                '.discount-card',
                '[class*="card"]',
                'a[href*="offer"]',
                'a[href*="discount"]',
                '[class*="offer"]',
                '[class*="discount"]'
            ]
            
            all_cards = []
            for selector in card_selectors:
                try:
                    cards = await frame.query_selector_all(selector)
                    if cards:
                        all_cards.extend(cards)
                except:
                    continue
            
            logger.info(f"Found {len(all_cards)} offer cards in Peekaboo")
            
            for i, card in enumerate(all_cards[:100]):  # Limit to 100 cards
                try:
                    # Get card text
                    card_text = await card.text_content()
                    if not card_text or len(card_text.strip()) < 10:
                        continue
                    
                    # Try to get more details
                    offer_data = await self._extract_peekaboo_card_data(card, bank, city_name, card_text)
                    if offer_data:
                        offers.append(offer_data)
                        
                except Exception as e:
                    logger.debug(f"Error extracting card {i}: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error extracting Peekaboo offers: {str(e)}")
        
        return offers
    
    async def _extract_peekaboo_card_data(self, card, bank: Dict, city_name: str, card_text: str) -> Optional[Dict]:
        """Extract data from a single Peekaboo card"""
        try:
            # Clean card text
            card_text = card_text.strip()
            
            # Extract title (first line or meaningful text)
            title = ''
            lines = [line.strip() for line in card_text.split('\n') if line.strip()]
            if lines:
                title = lines[0][:200]
            
            if not title:
                return None
            
            # Extract merchant from title or text
            merchant = ''
            if ' at ' in title.lower():
                merchant = title.split(' at ')[-1].strip()
            elif ' with ' in title.lower():
                merchant = title.split(' with ')[-1].strip()
            else:
                merchant = self._extract_merchant(card_text, title)
            
            # Extract discount
            discount = self._extract_discount(card_text)
            
            # Get description
            description = ''
            if len(lines) > 1:
                description = ' '.join(lines[1:3])[:300]
            else:
                description = f"{bank['name']} card offer at {merchant} in {city_name}"
            
            # Get URL if available
            url = ''
            try:
                href = await card.get_attribute('href')
                if href:
                    url = href if href.startswith('http') else f"https://www.meezanbank.com{href}"
            except:
                pass
            
            offer = {
                'title': title[:200],
                'description': description[:500],
                'bank_code': bank['code'],
                'bank_name': bank['name'],
                'valid_from': timezone.now().date(),
                'valid_to': (timezone.now() + timedelta(days=90)).date(),
                'offer_type': 'DISCOUNT',
                'category': self._categorize_offer(card_text),
                'discount_percentage': discount,
                'merchant': merchant[:100] or "Various Merchants",
                'city': city_name.upper().replace(' ', '_'),
                'source_url': url or bank['offer_urls'][0],
                'scraped_at': timezone.now(),
                'is_active': True,
                'terms_conditions': f"Valid for {bank['name']} cardholders in {city_name}. Terms apply.",
            }
            
            return offer
            
        except Exception as e:
            logger.debug(f"Error extracting card: {str(e)}")
            return None
    
    async def _scrape_generic_bank_with_filters(self, url: str, bank: Dict, city_name: str,
                                               merchant_type: Optional[str], search_term: str) -> List[Dict]:
        """Scrape generic bank websites with filters"""
        offers = []
        
        try:
            # Try browser first
            if self.use_browser and self.browser_context:
                html = await self._fetch_with_browser(url)
            else:
                html = await self._fetch_with_http(url)
            
            if not html:
                return []
            
            # Parse HTML
            soup = BeautifulSoup(html, 'html.parser')
            
            # Save HTML for debugging
            self._save_html_dump(bank['code'], html)
            
            # Extract offers using multiple strategies
            extraction_strategies = [
                self._extract_with_selectors,
                self._extract_with_semantic_analysis,
                self._extract_with_pattern_matching,
            ]
            
            for strategy in extraction_strategies:
                try:
                    strategy_offers = strategy(soup, url, bank, city_name)
                    if strategy_offers:
                        offers.extend(strategy_offers)
                        logger.info(f"Found {len(strategy_offers)} offers using {strategy.__name__}")
                        break
                except Exception as e:
                    logger.debug(f"Strategy {strategy.__name__} failed: {str(e)}")
                    continue
            
            # If no offers found, try generic extraction
            if not offers:
                offers = self._extract_generic_offers(soup, url, bank, city_name)
            
        except Exception as e:
            logger.error(f"Error scraping {bank['name']}: {str(e)}")
        
        return offers
    
    async def _fetch_with_browser(self, url: str) -> Optional[str]:
        """Fetch URL using browser"""
        if not self.browser_context:
            logger.warning("Browser context not available, falling back to HTTP")
            return await self._fetch_with_http(url)
        
        page = None
        try:
            page = await self.browser_context.new_page()
            
            # Set timeout
            page.set_default_timeout(60000)
            
            # Block unnecessary resources
            await page.route("**/*.{png,jpg,jpeg,gif,svg,ico,webp}", lambda route: route.abort())
            await page.route("**/*.{css,woff,woff2,eot,ttf,otf}", lambda route: route.abort())
            
            # Navigate to URL
            logger.info(f"Fetching with browser: {url}")
            response = await page.goto(url, wait_until='domcontentloaded', timeout=60000)
            
            if response and response.status != 200:
                logger.warning(f"HTTP {response.status} for {url}")
                await page.close()
                return None
            
            # Wait for content
            await page.wait_for_timeout(3000)
            
            # Try to load more content
            await self._scroll_and_load(page)
            
            # Get HTML
            html = await page.content()
            
            await page.close()
            return html
            
        except Exception as e:
            logger.error(f"Browser fetch error for {url}: {str(e)}")
            if page:
                try:
                    await page.close()
                except:
                    pass
            return None
    
    async def _fetch_with_http(self, url: str) -> Optional[str]:
        """Fetch URL using HTTP"""
        try:
            headers = {
                'User-Agent': self.user_agents[0],
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9,ur;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
            }
            
            response = requests.get(url, headers=headers, timeout=30, verify=False)
            response.raise_for_status()
            
            return response.text
            
        except Exception as e:
            logger.error(f"HTTP fetch error for {url}: {str(e)}")
            return None
    
    async def _scroll_and_load(self, page: Page):
        """Scroll page to load lazy content"""
        try:
            # Scroll to bottom
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(2000)
            
            # Scroll back up a bit
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
            await page.wait_for_timeout(1000)
            
            # Click any "Load More" buttons
            load_more_selectors = [
                'button:has-text("Load More")',
                'button:has-text("Show More")',
                'button:has-text("View More")',
                'a:has-text("Load More")',
                'a:has-text("Show More")',
            ]
            
            for selector in load_more_selectors:
                try:
                    button = await page.query_selector(selector)
                    if button:
                        await button.click(timeout=5000)
                        await page.wait_for_timeout(3000)
                except:
                    continue
                    
        except Exception as e:
            logger.debug(f"Scroll and load error: {str(e)}")
    
    # Add the helper methods that were previously defined but missing
    def _extract_with_selectors(self, soup: BeautifulSoup, url: str, bank: Dict, city_name: str) -> List[Dict]:
        """Extract offers using CSS selectors"""
        offers = []
        selectors = bank.get('selectors', {})
        
        if not selectors:
            return offers
        
        # Try different section selectors
        sections = []
        section_selectors = selectors.get('offer_section', '.offer-container, .deals-section, .discounts-grid')
        for selector in section_selectors.split(', '):
            found = soup.select(selector)
            if found:
                sections.extend(found)
        
        # If no sections found, use body
        if not sections:
            sections = [soup]
        
        for section in sections:
            # Find offer items
            items = []
            item_selectors = selectors.get('offer_item', '.offer-card, .deal-item, .discount-card')
            for selector in item_selectors.split(', '):
                found = section.select(selector)
                if found:
                    items.extend(found)
            
            # Additional generic selectors
            if not items:
                generic_selectors = [
                    '.card', '.tile', '.item', '.offer', '.deal', '.discount',
                    '.promotion', '.privilege', '.benefit'
                ]
                for selector in generic_selectors:
                    found = section.select(selector)
                    if found:
                        items.extend(found)
            
            for item in items[:50]:  # Limit items
                try:
                    offer = self._extract_offer_from_element(item, bank, city_name, url)
                    if offer:
                        offers.append(offer)
                except:
                    continue
        
        return offers
    
    def _extract_offer_from_element(self, element, bank: Dict, city_name: str, base_url: str) -> Optional[Dict]:
        """Extract offer data from HTML element"""
        try:
            # Get text content
            text = element.get_text(' ', strip=True)
            if len(text) < 20:  # Too short to be a meaningful offer
                return None
            
            # Extract title
            title = ''
            title_elements = element.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'strong', 'b'])
            if title_elements:
                title = title_elements[0].get_text(strip=True)
            
            if not title:
                # Try to extract title from first line
                lines = text.split('.')
                if lines:
                    title = lines[0].strip()[:200]
            
            # Extract merchant
            merchant = self._extract_merchant(text, title)
            
            # Extract discount
            discount = self._extract_discount(text)
            
            # Extract dates
            valid_from, valid_to = self._extract_dates(text)
            
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
                'valid_from': valid_from,
                'valid_to': valid_to,
                'offer_type': offer_type,
                'category': category,
                'discount_percentage': discount,
                'merchant': merchant[:100],
                'city': city_name.upper().replace(' ', '_'),
                'source_url': link or base_url,
                'scraped_at': timezone.now(),
                'is_active': True,
                'min_spend': self._extract_min_spend(text),
                'max_discount': self._extract_max_discount(text, discount),
                'terms_conditions': f"Offer valid for {bank['name']} cardholders. Terms and conditions apply.",
            }
            
            return offer
            
        except Exception as e:
            logger.debug(f"Error extracting offer from element: {str(e)}")
            return None
    
    def _extract_merchant(self, text: str, title: str) -> str:
        """Extract merchant name from text"""
        # Common Pakistani merchants
        pakistani_merchants = [
            'Foodpanda', 'Daraz', 'Careem', 'Bykea', 'Uber',
            'KFC', 'McDonald\'s', 'Pizza Hut', 'Domino\'s', 'Hardee\'s',
            'Subway', 'Gloria Jeans', 'Cup & Cino', 'Java',
            'Metro', 'Hyperstar', 'Chase Up', 'Naheed', 'Imtiaz',
            'Shell', 'PSO', 'Total', 'Attock', 'Hascol',
            'Emirates', 'PIA', 'Air Blue', 'Serena', 'Pearl Continental',
            'Nishat', 'ChenOne', 'J.', 'Alkaram', 'Gul Ahmed',
            'Sapphire', 'Khaadi', 'Service', 'Bata', 'Borjan'
        ]
        
        text_lower = text.lower()
        for merchant in pakistani_merchants:
            if merchant.lower() in text_lower:
                return merchant
        
        # Try to extract from patterns
        patterns = [
            r'at\s+([A-Z][a-zA-Z\s&]+(?:Mall|Store|Shop|Restaurant|Hotel|Cafe))',
            r'with\s+([A-Z][a-zA-Z\s&]+)',
            r'from\s+([A-Z][a-zA-Z\s&]+)',
            r'on\s+([A-Z][a-zA-Z\s&]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                merchant = match.group(1).strip()
                if 2 < len(merchant) < 50:
                    return merchant
        
        # Use title if it contains merchant-like words
        if ' at ' in title:
            return title.split(' at ')[-1]
        
        return "Various Merchants"
    
    def _extract_discount(self, text: str) -> Optional[float]:
        """Extract discount percentage from text"""
        patterns = [
            r'(\d{1,3})%\s*(?:off|discount|save|cashback|back)',
            r'save\s*(\d{1,3})%',
            r'(\d{1,3})%\s*saving',
            r'upto\s*(\d{1,3})%',
            r'up to\s*(\d{1,3})%',
            r'get\s*(\d{1,3})%',
            r'(\d{1,3})%\s*(?:reduction|less)',
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
    
    def _extract_dates(self, text: str) -> Tuple[datetime.date, datetime.date]:
        """Extract dates from text"""
        today = timezone.now().date()
        valid_from = today
        
        # Common date patterns
        date_patterns = [
            r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})',
            r'(\d{1,2})\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{4})',
            r'until\s+(\d{1,2})[-/](\d{1,2})[-/](\d{4})',
            r'till\s+(\d{1,2})[-/](\d{1,2})[-/](\d{4})',
            r'valid\s+until\s+(\d{1,2})[-/](\d{1,2})[-/](\d{4})',
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    if len(matches[0]) == 3:
                        day, month, year = matches[0]
                        valid_to = datetime(int(year), int(month), int(day)).date()
                        if valid_to > today:
                            return valid_from, valid_to
                except:
                    continue
        
        # Default: 30 days from now
        valid_to = today + timedelta(days=30)
        return valid_from, valid_to
    
    def _determine_offer_type(self, text: str) -> str:
        """Determine offer type from text"""
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
        elif any(word in text_lower for word in ['fee waiver', 'no fee', 'free', 'waiver']):
            return 'FEE_WAIVER'
        else:
            return 'OTHER'
    
    def _categorize_offer(self, text: str) -> str:
        """Categorize offer based on text"""
        text_lower = text.lower()
        
        categories = {
            'DINING': ['restaurant', 'dining', 'cafe', 'coffee', 'food', 'eat', 'dine', 
                      'pizza', 'burger', 'kfc', 'mcdonald', 'bbq', 'fast food', 'takeaway'],
            'TRAVEL': ['hotel', 'travel', 'flight', 'airline', 'holiday', 'vacation', 
                      'ticket', 'booking', 'emirates', 'pia', 'airblue', 'serena'],
            'SHOPPING': ['shopping', 'mall', 'store', 'retail', 'fashion', 'clothing', 
                        'apparel', 'daraz', 'al-karam', 'gul ahmed', 'khaadi'],
            'FUEL': ['fuel', 'petrol', 'gas', 'shell', 'caltex', 'total', 'pso', 
                    'hascol', 'attock', 'gas station'],
            'GROCERIES': ['grocery', 'supermarket', 'hypermarket', 'metro', 'naheed', 
                         'chaseup', 'imtiaz', 'hyperstar', 'alfatah'],
            'ELECTRONICS': ['electronics', 'mobile', 'phone', 'laptop', 'computer', 
                           'apple', 'samsung', 'huawei', 'oppo', 'vivo'],
            'ENTERTAINMENT': ['movie', 'cinema', 'entertainment', 'netflix', 'youtube', 
                             'spotify', 'game', 'cinplex', 'nova'],
            'HEALTHCARE': ['hospital', 'clinic', 'pharmacy', 'medical', 'health', 
                          'doctor', 'medicine', 'lab', 'test'],
            'EDUCATION': ['school', 'college', 'university', 'education', 'course', 
                         'training', 'tuition', 'academy'],
            'AUTOMOTIVE': ['car', 'auto', 'vehicle', 'tire', 'service', 'workshop', 
                          'suzuki', 'toyota', 'honda', 'mehran'],
        }
        
        for category, keywords in categories.items():
            if any(keyword in text_lower for keyword in keywords):
                return category
        
        return 'OTHER'
    
    def _extract_min_spend(self, text: str) -> Optional[float]:
        """Extract minimum spend from text"""
        patterns = [
            r'min(?:imum)?\s*spend\s*[:\-]?\s*Rs?\.?\s*(\d{1,10}(?:,\d{3})*(?:\.\d{2})?)',
            r'spend\s*Rs?\.?\s*(\d{1,10}(?:,\d{3})*(?:\.\d{2})?)\s*or\s*more',
            r'minimum\s*Rs?\.?\s*(\d{1,10}(?:,\d{3})*(?:\.\d{2})?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    amount_str = match.group(1).replace(',', '')
                    return float(amount_str)
                except:
                    continue
        
        return None
    
    def _extract_max_discount(self, text: str, discount_percentage: Optional[float]) -> Optional[float]:
        """Extract maximum discount amount from text"""
        if not discount_percentage:
            return None
        
        patterns = [
            r'max(?:imum)?\s*discount\s*[:\-]?\s*Rs?\.?\s*(\d{1,10}(?:,\d{3})*(?:\.\d{2})?)',
            r'upto\s*Rs?\.?\s*(\d{1,10}(?:,\d{3})*(?:\.\d{2})?)',
            r'up to\s*Rs?\.?\s*(\d{1,10}(?:,\d{3})*(?:\.\d{2})?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    amount_str = match.group(1).replace(',', '')
                    return float(amount_str)
                except:
                    continue
        
        return None
    
    def _extract_with_semantic_analysis(self, soup: BeautifulSoup, url: str, bank: Dict, city_name: str) -> List[Dict]:
        """Extract offers using semantic analysis"""
        offers = []
        
        # Look for offer-like sections
        offer_keywords = ['offer', 'discount', 'deal', 'promotion', 'privilege', 'cashback', 'saving']
        
        # Check all text elements
        text_elements = soup.find_all(['p', 'div', 'span', 'li', 'td'])
        
        for element in text_elements:
            text = element.get_text(' ', strip=True)
            if len(text) < 50:  # Too short for meaningful offer
                continue
            
            # Check if text contains offer keywords
            text_lower = text.lower()
            if any(keyword in text_lower for keyword in offer_keywords):
                offer = self._extract_offer_from_element(element, bank, city_name, url)
                if offer:
                    offers.append(offer)
        
        return offers[:20]  # Limit results
    
    def _extract_with_pattern_matching(self, soup: BeautifulSoup, url: str, bank: Dict, city_name: str) -> List[Dict]:
        """Extract offers using pattern matching"""
        offers = []
        
        # Look for common patterns
        patterns = [
            # Card-like elements
            '.card:has(h3, h4)',
            '.tile:has(h3, h4)',
            '.item:has(h3, h4)',
            
            # Offer containers
            '[class*="offer"]:has(h3, h4)',
            '[class*="deal"]:has(h3, h4)',
            '[class*="discount"]:has(h3, h4)',
            '[class*="promo"]:has(h3, h4)',
            
            # List items with offers
            'li:has(h3, h4)',
            'li:has(strong)',
            
            # Table rows with offers
            'tr:has(td:contains("%"))',
            'tr:has(td:contains("discount"))',
        ]
        
        for pattern in patterns:
            try:
                elements = soup.select(pattern)
                for element in elements[:30]:
                    offer = self._extract_offer_from_element(element, bank, city_name, url)
                    if offer:
                        offers.append(offer)
            except:
                continue
        
        return offers
    
    def _extract_generic_offers(self, soup: BeautifulSoup, url: str, bank: Dict, city_name: str) -> List[Dict]:
        """Extract offers using generic methods"""
        offers = []
        
        # Get all text
        all_text = soup.get_text(' ', strip=True)
        
        # Split into paragraphs
        paragraphs = [p.strip() for p in all_text.split('\n') if len(p.strip()) > 100]
        
        for para in paragraphs[:20]:
            # Check if paragraph contains offer-like content
            para_lower = para.lower()
            if any(keyword in para_lower for keyword in ['discount', 'offer', 'deal', '%', 'save']):
                offer = {
                    'title': f"{bank['name']} Offer",
                    'description': para[:500],
                    'bank_code': bank['code'],
                    'bank_name': bank['name'],
                    'valid_from': timezone.now().date(),
                    'valid_to': (timezone.now() + timedelta(days=30)).date(),
                    'offer_type': self._determine_offer_type(para),
                    'category': self._categorize_offer(para),
                    'discount_percentage': self._extract_discount(para),
                    'merchant': self._extract_merchant(para, ''),
                    'city': city_name.upper().replace(' ', '_'),
                    'source_url': url,
                    'scraped_at': timezone.now(),
                    'is_active': True,
                }
                offers.append(offer)
        
        return offers
    
    def _matches_merchant_type(self, offer: Dict, merchant_type: str) -> bool:
        """Check if offer matches merchant type"""
        category = offer.get('category', '').upper()
        
        # Map categories to merchant types
        category_to_merchant = {
            'DINING': 'RESTAURANT',
            'TRAVEL': 'TRAVEL',
            'SHOPPING': 'RETAIL',
            'E_COMMERCE': 'E_COMMERCE',
            'GROCERIES': 'SUPERMARKET',
            'FUEL': 'FUEL_STATION',
            'ELECTRONICS': 'ELECTRONICS',
            'ENTERTAINMENT': 'ENTERTAINMENT',
            'HEALTHCARE': 'HEALTHCARE',
            'EDUCATION': 'EDUCATION',
            'AUTOMOTIVE': 'AUTOMOTIVE',
        }
        
        offer_merchant_type = category_to_merchant.get(category, 'OTHER')
        return offer_merchant_type == merchant_type.upper()
    
    def _save_html_dump(self, bank_code: str, html: str):
        """Save HTML for debugging"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            dump_file = self.dump_dir / f"{bank_code}_{timestamp}.html"
            with open(dump_file, 'w', encoding='utf-8') as f:
                f.write(html)
        except:
            pass
    
    async def scrape_all_banks_with_filters(self, filters: Dict[str, Any]) -> Dict[str, List[Dict]]:
        """Scrape all banks with filters"""
        results = {}
        
        try:
            await self.setup_browser()
        except Exception as e:
            logger.error(f"Failed to setup browser: {str(e)}")
            self.use_browser = False
        
        for bank_code in self.banks.keys():
            try:
                offers = await self.scrape_bank_with_filters(bank_code, filters)
                results[bank_code] = offers
                logger.info(f"Scraped {len(offers)} offers from {bank_code}")
                
                # Delay between banks
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error scraping {bank_code}: {str(e)}")
                results[bank_code] = []
        
        # Cleanup
        await self.cleanup()
        
        return results

# Synchronous wrapper for Celery
def scrape_banks_with_filters_sync(filters: Dict[str, Any]) -> Dict[str, List[Dict]]:
    """Synchronous wrapper for async scraper with filters"""
    scraper = ProfessionalBankScraper(use_browser=True)
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        return loop.run_until_complete(scraper.scrape_all_banks_with_filters(filters))
    except Exception as e:
        logger.error(f"Error in sync scraper: {str(e)}")
        return {}
    finally:
        loop.close()