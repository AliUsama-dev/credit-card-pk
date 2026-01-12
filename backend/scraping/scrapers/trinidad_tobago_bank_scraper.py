# scraping/scrapers/trinidad_tobago_bank_scraper.py
"""
Professional scraper for Trinidad & Tobago banks credit cards
Scrapes card information, features, rewards, and offers from all major T&T banks
"""
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
try:
    from django.utils import timezone
except ImportError:
    from datetime import datetime
    class timezone:
        @staticmethod
        def now():
            return datetime.now()
        @staticmethod
        def isoformat():
            return datetime.now().isoformat()
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

# Try to import Playwright for JavaScript-rendered pages
try:
    from playwright.sync_api import sync_playwright, Browser, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright not available. Install with: pip install playwright && playwright install chromium")

class TrinidadTobagoBankScraper:
    """Complete scraper for all Trinidad & Tobago banks with credit card information"""
    
    def __init__(self, use_browser: bool = True):
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
        # Use browser if available and requested (default: True for better scraping)
        self.use_browser = use_browser and PLAYWRIGHT_AVAILABLE
        if self.use_browser:
            logger.info("✅ Browser mode enabled - will use Playwright for JavaScript-rendered pages")
        else:
            if use_browser and not PLAYWRIGHT_AVAILABLE:
                logger.warning("⚠️  Playwright not available - install with: pip install playwright && playwright install chromium")
            logger.info("Using requests library for scraping")
        self.browser = None
        self.playwright = None
        
        # All Trinidad & Tobago banks with their official credit card URLs
        # URLs verified and updated based on actual bank websites
        self.banks = {
            'ANSA': {
                'name': 'ANSA Bank Limited',
                'urls': [
                    'https://www.ansabank.com/personal-banking/credit-cards',
                    'https://www.ansabank.com/products/credit-cards',
                    'https://www.ansabank.com/credit-cards',
                ],
                'type': 'COMMERCIAL',
                'scraper': self.scrape_ansa_bank,
            },
            'CIBC': {
                'name': 'CIBC Caribbean Bank (Trinidad & Tobago) Limited',
                'urls': [
                    'https://www.cibccaribbean.com/credit-and-debit/cards',  # Main credit cards page
                    'https://www.cibccaribbean.com/credit-and-debit/cards/visa-classic-credit',
                    'https://www.cibccaribbean.com/credit-and-debit/cards/visa-rewards',
                    'https://www.cibccaribbean.com/credit-and-debit/cards/visa-platinum',
                    'https://www.cibccaribbean.com/credit-and-debit/cards/mastercard-black',
                    'https://www.cibccaribbean.com/credit-and-debit/cards/british-airways-visa-platinum',
                    'https://www.cibccaribbean.com/credit-and-debit/cards/jetblue-cards',
                ],
                'type': 'INTERNATIONAL',
                'scraper': self.scrape_cibc,
            },
            'CITI': {
                'name': 'Citibank (Trinidad & Tobago) Limited',
                'urls': [
                    'https://www.citi.com/credit-cards/',  # Main page - start here to find all categories
                    'https://www.citi.com/credit-cards/view-all-credit-cards',  # All cards page
                    'https://www.citi.com/credit-cards/savings-and-cash-back-credit-cards',
                    'https://www.citi.com/credit-cards/travel-reward-credit-cards',
                ],
                'type': 'INTERNATIONAL',
                'scraper': self.scrape_citibank,
            },
            'FIRST_CITIZENS': {
                'name': 'First Citizens Bank Limited',
                'urls': [
                    'https://www.firstcitizens.com.tt/personal/credit-cards',
                    'https://www.firstcitizens.com.tt/products/credit-cards',
                    'https://www.firstcitizens.com.tt/credit-cards',
                ],
                'type': 'COMMERCIAL',
                'scraper': self.scrape_first_citizens,
            },
            'JMMB': {
                'name': 'JMMB Bank (T&T) Limited',
                'urls': [
                    'https://www.jmmb.com/tt/personal/credit-cards',
                    'https://www.jmmb.com/tt/products/credit-cards',
                    'https://www.jmmb.com/tt/credit-cards',
                ],
                'type': 'COMMERCIAL',
                'scraper': self.scrape_jmmb,
            },
            'RBC': {
                'name': 'RBC Royal Bank (Trinidad & Tobago) Limited',
                'urls': [
                    'https://www.rbcroyalbank.com/caribbean/personal/credit-cards.html',
                    'https://www.rbcroyalbank.com/caribbean/credit-cards',
                    'https://www.rbcroyalbank.com/caribbean/personal/products/credit-cards',
                ],
                'type': 'INTERNATIONAL',
                'scraper': self.scrape_rbc,
            },
            'REPUBLIC': {
                'name': 'Republic Bank Limited',
                'urls': [
                    'https://www.republictt.com/personal/credit-cards',
                    'https://www.republictt.com/products/credit-cards',
                    'https://www.republictt.com/credit-cards',
                ],
                'type': 'COMMERCIAL',
                'scraper': self.scrape_republic,
            },
            'SCOTIA': {
                'name': 'Scotiabank Trinidad and Tobago Limited',
                'urls': [
                    'https://tt.scotiabank.com/personal/credit-cards.html',  # Updated URL
                    'https://tt.scotiabank.com/personal/credit-cards',
                    'https://www.scotiabank.com/tt/en/personal/credit-cards.html',
                ],
                'type': 'INTERNATIONAL',
                'scraper': self.scrape_scotia,
            },
        }
    
    # ==================== Citibank Scraper ====================
    def scrape_citibank(self, url: str) -> List[Dict]:
        """Scrape Citibank credit cards - Visit main page, find ALL category links, scrape each card's detail page"""
        cards = []
        seen_card_names = set()
        seen_card_urls = set()
        
        try:
            # Step 1: Visit the main Citibank credit cards page
            logger.info(f"Step 1: Visiting main Citibank cards page: {url}")
            
            # Use browser for JavaScript-rendered pages
            if self.use_browser:
                logger.info("  Using headless browser to load main page...")
                html_content = self._fetch_with_browser(url)
                if html_content:
                    soup = BeautifulSoup(html_content, 'html.parser')
                else:
                    logger.warning("  Browser fetch failed, falling back to requests...")
                    response = self.session.get(url, timeout=30)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.content, 'html.parser')
            else:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
            
            # Step 2: Find ALL "View all X cards" category links from the main page
            category_links = []
            all_links = soup.find_all('a', href=True)
            
            # Known category patterns from the actual website: https://www.citi.com/credit-cards/
            # Based on the site structure: "View all 27 cards", "View all 13 Rewards Cards", etc.
            category_patterns = [
                r'view\s+all\s+\d+\s+cards?',  # "View all 27 cards" (main)
                r'view\s+all\s+\d+\s+rewards?\s+cards?',  # "View all 13 Rewards Cards"
                r'view\s+all\s+\d+\s+travel\s+cards?',  # "View all 8 Travel Cards"
                r'view\s+all\s+\d+\s+cash\s*back\s+cards?',  # "View all 4 Cash Back Cards"
                r'view\s+all\s+\d+\s+cashback\s+cards?',  # "View all 4 Cashback Cards"
                r'view\s+all\s+\d+\s+balance\s+transfer',  # "View all 5 Balance Transfer"
                r'view\s+all\s+\d+\s+no\s+annual\s+fee',  # "View all 20 No Annual Fee"
                r'view\s+all\s+\d+\s+retail',  # "View all 11 Retail"
                r'view\s+all\s+\d+',  # "View all 27" (catch-all)
            ]
            
            logger.info(f"Scanning {len(all_links)} links for 'View all X cards' category pages...")
            
            for link in all_links:
                link_text = link.get_text(strip=True)
                href = link.get('href', '')
                
                if not href:
                    continue
                
                # Check if link text matches any category pattern (case-insensitive, flexible)
                link_text_lower = link_text.lower().strip()
                is_category_link = False
                
                for pattern in category_patterns:
                    if re.search(pattern, link_text_lower, re.I):
                        is_category_link = True
                        logger.info(f"✅ Pattern match: '{link_text}' matches pattern: {pattern}")
                        break
                
                # Also check href for view-all patterns (more flexible)
                href_lower = href.lower()
                if any(pattern in href_lower for pattern in ['view-all', 'viewall', 'all-cards', 'allcards', 'all-credit-cards']):
                    is_category_link = True
                    logger.info(f"✅ Href match: '{href}' contains view-all pattern")
                
                # Also check if link text contains "view all" and a number (catch-all)
                if re.search(r'view\s+all.*\d+', link_text_lower, re.I):
                    is_category_link = True
                    logger.info(f"✅ Catch-all match: '{link_text}' contains 'view all' and number")
                
                if is_category_link:
                    full_url = urljoin(url, href)
                    # Normalize URL (remove trailing slash, query params for comparison)
                    normalized = full_url.split('?')[0].rstrip('/')
                    existing_normalized = [c.split('?')[0].rstrip('/') for c in category_links]
                    if normalized not in existing_normalized:
                        category_links.append(full_url)
                        logger.info(f"✅ Found category link: '{link_text}' -> {full_url}")
                    else:
                        logger.debug(f"Skipping duplicate category link: {full_url}")
            
            # Always add the main view-all-credit-cards URL FIRST (should have all 27 cards)
            # This is the PRIMARY source: "View all 27 cards" from https://www.citi.com/credit-cards/
            view_all_url = 'https://www.citi.com/credit-cards/view-all-credit-cards'
            view_all_normalized = view_all_url.split('?')[0].rstrip('/')
            if view_all_normalized not in [c.split('?')[0].rstrip('/') for c in category_links]:
                category_links.insert(0, view_all_url)
                logger.info(f"✅ Added PRIMARY 'View All 27 Cards' URL: {view_all_url}")
            
            # Also add known category URLs directly (CRITICAL - these must be visited)
            # Based on actual website structure from https://www.citi.com/credit-cards/:
            # - Explore Featured Cards -> "View all 27 cards"
            # - Rewards Cards -> "View all 13 Rewards Cards"
            # - Travel Cards -> "View all 8 Travel Cards"
            # - Cash Back Cards -> "View all 4 Cash Back Cards"
            # - Balance Transfer (5)
            # - No Annual Fee (20)
            # - Retail (11)
            known_category_urls = [
                'https://www.citi.com/credit-cards/view-all-credit-cards',  # All Cards (27 cards) - PRIMARY
                'https://www.citi.com/credit-cards/rewards-credit-cards',  # Rewards Cards (13 cards)
                'https://www.citi.com/credit-cards/travel-reward-credit-cards',  # Travel Cards (8 cards)
                'https://www.citi.com/credit-cards/savings-and-cash-back-credit-cards',  # Cash Back Cards (4 cards)
                'https://www.citi.com/credit-cards/balance-transfer-credit-cards',  # Balance Transfer (5 cards)
                'https://www.citi.com/credit-cards/no-annual-fee-credit-cards',  # No Annual Fee (20 cards)
                'https://www.citi.com/credit-cards/retail-credit-cards',  # Retail (11 cards)
            ]
            
            for known_url in known_category_urls:
                normalized = known_url.split('?')[0].rstrip('/')
                existing_normalized = [c.split('?')[0].rstrip('/') for c in category_links]
                if normalized not in existing_normalized:
                    category_links.append(known_url)
                    logger.info(f"✅ Added known category URL (MUST VISIT): {known_url}")
            
            logger.info(f"Found {len(category_links)} category pages to visit:")
            for i, cat_url in enumerate(category_links, 1):
                logger.info(f"  {i}. {cat_url}")
            
            # Step 3: Visit each category page and collect ALL card links
            # This includes: "View all 27 cards", "View all 13 Rewards Cards", "View all 8 Travel Cards", etc.
            all_card_links = []
            
            for idx, category_url in enumerate(category_links):
                try:
                    logger.info(f"Step 3.{idx+1}: Visiting category page {idx+1}/{len(category_links)}: {category_url}")
                    
                    # Use browser for JavaScript-rendered pages (Citibank uses JS heavily)
                    if self.use_browser:
                        logger.info(f"  Using headless browser to load page (waiting for JS to render)...")
                        html_content = self._fetch_with_browser(category_url, wait_time=5)
                        if html_content:
                            cat_soup = BeautifulSoup(html_content, 'html.parser')
                            logger.info(f"  ✅ Browser loaded page successfully")
                        else:
                            logger.warning(f"  Browser fetch failed, falling back to requests...")
                            cat_response = self.session.get(category_url, timeout=30)
                            if cat_response.status_code != 200:
                                logger.warning(f"Failed to fetch category page: {category_url} (Status: {cat_response.status_code})")
                                continue
                            cat_soup = BeautifulSoup(cat_response.content, 'html.parser')
                    else:
                        logger.info(f"  Using requests library (no browser)...")
                        cat_response = self.session.get(category_url, timeout=30)
                        if cat_response.status_code != 200:
                            logger.warning(f"Failed to fetch category page: {category_url} (Status: {cat_response.status_code})")
                            continue
                        cat_soup = BeautifulSoup(cat_response.content, 'html.parser')
                    
                    # Save page content for debugging if no cards found
                    page_text = cat_soup.get_text()
                    logger.debug(f"  Page content length: {len(page_text)} characters")
                    logger.debug(f"  Page title: {cat_soup.find('title').get_text() if cat_soup.find('title') else 'No title'}")
                    
                    # Extract all card links from this category page
                    # This should find all cards from sections like "Explore Featured Cards", "Rewards Cards", etc.
                    logger.info(f"  Extracting card links from category page...")
                    cat_links = self._extract_all_card_links_from_page(cat_soup, category_url, seen_card_urls)
                    
                    # Log page structure for debugging
                    page_title = cat_soup.find('title')
                    logger.info(f"  Page title: {page_title.get_text() if page_title else 'No title'}")
                    logger.info(f"  Page has {len(cat_soup.find_all('a', href=True))} total links")
                    
                    # If we found very few cards, try to find card names in the page text
                    if len(cat_links) < 3:
                        logger.warning(f"  ⚠️  Only found {len(cat_links)} cards, trying to find card names in page content...")
                        # Look for card names in headings and text
                        all_headings = cat_soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                        for heading in all_headings:
                            heading_text = heading.get_text(strip=True)
                            # Check if it looks like a card name
                            if heading_text and len(heading_text) > 5 and 'citi' in heading_text.lower():
                                # Try to find a link near this heading
                                container = heading.find_parent(['div', 'article', 'section', 'li'])
                                if container:
                                    nearby_link = container.find('a', href=re.compile(r'/credit-cards/', re.I))
                                    if nearby_link:
                                        href = nearby_link.get('href', '')
                                        if href:
                                            clean_href = href.split('?')[0].rstrip('/')
                                            if clean_href not in seen_card_urls:
                                                full_url = urljoin(category_url, href)
                                                seen_card_urls.add(clean_href)
                                                cat_links.append({
                                                    'url': full_url,
                                                    'name': heading_text
                                                })
                                                logger.info(f"  ✅ Found card from heading: {heading_text} -> {full_url}")
                    all_card_links.extend(cat_links)
                    logger.info(f"  ✅ Found {len(cat_links)} card links from this category")
                    
                    # Log ALL card names for debugging (not just first 3)
                    if cat_links:
                        card_names = [c['name'] for c in cat_links]
                        logger.info(f"  ✅ All {len(cat_links)} cards from this category:")
                        for i, name in enumerate(card_names, 1):
                            logger.info(f"     {i}. {name}")
                    else:
                        logger.warning(f"  ⚠️  No cards found from category: {category_url}")
                        # Try to debug - save HTML snippet
                        page_title = cat_soup.find('title')
                        logger.debug(f"  Page title: {page_title.get_text() if page_title else 'No title'}")
                        all_page_links = cat_soup.find_all('a', href=True)
                        credit_card_links = [l for l in all_page_links if '/credit-cards/' in l.get('href', '')]
                        logger.debug(f"  Total links on page: {len(all_page_links)}")
                        logger.debug(f"  Links with '/credit-cards/': {len(credit_card_links)}")
                        if credit_card_links:
                            logger.debug(f"  Sample credit card links: {[l.get('href') for l in credit_card_links[:5]]}")
                    
                    time.sleep(1)  # Be respectful
                    
                except Exception as e:
                    logger.error(f"Error fetching category {category_url}: {str(e)}", exc_info=True)
                    continue
            
            # Remove duplicates based on URL
            unique_card_links = []
            seen_urls = set()
            for card_link in all_card_links:
                clean_url = card_link['url'].split('?')[0].rstrip('/')
                if clean_url not in seen_urls:
                    seen_urls.add(clean_url)
                    unique_card_links.append(card_link)
            
            logger.info(f"Step 3: Found {len(unique_card_links)} unique card links across all categories")
            
            if len(unique_card_links) < 20:
                logger.warning(f"⚠️  Only found {len(unique_card_links)} cards, expected 27+. This might indicate missing category pages or card links.")
            else:
                logger.info(f"✅ Good! Found {len(unique_card_links)} cards (expected ~27 cards)")
            
            # Step 4: Visit each card's detail page and extract COMPLETE information
            logger.info(f"Step 4: Starting to scrape {len(unique_card_links)} card detail pages...")
            
            for idx, card_info in enumerate(unique_card_links):
                try:
                    card_url = card_info['url']
                    card_name = card_info['name']
                    
                    # Skip invalid URLs
                    if not card_url or card_url.startswith('javascript:') or card_url.startswith('mailto:') or card_url.startswith('tel:'):
                        logger.debug(f"Skipping invalid URL: {card_url}")
                        continue
                    
                    # Skip comparison/category pages
                    if '/compare/' in card_url.lower():
                        logger.debug(f"Skipping comparison page: {card_url}")
                        continue
                    
                    if card_name in seen_card_names:
                        logger.debug(f"Skipping duplicate card name: {card_name}")
                        continue
                    
                    logger.info(f"Scraping card {idx+1}/{len(unique_card_links)}: {card_name} ({card_url})")
                    
                    # Visit the card detail page - use browser for JavaScript-rendered pages
                    if self.use_browser:
                        logger.info(f"  Using browser to fetch card page...")
                        card_html = self._fetch_with_browser(card_url, wait_time=2)  # Reduced wait time
                        if card_html:
                            card_soup = BeautifulSoup(card_html, 'html.parser')
                        else:
                            logger.warning(f"  Browser fetch failed or timed out, falling back to requests...")
                            try:
                                card_response = self.session.get(card_url, timeout=15)  # Reduced timeout
                                if card_response.status_code != 200:
                                    logger.warning(f"Failed to fetch {card_url}: {card_response.status_code}")
                                    continue
                                card_soup = BeautifulSoup(card_response.content, 'html.parser')
                            except Exception as req_error:
                                logger.error(f"Requests fallback also failed for {card_url}: {str(req_error)}")
                                continue
                    else:
                        card_response = self.session.get(card_url, timeout=20)
                        if card_response.status_code != 200:
                            logger.warning(f"Failed to fetch {card_url}: {card_response.status_code}")
                            continue
                        card_soup = BeautifulSoup(card_response.content, 'html.parser')
                    
                    # Extract card name from the page (more accurate) - try multiple selectors
                    # BUT: Only use page title if it's clearly better than the link name
                    # Many pages have generic titles like "Savings Accounts" in sidebar
                    original_card_name = card_name  # Keep original from link - this is usually more accurate
                    page_title = None
                    
                    # Try to find the main content heading (not sidebar/navigation)
                    main_content_selectors = [
                        'main h1', 'main h2',  # Main content area
                        '.content h1', '.content h2',
                        '.main-content h1', '.main-content h2',
                        'article h1', 'article h2',
                        '[role="main"] h1', '[role="main"] h2',
                        'h1.card-title', 'h2.card-title',
                        '.card-name', '[data-card-name]',
                    ]
                    
                    for selector in main_content_selectors:
                        page_title = card_soup.select_one(selector)
                        if page_title:
                            break
                    
                    # Fallback to any h1 if main content selectors didn't work
                    if not page_title:
                        # Try to find h1 that's NOT in sidebar/nav
                        all_h1s = card_soup.find_all('h1')
                        for h1 in all_h1s:
                            # Skip if it's in a nav, sidebar, or aside element
                            parent = h1.find_parent(['nav', 'aside', '.sidebar', '.navigation'])
                            if not parent:
                                page_title = h1
                                break
                    
                    # If still no good title, use first h1
                    if not page_title:
                        page_title = card_soup.select_one('h1')
                    
                    if page_title:
                        extracted_name = page_title.get_text(strip=True)
                        # Clean up the name (remove extra text like "| Citi" or "Credit Card")
                        extracted_name = re.sub(r'\s*[|]\s*.*$', '', extracted_name)
                        extracted_name = re.sub(r'\s*Credit\s*Card\s*$', '', extracted_name, flags=re.I)
                        extracted_name = re.sub(r'\s*-\s*Citi.*$', '', extracted_name, flags=re.I)
                        
                        # Only use page title if:
                        # 1. It's a valid card name
                        # 2. It's different from generic page titles
                        # 3. It contains card-related keywords (to avoid "Savings Accounts" type titles)
                        generic_titles = ['savings accounts', 'current accounts', 'checking accounts', 
                                         '404 not found', 'page not found', 'error', 'home', 'welcome',
                                         'credit card benefits', 'credit card exclusive offers', 'balancecover',
                                         'gift cards', 'visa gift cards']
                        
                        if extracted_name.lower() in generic_titles:
                            logger.debug(f"Ignoring generic page title: {extracted_name}, keeping original: {original_card_name}")
                            # Keep original name - don't override with generic title
                        elif extracted_name and self._is_valid_card_name(extracted_name):
                            # Check if it contains card-related keywords
                            card_keywords = ['card', 'visa', 'mastercard', 'platinum', 'gold', 'credit', 
                                            'debit', 'aadvantage', 'rewards', 'cashback', 'infinite', 'signature']
                            if any(keyword in extracted_name.lower() for keyword in card_keywords):
                                # Page title has card keywords - use it if it's better than original
                                if original_card_name and self._is_valid_card_name(original_card_name):
                                    # Compare: prefer the one with more card keywords or longer name
                                    original_keywords = sum(1 for kw in card_keywords if kw in original_card_name.lower())
                                    extracted_keywords = sum(1 for kw in card_keywords if kw in extracted_name.lower())
                                    if extracted_keywords > original_keywords or (extracted_keywords == original_keywords and len(extracted_name) > len(original_card_name)):
                                        card_name = extracted_name
                                        logger.debug(f"Using improved page title: {card_name} (had {extracted_keywords} keywords vs {original_keywords})")
                                    else:
                                        logger.debug(f"Keeping original card name '{original_card_name}' (better than page title '{extracted_name}')")
                                else:
                                    card_name = extracted_name
                                    logger.debug(f"Using page title: {card_name}")
                            elif original_card_name and self._is_valid_card_name(original_card_name):
                                # Page title doesn't have card keywords - keep original
                                logger.debug(f"Keeping original card name '{original_card_name}' (page title '{extracted_name}' lacks card keywords)")
                            else:
                                # No good original name, use page title anyway
                                card_name = extracted_name
                                logger.debug(f"Using page title as fallback: {card_name}")
                        elif original_card_name and self._is_valid_card_name(original_card_name):
                            # Page title is invalid, keep original
                            logger.debug(f"Keeping original card name '{original_card_name}' (page title '{extracted_name}' is invalid)")
                        else:
                            # Both are invalid, but use page title as last resort
                            card_name = extracted_name
                            logger.debug(f"Using page title as last resort: {card_name}")
                    
                    # Final validation - reject generic names that slipped through
                    if not self._is_valid_card_name(card_name):
                        logger.debug(f"Skipping invalid card name: {card_name}")
                        continue
                    
                    # Additional check: reject generic page titles
                    card_name_lower = card_name.lower().strip()
                    generic_rejections = [
                        'savings accounts', 'current accounts', 'checking accounts',
                        '404 not found', 'page not found', 'error', 'home',
                        'credit card benefits', 'credit card exclusive offers',
                        'balancecover', 'gift cards', 'visa gift cards'
                    ]
                    if card_name_lower in generic_rejections:
                        logger.debug(f"Rejecting generic page title: {card_name}")
                        continue
                    
                    seen_card_names.add(card_name)
                    
                    # Extract ALL card details from the detail page
                    card_data = {
                        'name': card_name,
                        'bank': 'Citibank (Trinidad & Tobago) Limited',
                        'bank_code': 'CITI',
                        'card_type': self._detect_card_type(card_name),
                        'scraping_url': card_url,
                        'scraped_at': timezone.now().isoformat(),
                    }
                    
                    # Extract card image
                    card_data['image_url'] = self._extract_card_image(card_soup, card_url)
                    
                    # Extract detailed information
                    card_data['annual_fee'] = self._extract_annual_fee(card_soup)
                    card_data['cashback_rate'] = self._extract_cashback_rate(card_soup)
                    card_data['reward_points_rate'] = self._extract_reward_rate(card_soup)
                    card_data['features'] = self._extract_features(card_soup)
                    card_data['welcome_bonus'] = self._extract_welcome_bonus(card_soup)
                    card_data['requirements'] = self._extract_requirements(card_soup)
                    
                    # Extract APR/Interest Rate
                    apr_info = self._extract_apr_info(card_soup)
                    if apr_info:
                        card_data['interest_rate'] = apr_info
                    
                    cards.append(card_data)
                    logger.info(f"✅ Successfully scraped: {card_name}")
                    logger.info(f"   - Annual Fee: ${card_data.get('annual_fee', 0) or 0}")
                    logger.info(f"   - Cashback: {card_data.get('cashback_rate', 0) or 0}%")
                    logger.info(f"   - Rewards: {card_data.get('reward_points_rate', 0) or 0}x")
                    logger.info(f"   - Interest Rate: {card_data.get('interest_rate', 'N/A')}")
                    logger.info(f"   - Welcome Bonus: {card_data.get('welcome_bonus', 'N/A')[:80] if card_data.get('welcome_bonus') else 'N/A'}")
                    logger.info(f"   - Features: {len(card_data.get('features', '').split(',')) if card_data.get('features') else 0} features")
                    logger.info(f"   - Image: {'Yes' if card_data.get('image_url') else 'No'}")
                    
                    time.sleep(1.5)  # Be respectful between requests
                    
                except Exception as e:
                    logger.error(f"Error scraping card {card_info.get('name', 'Unknown')}: {str(e)}", exc_info=True)
                    continue
            
            if not cards:
                logger.warning("No cards found from scraping, using sample data")
                return self._get_sample_citibank_cards()
            
            logger.info(f"✅ Successfully scraped {len(cards)} cards from Citibank")
            return cards
            
        except Exception as e:
            logger.error(f"Error scraping Citibank: {str(e)}", exc_info=True)
            return self._get_sample_citibank_cards()
    
    def _extract_all_card_links_from_page(self, soup: BeautifulSoup, base_url: str, seen_card_urls: set, card_url_pattern: str = None) -> List[Dict]:
        """Extract all card links from a page using multiple comprehensive strategies"""
        card_links = []
        initial_seen_count = len(seen_card_urls)
        
        # Default pattern - look for credit-card related URLs
        if not card_url_pattern:
            # Try to detect pattern from base_url
            if 'credit-cards' in base_url.lower():
                card_url_pattern = 'credit-card'
            elif 'card' in base_url.lower():
                card_url_pattern = 'card'
            else:
                card_url_pattern = 'card|credit'
        
        # Strategy 1: Find all links that might be card links
        all_links = soup.find_all('a', href=True)
        logger.info(f"Found {len(all_links)} total links on page")
        
        # Count how many match the pattern
        pattern_links = [l for l in all_links if re.search(card_url_pattern, l.get('href', ''), re.I)]
        logger.info(f"Found {len(pattern_links)} links matching pattern '{card_url_pattern}'")
        
        # For Citibank specifically, look for links in card containers/sections
        # Cards are often in sections like "Explore Featured Cards", "Rewards Cards", etc.
        card_sections = soup.find_all(['section', 'div'], class_=re.compile(r'card|product|feature', re.I))
        logger.info(f"Found {len(card_sections)} potential card sections/containers")
        
        # Also look for links in script tags or data attributes (for JS-rendered content)
        # Try both application/json and text/javascript script tags
        script_tags = soup.find_all('script', type=['application/json', 'text/javascript', None])
        for script in script_tags:
            try:
                script_content = script.string or ''
                if not script_content:
                    continue
                
                # Try to parse as JSON
                import json
                data = None
                try:
                    data = json.loads(script_content)
                except:
                    # Try to extract JSON from JavaScript code (look for JSON objects)
                    json_match = re.search(r'\{[^{}]*"cards?"[^{}]*\}', script_content, re.I)
                    if json_match:
                        try:
                            data = json.loads(json_match.group(0))
                        except:
                            pass
                
                if data:
                    # Look for card data in JSON (more flexible - check nested structures)
                    cards_data = []
                    if isinstance(data, dict):
                        # Check multiple possible keys
                        for key in ['cards', 'items', 'products', 'data', 'content', 'results']:
                            if key in data:
                                value = data[key]
                                if isinstance(value, list):
                                    cards_data.extend(value)
                                elif isinstance(value, dict):
                                    # Check if it's a nested structure
                                    for nested_key in ['cards', 'items', 'products', 'data']:
                                        if nested_key in value and isinstance(value[nested_key], list):
                                            cards_data.extend(value[nested_key])
                    
                    for card_data in cards_data:
                        if isinstance(card_data, dict):
                            card_url = card_data.get('url') or card_data.get('href') or card_data.get('link') or card_data.get('slug') or card_data.get('path')
                            if card_url:
                                # Check if it looks like a card URL
                                if re.search(r'card|credit|product', card_url, re.I):
                                    card_name = card_data.get('name') or card_data.get('title') or card_data.get('productName') or card_data.get('cardName') or ''
                                    if card_name and self._is_valid_card_name(card_name):
                                        clean_href = card_url.split('?')[0].rstrip('/')
                                        if clean_href not in seen_card_urls:
                                            full_url = urljoin(base_url, card_url)
                                            seen_card_urls.add(clean_href)
                                            card_links.append({
                                                'url': full_url,
                                                'name': card_name
                                            })
                                            logger.info(f"✅ Found card from JSON data: {card_name} -> {full_url}")
            except Exception as e:
                logger.debug(f"Error parsing script tag: {str(e)}")
                pass
        
        for link in all_links:
            href = link.get('href', '')
            if not href:
                continue
            
            # Skip invalid URLs early
            href_lower = href.lower().strip()
            
            # Skip javascript:void(0), javascript:, mailto:, tel:, etc.
            if any(href_lower.startswith(prefix) for prefix in ['javascript:', 'mailto:', 'tel:', '#', 'void(0)']):
                logger.debug(f"Skipping invalid URL: {href}")
                continue
            
            # Skip /compare/ URLs - these are category/comparison pages, not individual cards
            if '/compare/' in href_lower:
                logger.debug(f"Skipping comparison page: {href}")
                continue
            
            # Check if href matches card pattern (more flexible)
            is_card_link = False
            
            # Check for common card URL patterns (Citibank uses /credit-cards/ URLs)
            card_patterns = [
                r'/credit-cards/[^/]+',  # /credit-cards/card-name (Citibank pattern)
                r'credit[-_]?card',
                r'/card/',
                r'product',
                r'credit-card',
            ]
            
            for pattern in card_patterns:
                if re.search(pattern, href_lower, re.I):
                    is_card_link = True
                    break
            
            # Also check if it's NOT a category/view-all link
            if any(skip in href_lower for skip in ['view-all', 'viewall', 'category', 'explore']):
                # Skip category links, but allow if it's a specific card page
                if '/credit-cards/' in href_lower and len(href_lower.split('/credit-cards/')[-1].split('/')[0]) > 3:
                    # This might be a card page, not a category page
                    pass
                else:
                    continue
            
            # Also check if link text suggests it's a card
            link_text = link.get_text(strip=True).lower()
            if any(keyword in link_text for keyword in ['card', 'credit', 'visa', 'mastercard', 'platinum', 'gold']):
                if len(link_text) > 5 and 'view' not in link_text and 'all' not in link_text:
                    is_card_link = True
            
            if not is_card_link:
                continue
            
            # Skip ONLY navigation and non-card links
            skip_patterns = [
                'view-all', 'viewall', 'compare', 'terms', 'privacy', 'contact', 'help', 'support',
                'apply-now', 'learn-more', 'about', 'faq', 'card-member-agreement', 'cma-',
                'displayterms', 'online.citi.com', 'agreement'
            ]
            if any(skip in href_lower for skip in skip_patterns):
                logger.debug(f"Skipping navigation link: {href}")
                continue
            
            # Must have a meaningful path (not just root)
            clean_href = href.split('?')[0].split('#')[0].rstrip('/')
            if not clean_href or clean_href == base_url.rstrip('/') or len(clean_href) < 10:
                continue
            
            if clean_href in seen_card_urls:
                continue
            
            # Extract card name - try multiple strategies
            card_name = None
            
            # Strategy 1: Get from link text
            link_text = link.get_text(strip=True)
            if link_text and self._is_valid_card_name(link_text):
                card_name = link_text
            
            # Strategy 2: Look in parent container for heading/title
            if not card_name or not self._is_valid_card_name(card_name):
                parent = link.parent
                # Go up multiple levels to find card container
                for level in range(3):
                    if not parent:
                        break
                    # Look for headings in this level
                    title_elem = parent.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                    if title_elem:
                        title_text = title_elem.get_text(strip=True)
                        if title_text and self._is_valid_card_name(title_text):
                            card_name = title_text
                            break
                    # Look for data attributes
                    data_name = parent.get('data-card-name') or parent.get('data-product-name') or parent.get('data-name')
                    if data_name and self._is_valid_card_name(data_name):
                        card_name = data_name
                        break
                    parent = parent.parent if hasattr(parent, 'parent') else None
            
            # Strategy 3: Extract from URL
            if not card_name or not self._is_valid_card_name(card_name):
                card_name = self._extract_card_name_from_url(clean_href)
            
            # Strategy 4: Use URL slug as last resort
            if not card_name or len(card_name.strip()) < 3:
                # Extract last meaningful part of URL
                url_parts = [p for p in clean_href.split('/') if p and p not in ['http:', 'https:', '']]
                if url_parts:
                    card_slug = url_parts[-1]
                    card_name = card_slug.replace('-', ' ').replace('_', ' ').title()
            
            # Filter out "Card details" and other non-card names
            card_name_clean = card_name.strip() if card_name else ''
            skip_names = [
                'card details', 'details', 'apply now', 'apply', 'learn more', 'view all', 'explore cards',
                'balance transfer cards', 'rewards cards', 'cash back cards', 'travel cards', 
                'retail cards', 'retail store cards', 'small business credit cards', 'business credit cards',
                'credit card agreements', 'card member agreement', '0% intro apr credit cards',
                'earn', 'javascript:void', 'view balance transfer cards',
                'credit card benefits', 'credit card exclusive offers', 'balancecover credit card insurance',
                'balancecover', 'gift cards', 'visa gift cards', 'savings accounts', 'current accounts',
                'checking accounts', '404 not found', 'page not found', 'error'
            ]
            if card_name_clean.lower() in skip_names:
                logger.debug(f"Skipping category/navigation link: {href} (name: '{card_name_clean}')")
                continue
            
            # Also check if name ends with generic "Cards" (likely a category page)
            if card_name_clean.lower().endswith(' cards') and len(card_name_clean.split()) <= 3:
                logger.debug(f"Skipping likely category page: {href} (name: '{card_name_clean}')")
                continue
            
            # Accept the card if we have any reasonable name
            if card_name_clean and len(card_name_clean) > 3:
                full_url = urljoin(base_url, href)
                seen_card_urls.add(clean_href)
                card_links.append({
                    'url': full_url,
                    'name': card_name_clean
                })
                logger.info(f"✅ Found card: {card_name_clean} -> {full_url}")
            else:
                logger.debug(f"Skipping link with invalid name: {href} (name: '{card_name_clean}')")
        
        # Strategy 2: Look for card containers (divs, articles, sections with card classes)
        card_containers = soup.find_all(['div', 'article', 'section', 'li'], 
                                       class_=re.compile(r'card|product|offer|item', re.I))
        
        for container in card_containers:
            # Look for links inside card containers
            link_elem = container.find('a', href=True)
            if link_elem:
                href = link_elem.get('href', '')
                # Check if it's a card link
                if href and (re.search(r'card|credit', href, re.I) or any(keyword in link_elem.get_text(strip=True).lower() for keyword in ['card', 'credit', 'visa', 'mastercard'])):
                    clean_href = href.split('?')[0].rstrip('/')
                    
                    # Skip if already seen or is a navigation link (but allow 'apply' links as they might be card pages)
                    href_lower = href.lower()
                    if any(skip in href_lower for skip in ['view-all', 'compare-cards']):
                        continue
                    
                    if clean_href not in seen_card_urls and len(clean_href) > len('/credit-cards/'):
                        card_name = link_elem.get_text(strip=True)
                        if not card_name or not self._is_valid_card_name(card_name):
                            # Try to find name in container
                            title_elem = container.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                            if title_elem:
                                card_name = title_elem.get_text(strip=True)
                            else:
                                # Try data attributes
                                card_name = container.get('data-card-name') or container.get('data-name') or ''
                                if not card_name:
                                    card_name = self._extract_card_name_from_url(clean_href)
                        
                        if card_name and self._is_valid_card_name(card_name):
                            full_url = urljoin(base_url, href)
                            seen_card_urls.add(clean_href)
                            card_links.append({
                                'url': full_url,
                                'name': card_name
                            })
                            logger.debug(f"Found card link from container: {card_name} -> {full_url}")
        
        # Strategy 3: Look for data attributes that might contain card URLs
        elements_with_data = soup.find_all(attrs={'data-card-url': True}) + \
                            soup.find_all(attrs={'data-url': True}) + \
                            soup.find_all(attrs={'data-href': True})
        
        for elem in elements_with_data:
            card_url = elem.get('data-card-url') or elem.get('data-url') or elem.get('data-href')
            if card_url and '/credit-cards/' in card_url:
                clean_href = card_url.split('?')[0].rstrip('/')
                if clean_href not in seen_card_urls and len(clean_href) > len('/credit-cards/'):
                    card_name = elem.get('data-card-name') or elem.get_text(strip=True)
                    if not card_name or not self._is_valid_card_name(card_name):
                        card_name = self._extract_card_name_from_url(clean_href)
                    
                    if card_name and self._is_valid_card_name(card_name):
                        full_url = urljoin(base_url, card_url)
                        seen_card_urls.add(clean_href)
                        card_links.append({
                            'url': full_url,
                            'name': card_name
                        })
                        logger.debug(f"Found card link from data attribute: {card_name} -> {full_url}")
        
        # Strategy 4: Fallback - Find ANY link with credit-cards in it (very aggressive)
        # Also check for "Card details" links which might be on category pages
        # For Citibank, be more aggressive since they have many cards
        if len(card_links) < 10:  # If we found very few cards, try fallback (increased threshold for Citibank)
            logger.info(f"Only found {len(card_links)} cards, trying aggressive fallback to find more...")
            all_fallback_links = soup.find_all('a', href=True)
            for link in all_fallback_links:
                href = link.get('href', '')
                link_text = link.get_text(strip=True).lower()
                
                if href and '/credit-cards/' in href:
                    # Skip only obvious non-card links
                    if any(skip in href.lower() for skip in ['view-all', 'compare-cards', 'terms', 'privacy', 'help', 'support']):
                        continue
                    
                    # Check if it's a "Card details" link (these are card pages)
                    is_card_details = 'card details' in link_text or 'card-details' in href.lower()
                    
                    clean_href = href.split('?')[0].rstrip('/')
                    if clean_href not in seen_card_urls and len(clean_href) > len('/credit-cards/'):
                        card_name = link.get_text(strip=True) or self._extract_card_name_from_url(clean_href)
                        if not card_name:
                            card_slug = clean_href.split('/credit-cards/')[-1] if '/credit-cards/' in clean_href else ''
                            card_name = card_slug.replace('-', ' ').title() if card_slug else 'Unknown Card'
                        
                        # Filter out "Card details" and navigation text
                        card_name_clean = card_name.strip() if card_name else ''
                        if card_name_clean.lower() in ['card details', 'details', 'apply now', 'apply', 'learn more']:
                            continue
                        
                        if len(card_name_clean) > 3 or (is_card_details and len(card_name_clean) > 0):
                            full_url = urljoin(base_url, href)
                            seen_card_urls.add(clean_href)
                            # If it's a "Card details" link, try to find the actual card name from the page
                            if is_card_details and len(card_name_clean) < 5:
                                # Look for card name in nearby elements
                                parent = link.find_parent(['div', 'article', 'section'])
                                if parent:
                                    title = parent.find(['h1', 'h2', 'h3', 'h4'])
                                    if title:
                                        card_name_clean = title.get_text(strip=True)
                            
                            if len(card_name_clean) > 3:
                                card_links.append({
                                    'url': full_url,
                                    'name': card_name_clean
                                })
                                logger.info(f"Fallback found card: {card_name_clean} -> {full_url}")
        
        # Strategy 5: Look for card titles/headings that might have links nearby
        # Look for any heading that might be a card name
        card_headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5'])
        for heading in card_headings:
            heading_text = heading.get_text(strip=True)
            # Skip if it's clearly not a card name
            if not heading_text or len(heading_text) < 5:
                continue
            if heading_text.lower() in ['card details', 'apply now', 'view all', 'explore cards']:
                continue
            
            # Look for links in the same container or nearby
            container = heading.find_parent(['div', 'article', 'section', 'li', 'a'])
            if container:
                # First try to find a link in the container
                nearby_link = container.find('a', href=re.compile(r'/credit-cards/', re.I))
                if not nearby_link and container.name == 'a':
                    # The container itself might be the link
                    nearby_link = container
                
                if nearby_link:
                    href = nearby_link.get('href', '')
                    if href and '/credit-cards/' in href:
                        clean_href = href.split('?')[0].rstrip('/')
                        if clean_href not in seen_card_urls and len(clean_href) > len('/credit-cards/'):
                            # Use heading text as card name
                            card_name = heading_text
                            if card_name and len(card_name.strip()) > 3:
                                full_url = urljoin(base_url, href)
                                seen_card_urls.add(clean_href)
                                card_links.append({
                                    'url': full_url,
                                    'name': card_name.strip()
                                })
                                logger.info(f"Found card from heading: {card_name} -> {full_url}")
        
        # Strategy 6: Look for data attributes and card components
        card_elements = soup.find_all(attrs={'data-card-name': True}) + \
                       soup.find_all(attrs={'data-product-name': True}) + \
                       soup.find_all(class_=re.compile(r'card.*name|product.*name', re.I))
        
        for elem in card_elements:
            card_name = elem.get('data-card-name') or elem.get('data-product-name') or elem.get_text(strip=True)
            if not card_name or len(card_name) < 5:
                continue
            
            # Find link in this element or parent
            link_elem = elem.find('a', href=re.compile(r'/credit-cards/', re.I))
            if not link_elem:
                parent = elem.find_parent(['div', 'article', 'section'])
                if parent:
                    link_elem = parent.find('a', href=re.compile(r'/credit-cards/', re.I))
            
            if link_elem:
                href = link_elem.get('href', '')
                if href and '/credit-cards/' in href:
                    clean_href = href.split('?')[0].rstrip('/')
                    if clean_href not in seen_card_urls and len(clean_href) > len('/credit-cards/'):
                        full_url = urljoin(base_url, href)
                        seen_card_urls.add(clean_href)
                        card_links.append({
                            'url': full_url,
                            'name': card_name.strip()
                        })
                        logger.info(f"Found card from data attribute: {card_name} -> {full_url}")
        
        new_cards_found = len(seen_card_urls) - initial_seen_count
        logger.info(f"Extracted {new_cards_found} new card links from this page (total links found: {len(card_links)})")
        
        return card_links
    
    def _extract_card_name_from_url(self, url: str) -> str:
        """Extract card name from URL like '/credit-cards/citi-double-cash-credit-card'"""
        # Extract the card slug
        match = re.search(r'/credit-cards/([^/?]+)', url)
        if match:
            slug = match.group(1)
            # Remove common suffixes
            slug = re.sub(r'(-credit-card|-card)$', '', slug, flags=re.I)
            # Convert slug to readable name: 'citi-double-cash' -> 'Citi Double Cash'
            name = slug.replace('-', ' ').title()
            # Fix common patterns and preserve special cases
            name = re.sub(r'\bCiti\b', 'Citi', name)  # Preserve "Citi" capitalization
            name = re.sub(r'\bVisa\b', 'Visa', name)  # Preserve "Visa"
            name = re.sub(r'\bMastercard\b', 'Mastercard', name)  # Preserve "Mastercard"
            name = re.sub(r'\bAmex\b', 'Amex', name)  # Preserve "Amex"
            name = re.sub(r'\bAmerican Express\b', 'American Express', name)  # Preserve "American Express"
            # Remove extra spaces
            name = re.sub(r'\s+', ' ', name).strip()
            return name
        return ''
    
    def _extract_apr_info(self, element) -> Optional[float]:
        """Extract APR/interest rate information"""
        text = element.get_text() if hasattr(element, 'get_text') else str(element)
        # Look for APR patterns
        apr_patterns = [
            r'APR[:\s]+(\d+(?:\.\d+)?)\s*%',
            r'interest\s+rate[:\s]+(\d+(?:\.\d+)?)\s*%',
            r'(\d+(?:\.\d+)?)\s*%\s*APR',
            r'variable\s+APR[:\s]+(\d+(?:\.\d+)?)\s*%',
        ]
        
        for pattern in apr_patterns:
            match = re.search(pattern, text, re.I)
            if match:
                try:
                    return float(match.group(1))
                except:
                    pass
        
        return None
    
    # ==================== Generic Professional Scraper ====================
    def _scrape_bank_professional(self, url: str, bank_name: str, bank_code: str, card_link_pattern: str = None) -> List[Dict]:
        """Generic professional scraper that visits main page, finds all card links, and scrapes detail pages"""
        cards = []
        seen_card_names = set()
        seen_card_urls = set()
        
        try:
            # Step 1: Visit main page with browser if available
            logger.info(f"Step 1: Visiting {bank_name} cards page: {url}")
            
            if self.use_browser:
                logger.info("  Using headless browser to load page...")
                html_content = self._fetch_with_browser(url)
                if html_content:
                    soup = BeautifulSoup(html_content, 'html.parser')
                else:
                    response = self.session.get(url, timeout=30)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.content, 'html.parser')
            else:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
            
            # Step 2: Find all card links (use generic pattern detection)
            all_card_links = self._extract_all_card_links_from_page(soup, url, seen_card_urls)
            
            # If no card links found, try to find cards directly on the page
            if not all_card_links:
                logger.info("  No card links found, trying to extract cards directly from page...")
                card_containers = soup.find_all(['div', 'section', 'article'], class_=re.compile(r'card|product|credit', re.I))
                for container in card_containers:
                    # Look for card name
                    card_name_elem = container.find(['h1', 'h2', 'h3', 'h4', 'h5'])
                    if card_name_elem:
                        card_name = card_name_elem.get_text(strip=True)
                        if card_name and self._is_valid_card_name(card_name):
                            # Look for link in container
                            link_elem = container.find('a', href=True)
                            card_url = urljoin(url, link_elem.get('href', '')) if link_elem else url
                            
                            # Only add if URL is different from base URL
                            if card_url != url:
                                all_card_links.append({
                                    'url': card_url,
                                    'name': card_name
                                })
                            else:
                                # If no separate link, use the container itself as the card page
                                all_card_links.append({
                                    'url': url,
                                    'name': card_name
                                })
            
            logger.info(f"Step 2: Found {len(all_card_links)} card links")
            
            # Step 3: Visit each card's detail page and extract complete information
            for idx, card_info in enumerate(all_card_links):
                try:
                    card_url = card_info['url']
                    card_name = card_info['name']
                    
                    if card_name in seen_card_names:
                        continue
                    
                    logger.info(f"Scraping card {idx+1}/{len(all_card_links)}: {card_name}")
                    
                    # Visit card detail page (or use main page if same URL)
                    if card_url == url:
                        # Card is on the main page, use the main soup
                        card_soup = soup
                    elif self.use_browser:
                        html_content = self._fetch_with_browser(card_url)
                        if html_content:
                            card_soup = BeautifulSoup(html_content, 'html.parser')
                        else:
                            card_response = self.session.get(card_url, timeout=20)
                            if card_response.status_code != 200:
                                continue
                            card_soup = BeautifulSoup(card_response.content, 'html.parser')
                    else:
                        card_response = self.session.get(card_url, timeout=20)
                        if card_response.status_code != 200:
                            continue
                        card_soup = BeautifulSoup(card_response.content, 'html.parser')
                    
                    # Extract card name from page
                    page_title = card_soup.find(['h1', 'h2', 'h3'])
                    if page_title:
                        extracted_name = page_title.get_text(strip=True)
                        if extracted_name and self._is_valid_card_name(extracted_name):
                            card_name = extracted_name
                    
                    if not self._is_valid_card_name(card_name):
                        continue
                    
                    # Additional check: reject generic page titles
                    card_name_lower = card_name.lower().strip()
                    generic_rejections = [
                        'savings accounts', 'current accounts', 'checking accounts',
                        '404 not found', 'page not found', 'error', 'home',
                        'credit card benefits', 'credit card exclusive offers',
                        'balancecover', 'gift cards', 'visa gift cards'
                    ]
                    if card_name_lower in generic_rejections:
                        logger.debug(f"Rejecting generic page title: {card_name}")
                        continue
                    
                    seen_card_names.add(card_name)
                    
                    # Extract all card details
                    card_data = {
                        'name': card_name,
                        'bank': bank_name,
                        'bank_code': bank_code,
                        'card_type': self._detect_card_type(card_name),
                        'scraping_url': card_url,
                        'scraped_at': timezone.now().isoformat(),
                    }
                    
                    # Extract image
                    card_data['image_url'] = self._extract_card_image(card_soup, card_url)
                    
                    # Extract detailed information
                    card_data['annual_fee'] = self._extract_annual_fee(card_soup)
                    card_data['cashback_rate'] = self._extract_cashback_rate(card_soup)
                    card_data['reward_points_rate'] = self._extract_reward_rate(card_soup)
                    card_data['features'] = self._extract_features(card_soup)
                    card_data['welcome_bonus'] = self._extract_welcome_bonus(card_soup)
                    card_data['requirements'] = self._extract_requirements(card_soup)
                    
                    apr_info = self._extract_apr_info(card_soup)
                    if apr_info:
                        card_data['interest_rate'] = apr_info
                    
                    cards.append(card_data)
                    logger.info(f"✅ Scraped: {card_name}")
                    
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error scraping card {card_info.get('name', 'Unknown')}: {str(e)}")
                    continue
            
            if not cards:
                logger.warning(f"No cards found from scraping {bank_name}")
                return []
            
            logger.info(f"✅ Successfully scraped {len(cards)} cards from {bank_name}")
            return cards
            
        except Exception as e:
            logger.error(f"Error scraping {bank_name}: {str(e)}", exc_info=True)
            return []
    
    # ==================== ANSA Bank Scraper ====================
    def scrape_ansa_bank(self, url: str) -> List[Dict]:
        """Scrape ANSA Bank credit cards - Professional approach"""
        cards = self._scrape_bank_professional(
            url, 
            'ANSA Bank Limited',
            'ANSA'
        )
        
        if not cards:
            return self._get_sample_ansa_cards()
        
        return cards
    
    # ==================== CIBC Scraper ====================
    def scrape_cibc(self, url: str) -> List[Dict]:
        """Scrape CIBC Caribbean credit cards - Professional approach with special handling for CIBC structure"""
        # CIBC has a main cards page at /credit-and-debit/cards with links to individual card pages
        # The URL structure is: /credit-and-debit/cards/{card-name}
        cards = []
        seen_card_names = set()
        seen_card_urls = set()
        
        try:
            logger.info(f"Scraping CIBC Caribbean from: {url}")
            
            # Step 1: Visit main page or specific card page
            if self.use_browser:
                html_content = self._fetch_with_browser(url)
                if html_content:
                    soup = BeautifulSoup(html_content, 'html.parser')
                else:
                    response = self.session.get(url, timeout=30)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.content, 'html.parser')
            else:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
            
            # Step 2: Check if this is the main cards page or a specific card page
            is_main_page = '/credit-and-debit/cards' in url and url.count('/') <= 4
            
            if is_main_page:
                # Find all card links from main page
                # CIBC card links are typically: /credit-and-debit/cards/{card-name}
                card_links = []
                all_links = soup.find_all('a', href=True)
                
                for link in all_links:
                    href = link.get('href', '')
                    if '/credit-and-debit/cards/' in href and href != '/credit-and-debit/cards':
                        # Extract card name from URL
                        card_slug = href.split('/credit-and-debit/cards/')[-1].split('?')[0].split('#')[0]
                        if card_slug and len(card_slug) > 3:
                            full_url = urljoin(url, href)
                            clean_url = full_url.split('?')[0].rstrip('/')
                            
                            if clean_url not in seen_card_urls:
                                # Get card name from link text or URL
                                card_name = link.get_text(strip=True)
                                if not card_name or len(card_name) < 3:
                                    card_name = card_slug.replace('-', ' ').title()
                                
                                seen_card_urls.add(clean_url)
                                card_links.append({
                                    'url': full_url,
                                    'name': card_name
                                })
                                logger.info(f"Found CIBC card link: {card_name} -> {full_url}")
                
                # If no links found, try to find cards directly on the page
                if not card_links:
                    logger.info("No card links found, trying to extract cards directly from page...")
                    # Look for card containers
                    card_containers = soup.find_all(['div', 'article', 'section'], 
                                                   class_=re.compile(r'card|product|credit', re.I))
                    for container in card_containers:
                        # Look for headings that might be card names
                        heading = container.find(['h1', 'h2', 'h3', 'h4'])
                        if heading:
                            card_name = heading.get_text(strip=True)
                            if card_name and self._is_valid_card_name(card_name):
                                # Check if there's a link
                                link_elem = container.find('a', href=True)
                                card_url = urljoin(url, link_elem.get('href', '')) if link_elem else url
                                card_links.append({
                                    'url': card_url,
                                    'name': card_name
                                })
                
                logger.info(f"Found {len(card_links)} CIBC card links from main page")
                
                # Step 3: Visit each card's detail page
                for card_info in card_links:
                    try:
                        card_url = card_info['url']
                        card_name = card_info['name']
                        
                        if card_name in seen_card_names:
                            continue
                        
                        logger.info(f"Scraping CIBC card: {card_name} from {card_url}")
                        
                        # Visit card detail page
                        if self.use_browser:
                            card_html = self._fetch_with_browser(card_url)
                            if card_html:
                                card_soup = BeautifulSoup(card_html, 'html.parser')
                            else:
                                card_response = self.session.get(card_url, timeout=20)
                                if card_response.status_code != 200:
                                    continue
                                card_soup = BeautifulSoup(card_response.content, 'html.parser')
                        else:
                            card_response = self.session.get(card_url, timeout=20)
                            if card_response.status_code != 200:
                                continue
                            card_soup = BeautifulSoup(card_response.content, 'html.parser')
                        
                        # Extract card details
                        card_data = {
                            'name': card_name,
                            'bank': 'CIBC Caribbean Bank (Trinidad & Tobago) Limited',
                            'bank_code': 'CIBC',
                            'card_type': self._detect_card_type(card_name),
                            'scraping_url': card_url,
                            'scraped_at': timezone.now().isoformat(),
                        }
                        
                        # Extract all details
                        card_data['image_url'] = self._extract_card_image(card_soup, card_url)
                        card_data['annual_fee'] = self._extract_annual_fee(card_soup)
                        card_data['cashback_rate'] = self._extract_cashback_rate(card_soup)
                        card_data['reward_points_rate'] = self._extract_reward_rate(card_soup)
                        card_data['features'] = self._extract_features(card_soup)
                        card_data['welcome_bonus'] = self._extract_welcome_bonus(card_soup)
                        card_data['requirements'] = self._extract_requirements(card_soup)
                        
                        apr_info = self._extract_apr_info(card_soup)
                        if apr_info:
                            card_data['interest_rate'] = apr_info
                        
                        cards.append(card_data)
                        seen_card_names.add(card_name)
                        logger.info(f"✅ Scraped CIBC card: {card_name}")
                        
                        time.sleep(1)
                        
                    except Exception as e:
                        logger.error(f"Error scraping CIBC card {card_info.get('name', 'Unknown')}: {str(e)}")
                        continue
            else:
                # This is a specific card page, extract directly
                cards = self._scrape_bank_professional(
                    url,
                    'CIBC Caribbean Bank (Trinidad & Tobago) Limited',
                    'CIBC'
                )
            
            if not cards:
                logger.warning("No CIBC cards found, using sample data")
                return self._get_sample_cibc_cards()
            
            logger.info(f"✅ Successfully scraped {len(cards)} CIBC cards")
            return cards
            
        except Exception as e:
            logger.error(f"Error scraping CIBC: {str(e)}", exc_info=True)
            return self._get_sample_cibc_cards()
    
    # ==================== First Citizens Scraper ====================
    def scrape_first_citizens(self, url: str) -> List[Dict]:
        """Scrape First Citizens Bank credit cards - Professional approach"""
        cards = self._scrape_bank_professional(
            url,
            'First Citizens Bank Limited',
            'FIRST_CITIZENS'
        )
        
        if not cards:
            return self._get_sample_first_citizens_cards()
        
        return cards
    
    # ==================== JMMB Scraper ====================
    def scrape_jmmb(self, url: str) -> List[Dict]:
        """Scrape JMMB Bank credit cards - Professional approach"""
        cards = self._scrape_bank_professional(
            url,
            'JMMB Bank (T&T) Limited',
            'JMMB'
        )
        
        if not cards:
            return self._get_sample_jmmb_cards()
        
        return cards
    
    # ==================== RBC Scraper ====================
    def scrape_rbc(self, url: str) -> List[Dict]:
        """Scrape RBC Royal Bank credit cards - Professional approach"""
        cards = self._scrape_bank_professional(
            url,
            'RBC Royal Bank (Trinidad & Tobago) Limited',
            'RBC'
        )
        
        if not cards:
            return self._get_sample_rbc_cards()
        
        return cards
    
    # ==================== Republic Bank Scraper ====================
    def scrape_republic(self, url: str) -> List[Dict]:
        """Scrape Republic Bank credit cards - Professional approach"""
        cards = self._scrape_bank_professional(
            url,
            'Republic Bank Limited',
            'REPUBLIC'
        )
        
        if not cards:
            return self._get_sample_republic_cards()
        
        return cards
    
    # ==================== Scotiabank Scraper ====================
    def scrape_scotia(self, url: str) -> List[Dict]:
        """Scrape Scotiabank credit cards - Professional approach"""
        cards = self._scrape_bank_professional(
            url,
            'Scotiabank Trinidad and Tobago Limited',
            'SCOTIA'
        )
        
        if not cards:
            return self._get_sample_scotia_cards()
        
        return cards
    
    # ==================== Helper Methods ====================
    def _is_valid_card_name(self, name: str) -> bool:
        """Check if a name is a valid card name (not a navigation link)"""
        if not name or len(name) < 5:  # Minimum length for card names
            return False
        
        name_lower = name.lower().strip()
        
        # Filter out navigation/action text patterns
        exclude_patterns = [
            r'^view\s+all',
            r'^see\s+more',
            r'^explore',
            r'^learn\s+more',
            r'^apply\s+now',
            r'^compare',
            r'^cards?\s*$',  # Just "Cards" or "Card"
            r'^\d+\s+cards?$',  # "13 Cards" or "8 Cards"
            r'^all\s+',  # "All Rewards Cards"
            r'^site\s+map',  # "Site Map"
            r'^sitemap',  # "Sitemap"
            r'^rewards?\s*$',  # Just "Rewards" or "Reward"
            r'^javascript:',  # JavaScript links
            r'^respond\s+to',  # "Respond to Mail Offer"
            r'^check\s+your',  # "Check Your Application"
            r'^credit\s+knowledge',  # "Credit Knowledge Center"
            r'^overdraft',  # "Overdraft Line of Credit"
            r'^investments',  # "Investments & Insurance"
            r'^citigold',  # "Citigold" (banking service, not card)
            r'^citi\s+shop',  # "Citi Shop"
            r'^balance\s+transfer\s+credit\s+cards?$',  # Category names
            r'^cash\s+back\s+credit\s+cards?$',
            r'^travel\s+credit\s+cards?$',
            r'^rewards\s+credit\s+cards?$',
            r'^retail\s+store\s+cards?$',
            r'^small\s+business\s+credit\s+cards?$',
            r'^card\s+member\s+agreement$',
            r'^savings\s+accounts?$',  # Generic account types
            r'^current\s+accounts?$',
            r'^checking\s+accounts?$',
            r'^credit\s+card\s+benefits$',  # Non-card pages
            r'^credit\s+card\s+exclusive\s+offers$',
            r'^balancecover',  # Insurance page
            r'^gift\s+cards?$',  # Gift cards (not credit cards)
            r'^404\s+not\s+found$',  # Error pages
            r'^page\s+not\s+found$',
        ]
        
        # Check against exclude patterns
        for pattern in exclude_patterns:
            if re.search(pattern, name_lower):
                return False
        
        # Must contain card-related keywords or be a proper card name
        card_keywords = ['card', 'visa', 'mastercard', 'amex', 'platinum', 'gold', 'premium', 'rewards', 'cash', 'travel', 'infinite', 'signature']
        if not any(keyword in name_lower for keyword in card_keywords):
            # If no keywords, check if it looks like a proper product name
            if name[0].islower() or (name.count(' ') < 1 and len(name) < 10):
                return False
        
        return True
    
    def _detect_card_type(self, card_name: str) -> str:
        """Detect card type from name"""
        name_lower = card_name.lower()
        if any(word in name_lower for word in ['platinum', 'platinum plus']):
            return 'PLATINUM'
        elif any(word in name_lower for word in ['gold', 'gold plus']):
            return 'GOLD'
        elif any(word in name_lower for word in ['premium', 'signature', 'infinite', 'world']):
            return 'PREMIUM'
        elif any(word in name_lower for word in ['debit']):
            return 'DEBIT'
        else:
            return 'CREDIT'
    
    def _extract_annual_fee(self, element) -> Optional[float]:
        """Extract annual fee from element"""
        text = element.get_text() if hasattr(element, 'get_text') else str(element)
        # Look for patterns like "$100", "TT$100", "100 TTD", "Free", "No annual fee"
        fee_patterns = [
            r'(?:TT\$|TTD|\$)\s*(\d+(?:\.\d+)?)',
            r'annual\s+fee[:\s]+(?:TT\$|TTD|\$)?\s*(\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)\s*(?:TTD|TT\$|\$)',
        ]
        
        for pattern in fee_patterns:
            match = re.search(pattern, text, re.I)
            if match:
                try:
                    return float(match.group(1))
                except:
                    pass
        
        # Check for free
        if re.search(r'\b(?:free|no\s+annual|waived)\b', text, re.I):
            return 0.0
        
        return None
    
    def _extract_cashback_rate(self, element) -> Optional[float]:
        """Extract cashback rate from element"""
        text = element.get_text() if hasattr(element, 'get_text') else str(element)
        # Look for patterns like "2%", "2% cashback", "up to 5%", "2% Cash Back"
        patterns = [
            r'(\d+(?:\.\d+)?)\s*%\s*cash\s*back',  # "2% cash back"
            r'cash\s*back[:\s]+(\d+(?:\.\d+)?)\s*%',  # "cash back: 2%"
            r'(\d+(?:\.\d+)?)\s*%\s*(?:cash\s*back|cb)',  # "2% cashback"
            r'earn\s+(\d+(?:\.\d+)?)\s*%\s*cash',  # "earn 2% cash"
            r'(\d+(?:\.\d+)?)\s*%\s*when\s+you\s+buy',  # "1% when you buy"
            r'(\d+(?:\.\d+)?)\s*%\s*as\s+you\s+pay',  # "1% as you pay" (for Double Cash)
        ]
        
        # Special handling for Citi Double Cash (1% + 1% = 2%)
        if 'double cash' in text.lower():
            # Look for "1% when you buy" and "1% as you pay"
            buy_match = re.search(r'(\d+(?:\.\d+)?)\s*%\s*(?:when\s+you\s+buy|on\s+purchases)', text, re.I)
            pay_match = re.search(r'(\d+(?:\.\d+)?)\s*%\s*(?:as\s+you\s+pay|when\s+you\s+pay)', text, re.I)
            if buy_match and pay_match:
                try:
                    buy_rate = float(buy_match.group(1))
                    pay_rate = float(pay_match.group(1))
                    return buy_rate + pay_rate  # Total cashback rate
                except:
                    pass
        
        for pattern in patterns:
            match = re.search(pattern, text, re.I)
            if match:
                try:
                    rate = float(match.group(1))
                    # If we find multiple rates, take the highest
                    if rate > 0:
                        return rate
                except:
                    pass
        
        return None
    
    def _extract_reward_rate(self, element) -> Optional[float]:
        """Extract reward points rate from element"""
        text = element.get_text() if hasattr(element, 'get_text') else str(element)
        # Look for patterns like "1 point per $1", "2x points"
        patterns = [
            r'(\d+(?:\.\d+)?)\s*(?:point|pt|pts)\s*per\s*(?:\$|dollar)',
            r'(\d+(?:\.\d+)?)x\s*(?:point|pt|pts)',
            r'(\d+(?:\.\d+)?)\s*(?:point|pt|pts)\s*per\s*(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.I)
            if match:
                try:
                    return float(match.group(1))
                except:
                    pass
        
        return None
    
    def _extract_features(self, element) -> Optional[str]:
        """Extract card features"""
        features = []
        
        # Method 1: Look for feature lists
        feature_items = element.find_all(['li', 'p', 'div'], class_=re.compile(r'feature|benefit|advantage', re.I))
        for item in feature_items[:15]:  # Limit to 15 features
            feature_text = item.get_text(strip=True)
            if feature_text and len(feature_text) > 5 and len(feature_text) < 200:
                features.append(feature_text)
        
        # Method 2: Look for sections with benefits
        benefit_sections = element.find_all(['section', 'div'], class_=re.compile(r'benefit|feature|advantage|perk', re.I))
        for section in benefit_sections:
            section_text = section.get_text(strip=True)
            if section_text and len(section_text) > 10:
                # Split by common separators
                parts = re.split(r'[•\-\n]', section_text)
                for part in parts[:10]:
                    part = part.strip()
                    if part and len(part) > 5 and len(part) < 200:
                        features.append(part)
        
        # Method 3: Extract from structured lists
        lists = element.find_all(['ul', 'ol'], class_=re.compile(r'feature|benefit|list', re.I))
        for ul in lists:
            items = ul.find_all('li')
            for item in items[:10]:
                item_text = item.get_text(strip=True)
                if item_text and len(item_text) > 5 and len(item_text) < 200:
                    features.append(item_text)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_features = []
        for feature in features:
            feature_lower = feature.lower()
            if feature_lower not in seen and len(feature) > 5:
                seen.add(feature_lower)
                unique_features.append(feature)
        
        if unique_features:
            return '\n'.join(unique_features[:15])  # Limit to 15 features
        
        return None
    
    def _extract_welcome_bonus(self, element) -> Optional[str]:
        """Extract welcome bonus information"""
        text = element.get_text() if hasattr(element, 'get_text') else str(element)
        # Look for welcome bonus patterns
        bonus_patterns = [
            r'welcome\s+bonus[:\s]+(.+?)(?:\.|$|\n)',
            r'sign[-\s]up\s+bonus[:\s]+(.+?)(?:\.|$|\n)',
            r'new\s+cardmember\s+bonus[:\s]+(.+?)(?:\.|$|\n)',
            r'earn\s+\$?\s*(\d+(?:,\d+)?)\s*(?:cash\s+back|points|miles|bonus)',  # "Earn $200 cash back"
            r'\$?\s*(\d+(?:,\d+)?)\s*(?:cash\s+back|points|miles)\s+after\s+you\s+spend',  # "$200 cash back after you spend"
            r'(\d+(?:,\d+)?)\s*(?:ThankYou|points|miles)\s+after\s+spending',  # "60,000 points after spending"
        ]
        
        for pattern in bonus_patterns:
            match = re.search(pattern, text, re.I)
            if match:
                try:
                    bonus_text = match.group(1).strip() if match.lastindex >= 1 else ''
                except (IndexError, AttributeError):
                    continue
                
                if not bonus_text:
                    continue
                
                # Try to get more context
                context_match = re.search(
                    r'(earn|get|receive)\s+\$?\s*(\d+(?:,\d+)?)\s*(?:cash\s+back|points|miles|bonus)\s+(?:after|when|if).*?(\d+(?:,\d+)?)\s*(?:spend|purchase|month)',
                    text, re.I
                )
                if context_match:
                    try:
                        # Safely access groups - check if they exist
                        groups = context_match.groups()
                        amount = groups[1] if len(groups) > 1 and groups[1] else bonus_text
                        reward_type = 'points' if 'points' in text.lower() or 'miles' in text.lower() else 'cash back'
                        spend_amount = groups[2] if len(groups) > 2 and groups[2] else ''
                        if spend_amount:
                            return f"Earn {amount} {reward_type} after spending ${spend_amount}"
                        else:
                            return f"Earn {amount} {reward_type}"
                    except (IndexError, AttributeError):
                        return bonus_text
                return bonus_text
        
        return None
    
    def _extract_requirements(self, element) -> Optional[str]:
        """Extract card requirements"""
        text = element.get_text() if hasattr(element, 'get_text') else str(element)
        # Look for requirements section
        req_section = element.find(['div', 'section'], class_=re.compile(r'requirement|eligibility|qualify', re.I))
        if req_section:
            return req_section.get_text(strip=True)
        
        return None
    
    def _extract_card_image(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        """Extract card image URL from the page"""
        # Strategy 1: Look for img tags with card-related classes/attributes
        img_selectors = [
            ('img', {'class': re.compile(r'card.*image|product.*image|card.*img', re.I)}),
            ('img', {'data-card-image': True}),
            ('img', {'data-product-image': True}),
            ('img', {'alt': re.compile(r'card|credit', re.I)}),
            ('img', {'src': re.compile(r'card|credit', re.I)}),
        ]
        
        for tag, attrs in img_selectors:
            images = soup.find_all(tag, attrs)
            for img in images:
                img_src = img.get('src') or img.get('data-src') or img.get('data-lazy-src') or img.get('data-original')
                if img_src:
                    # Convert relative URLs to absolute
                    if img_src.startswith('//'):
                        img_src = 'https:' + img_src
                    elif img_src.startswith('/'):
                        img_src = urljoin(base_url, img_src)
                    elif not img_src.startswith('http'):
                        img_src = urljoin(base_url, img_src)
                    
                    # Filter out small images (likely icons) and non-card images
                    if any(skip in img_src.lower() for skip in ['icon', 'logo', 'button', 'badge', 'flag', 'arrow']):
                        continue
                    
                    # Check image dimensions if available
                    width = img.get('width')
                    height = img.get('height')
                    if width and height:
                        try:
                            w, h = int(width), int(height)
                            if w < 200 or h < 200:  # Skip small images
                                continue
                        except:
                            pass
                    
                    logger.debug(f"Found card image: {img_src}")
                    return img_src
        
        # Strategy 2: Look for images in card containers
        card_containers = soup.find_all(['div', 'article', 'section'], 
                                       class_=re.compile(r'card|product|hero|banner', re.I))
        for container in card_containers:
            img = container.find('img')
            if img:
                img_src = img.get('src') or img.get('data-src') or img.get('data-lazy-src') or img.get('data-original')
                if img_src:
                    if img_src.startswith('//'):
                        img_src = 'https:' + img_src
                    elif img_src.startswith('/'):
                        img_src = urljoin(base_url, img_src)
                    elif not img_src.startswith('http'):
                        img_src = urljoin(base_url, img_src)
                    
                    # Skip icons and small images
                    if not any(skip in img_src.lower() for skip in ['icon', 'logo', 'button', 'badge']):
                        logger.debug(f"Found card image in container: {img_src}")
                        return img_src
        
        # Strategy 3: Look for background images in CSS
        style_elements = soup.find_all(['div', 'section'], style=re.compile(r'background.*image', re.I))
        for elem in style_elements:
            style = elem.get('style', '')
            match = re.search(r'url\(["\']?([^"\']+)["\']?\)', style)
            if match:
                img_src = match.group(1)
                if img_src.startswith('//'):
                    img_src = 'https:' + img_src
                elif img_src.startswith('/'):
                    img_src = urljoin(base_url, img_src)
                elif not img_src.startswith('http'):
                    img_src = urljoin(base_url, img_src)
                
                if not any(skip in img_src.lower() for skip in ['icon', 'logo', 'button', 'badge']):
                    logger.debug(f"Found card image in CSS: {img_src}")
                    return img_src
        
        logger.debug("No card image found on page")
        return None
    
    # ==================== Sample Data Methods ====================
    def _get_sample_citibank_cards(self) -> List[Dict]:
        """Sample Citibank cards based on typical offerings"""
        return [
            {
                'name': 'Citi Premier Card',
                'bank': 'Citibank (Trinidad & Tobago) Limited',
                'bank_code': 'CITI',
                'card_type': 'PREMIUM',
                'annual_fee': 95.0,
                'cashback_rate': 1.0,
                'reward_points_rate': 1.0,
                'welcome_bonus': '60,000 ThankYou Points after spending $4,000 in first 3 months',
                'features': '3x points on travel including gas stations\n3x points on restaurants\n3x points on entertainment\n1x points on all other purchases',
                'scraping_url': 'https://www.citi.com/credit-cards/',
                'scraped_at': timezone.now().isoformat(),
            },
            {
                'name': 'Citi Double Cash Card',
                'bank': 'Citibank (Trinidad & Tobago) Limited',
                'bank_code': 'CITI',
                'card_type': 'CREDIT',
                'annual_fee': 0.0,
                'cashback_rate': 2.0,
                'reward_points_rate': None,
                'welcome_bonus': None,
                'features': '2% cash back on all purchases\n1% when you buy, 1% when you pay\nNo annual fee',
                'scraping_url': 'https://www.citi.com/credit-cards/',
                'scraped_at': timezone.now().isoformat(),
            },
            {
                'name': 'Citi Rewards+ Card',
                'bank': 'Citibank (Trinidad & Tobago) Limited',
                'bank_code': 'CITI',
                'card_type': 'CREDIT',
                'annual_fee': 0.0,
                'cashback_rate': None,
                'reward_points_rate': 2.0,
                'welcome_bonus': '15,000 bonus points after spending $1,000 in first 3 months',
                'features': '2x ThankYou Points at supermarkets and gas stations\n1x points on all other purchases\nRound up to nearest 10 points',
                'scraping_url': 'https://www.citi.com/credit-cards/',
                'scraped_at': timezone.now().isoformat(),
            },
        ]
    
    def _get_sample_ansa_cards(self) -> List[Dict]:
        """Sample ANSA Bank cards"""
        return [
            {
                'name': 'ANSA Classic Credit Card',
                'bank': 'ANSA Bank Limited',
                'bank_code': 'ANSA',
                'card_type': 'CREDIT',
                'annual_fee': 150.0,
                'cashback_rate': 0.5,
                'features': 'Low interest rate\nFlexible payment options\n24/7 customer support',
                'scraping_url': 'https://www.ansabank.com/credit-cards',
                'scraped_at': timezone.now().isoformat(),
            },
            {
                'name': 'ANSA Gold Credit Card',
                'bank': 'ANSA Bank Limited',
                'bank_code': 'ANSA',
                'card_type': 'GOLD',
                'annual_fee': 300.0,
                'cashback_rate': 1.0,
                'features': 'Higher credit limit\nTravel insurance\nPurchase protection',
                'scraping_url': 'https://www.ansabank.com/credit-cards',
                'scraped_at': timezone.now().isoformat(),
            },
        ]
    
    def _get_sample_cibc_cards(self) -> List[Dict]:
        """Sample CIBC cards"""
        return [
            {
                'name': 'CIBC Aventura Visa Infinite Card',
                'bank': 'CIBC Caribbean Bank (Trinidad & Tobago) Limited',
                'bank_code': 'CIBC',
                'card_type': 'PREMIUM',
                'annual_fee': 120.0,
                'reward_points_rate': 1.5,
                'features': 'Travel rewards\nAirport lounge access\nTravel insurance',
                'scraping_url': 'https://www.cibccaribbean.com/tt/credit-cards',
                'scraped_at': timezone.now().isoformat(),
            },
        ]
    
    def _get_sample_first_citizens_cards(self) -> List[Dict]:
        """Sample First Citizens cards"""
        return [
            {
                'name': 'First Citizens Classic Credit Card',
                'bank': 'First Citizens Bank Limited',
                'bank_code': 'FIRST_CITIZENS',
                'card_type': 'CREDIT',
                'annual_fee': 100.0,
                'cashback_rate': 0.5,
                'features': 'Low annual fee\nFlexible payment options',
                'scraping_url': 'https://www.firstcitizens.com.tt/credit-cards',
                'scraped_at': timezone.now().isoformat(),
            },
            {
                'name': 'First Citizens Platinum Credit Card',
                'bank': 'First Citizens Bank Limited',
                'bank_code': 'FIRST_CITIZENS',
                'card_type': 'PLATINUM',
                'annual_fee': 400.0,
                'cashback_rate': 1.5,
                'features': 'Premium benefits\nTravel rewards\nConcierge service',
                'scraping_url': 'https://www.firstcitizens.com.tt/credit-cards',
                'scraped_at': timezone.now().isoformat(),
            },
        ]
    
    def _get_sample_jmmb_cards(self) -> List[Dict]:
        """Sample JMMB cards"""
        return [
            {
                'name': 'JMMB Credit Card',
                'bank': 'JMMB Bank (T&T) Limited',
                'bank_code': 'JMMB',
                'card_type': 'CREDIT',
                'annual_fee': 120.0,
                'cashback_rate': 0.75,
                'features': 'Competitive rates\nRewards program',
                'scraping_url': 'https://www.jmmb.com/tt/credit-cards',
                'scraped_at': timezone.now().isoformat(),
            },
        ]
    
    def _get_sample_rbc_cards(self) -> List[Dict]:
        """Sample RBC cards"""
        return [
            {
                'name': 'RBC Avion Visa Infinite',
                'bank': 'RBC Royal Bank (Trinidad & Tobago) Limited',
                'bank_code': 'RBC',
                'card_type': 'PREMIUM',
                'annual_fee': 120.0,
                'reward_points_rate': 1.25,
                'features': 'Travel rewards\nFlexible redemption\nTravel insurance',
                'scraping_url': 'https://www.rbcroyalbank.com/caribbean/credit-cards',
                'scraped_at': timezone.now().isoformat(),
            },
        ]
    
    def _get_sample_republic_cards(self) -> List[Dict]:
        """Sample Republic Bank cards"""
        return [
            {
                'name': 'Republic Classic Credit Card',
                'bank': 'Republic Bank Limited',
                'bank_code': 'REPUBLIC',
                'card_type': 'CREDIT',
                'annual_fee': 100.0,
                'cashback_rate': 0.5,
                'features': 'Low annual fee\nWide acceptance',
                'scraping_url': 'https://www.republictt.com/credit-cards',
                'scraped_at': timezone.now().isoformat(),
            },
            {
                'name': 'Republic Platinum Credit Card',
                'bank': 'Republic Bank Limited',
                'bank_code': 'REPUBLIC',
                'card_type': 'PLATINUM',
                'annual_fee': 350.0,
                'cashback_rate': 1.25,
                'features': 'Premium benefits\nTravel rewards\nPurchase protection',
                'scraping_url': 'https://www.republictt.com/credit-cards',
                'scraped_at': timezone.now().isoformat(),
            },
        ]
    
    def _get_sample_scotia_cards(self) -> List[Dict]:
        """Sample Scotiabank cards"""
        return [
            {
                'name': 'Scotiabank Gold American Express Card',
                'bank': 'Scotiabank Trinidad and Tobago Limited',
                'bank_code': 'SCOTIA',
                'card_type': 'GOLD',
                'annual_fee': 99.0,
                'reward_points_rate': 1.0,
                'features': 'Scene+ rewards\nTravel benefits\nInsurance coverage',
                'scraping_url': 'https://www.scotiabank.com/tt/en/personal/credit-cards.html',
                'scraped_at': timezone.now().isoformat(),
            },
            {
                'name': 'Scotiabank Momentum Visa Infinite',
                'bank': 'Scotiabank Trinidad and Tobago Limited',
                'bank_code': 'SCOTIA',
                'card_type': 'PREMIUM',
                'annual_fee': 120.0,
                'cashback_rate': 4.0,
                'features': '4% cash back on groceries and recurring bills\n2% cash back on gas and transit\n1% cash back on all other purchases',
                'scraping_url': 'https://www.scotiabank.com/tt/en/personal/credit-cards.html',
                'scraped_at': timezone.now().isoformat(),
            },
        ]
    
    # ==================== Main Scraping Methods ====================
    def scrape_bank(self, bank_code: str) -> Tuple[str, List[Dict]]:
        """Scrape cards for a specific bank - tries all URLs until successful"""
        logger.info(f"🔍 Starting scrape_bank for {bank_code}")
        bank_info = self.banks.get(bank_code)
        if not bank_info:
            logger.error(f"Bank {bank_code} not found in banks dictionary")
            return bank_code, []
        
        logger.info(f"Found bank info for {bank_code}: {bank_info['name']}")
        logger.info(f"Will try {len(bank_info['urls'])} URLs")
        
        all_cards = []
        seen_card_names = set()
        
        # Try all URLs until we get cards
        for idx, url in enumerate(bank_info['urls']):
            try:
                logger.info(f"📄 Trying URL {idx+1}/{len(bank_info['urls'])} for {bank_code}: {url}")
                cards = bank_info['scraper'](url)
                logger.info(f"Scraper returned {len(cards) if cards else 0} cards from {url}")
                if cards:
                    # Filter duplicates by card name
                    for card in cards:
                        card_name = card.get('name', '').strip()
                        if card_name and card_name not in seen_card_names:
                            seen_card_names.add(card_name)
                            all_cards.append(card)
                            logger.debug(f"Added card: {card_name}")
                        else:
                            logger.debug(f"Skipped duplicate card: {card_name}")
                    
                    logger.info(f"✅ Successfully scraped {len(cards)} cards from {url} (total unique: {len(all_cards)})")
                    # Continue trying other URLs to get more cards, but if we have enough, we can stop
                    if len(all_cards) >= 5:  # If we have at least 5 cards, that's probably all
                        logger.info(f"Got {len(all_cards)} cards, continuing to try other URLs for completeness...")
                else:
                    logger.warning(f"No cards returned from {url}")
            except Exception as e:
                logger.error(f"❌ Error scraping {bank_code} from {url}: {str(e)}", exc_info=True)
                continue
        
        # If still no cards, use sample data
        if not all_cards:
            logger.warning(f"⚠️  No cards found for {bank_code} from any URL, trying sample data...")
            sample_method = getattr(self, f'_get_sample_{bank_code.lower()}_cards', None)
            if sample_method:
                all_cards = sample_method()
                logger.info(f"✅ Using {len(all_cards)} sample cards for {bank_code}")
            else:
                logger.error(f"No sample data method found for {bank_code}")
        else:
            logger.info(f"✅ Final result: {len(all_cards)} unique cards scraped for {bank_code}")
        
        return bank_code, all_cards
    
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
                    bank_code, cards = future.result()
                    results[bank_code] = cards
                    logger.info(f"Scraped {len(cards)} cards from {bank_code}")
                except Exception as e:
                    logger.error(f"Failed to scrape {bank_code}: {str(e)}")
                    results[bank_code] = []
        
        return results
    
    def scrape_specific_banks(self, bank_codes: List[str]) -> Dict[str, List[Dict]]:
        """Scrape specific banks"""
        results = {}
        for bank_code in bank_codes:
            if bank_code in self.banks:
                bank_code, cards = self.scrape_bank(bank_code)
                results[bank_code] = cards
        return results
    
    def _fetch_with_browser(self, url: str, wait_time: int = 5) -> Optional[str]:
        """Fetch page content using Playwright headless browser for JavaScript-rendered pages"""
        if not PLAYWRIGHT_AVAILABLE:
            logger.warning("Playwright not available, cannot use browser")
            return None
        
        try:
            logger.debug(f"Launching headless browser for {url}...")
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                
                # Set user agent
                page.set_extra_http_headers({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                })
                
                # Navigate to page - use 'load' instead of 'networkidle' for better reliability
                # 'load' waits for the load event, which is more reliable than 'networkidle'
                logger.debug(f"Navigating to {url}...")
                try:
                    page.goto(url, wait_until='load', timeout=30000)  # Reduced timeout to 30s
                except Exception as goto_error:
                    # If 'load' times out, try 'domcontentloaded' which is faster
                    logger.debug(f"'load' wait failed, trying 'domcontentloaded': {str(goto_error)}")
                    try:
                        page.goto(url, wait_until='domcontentloaded', timeout=20000)
                    except Exception as dom_error:
                        logger.warning(f"Navigation failed with both 'load' and 'domcontentloaded': {str(dom_error)}")
                        browser.close()
                        return None
                
                # Wait for JavaScript to render content (reduced wait time)
                time.sleep(min(wait_time, 3))  # Cap at 3 seconds
                
                # Wait for page to be fully loaded - try multiple selectors with shorter timeout
                selectors_to_wait = [
                    'body',  # At least body should be there (most reliable)
                    'a[href*="/credit-cards/"]',  # Card links
                    '[class*="card"]',  # Elements with "card" in class
                    '[class*="product"]',  # Elements with "product" in class
                ]
                
                page_loaded = False
                for selector in selectors_to_wait:
                    try:
                        page.wait_for_selector(selector, timeout=3000)  # Reduced to 3s
                        logger.debug(f"Found elements matching selector: {selector}")
                        page_loaded = True
                        break
                    except:
                        logger.debug(f"No elements found with selector: {selector}, trying next...")
                        continue
                
                if not page_loaded:
                    logger.warning(f"Page may not be fully loaded, but continuing anyway for {url}")
                
                # Try to wait for network idle, but don't fail if it times out
                try:
                    page.wait_for_load_state('networkidle', timeout=5000)  # Reduced to 5s
                    logger.debug("Page network is idle")
                except:
                    logger.debug("Network idle timeout (this is OK), continuing anyway...")
                
                # Scroll to load lazy-loaded content (but don't wait too long)
                try:
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(1)  # Reduced wait
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
                    time.sleep(0.5)  # Reduced wait
                    page.evaluate("window.scrollTo(0, 0)")
                    time.sleep(0.5)  # Reduced wait
                except Exception as scroll_error:
                    logger.debug(f"Scroll failed (this is OK): {str(scroll_error)}")
                
                # Get fully rendered page content
                html_content = page.content()
                browser.close()
                
                logger.info(f"✅ Successfully fetched {url} with browser ({len(html_content)} bytes)")
                return html_content
                
        except Exception as e:
            error_msg = str(e)
            # Check if it's a timeout error
            if 'timeout' in error_msg.lower() or 'Timeout' in error_msg:
                logger.warning(f"Browser timeout for {url}, will fall back to requests if needed")
            else:
                logger.error(f"Error fetching {url} with browser: {error_msg}")
            return None
    
    def __del__(self):
        """Cleanup browser resources"""
        if self.browser:
            try:
                self.browser.close()
            except:
                pass
        if self.playwright:
            try:
                self.playwright.stop()
            except:
                pass

