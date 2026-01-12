import logging
import os
import re
from dataclasses import dataclass
from datetime import timedelta
from typing import Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from django.utils import timezone

logger = logging.getLogger(__name__)


def _is_blocked_html(html: str) -> bool:
    if not html:
        return True
    h = html.lower()
    blocked_markers = [
        'request rejected',
        'access denied',
        'incapsula',
        '_incapsula_resource',
        'cloudflare',
        'attention required',
        'captcha',
        'bot detection',
    ]
    return any(m in h for m in blocked_markers)


def _same_domain(url: str, base: str) -> bool:
    try:
        return urlparse(url).netloc == urlparse(base).netloc
    except Exception:
        return False


def _extract_discount_percent(text: str) -> Optional[float]:
    if not text:
        return None
    m = re.search(r'(\d{1,2}(?:\.\d+)?)\s*%', text)
    if not m:
        return None
    try:
        return float(m.group(1))
    except Exception:
        return None


def _detect_offer_type(text: str) -> str:
    t = (text or '').lower()
    if any(k in t for k in ['cashback', 'cash back', 'cash-back']):
        return 'CASHBACK'
    if any(k in t for k in ['emi', 'installment', 'easy payment']):
        return 'EMI'
    if any(k in t for k in ['reward', 'points', 'multiplier', 'double points']):
        return 'REWARD_MULTIPLIER'
    if any(k in t for k in ['waiver', 'no fee', 'free annual', 'fee']):
        return 'FEE_WAIVER'
    if any(k in t for k in ['discount', '%', 'off', 'save']):
        return 'DISCOUNT'
    return 'OTHER'


def _extract_city(text: str) -> str:
    t = (text or '').lower()
    cities = [
        'karachi', 'lahore', 'islamabad', 'rawalpindi', 'faisalabad', 'multan',
        'hyderabad', 'peshawar', 'quetta', 'gujranwala', 'sialkot', 'bahawalpur',
        'sargodha', 'sukkur', 'larkana', 'sheikhupura', 'mirpur khas', 'kasur', 'gujrat',
    ]
    for c in cities:
        if c in t:
            return c.upper().replace(' ', '_')
    return 'ALL_PAKISTAN'


def _extract_merchant(text: str) -> str:
    t = (text or '').lower()
    merchants = [
        'foodpanda', 'daraz', 'careem', 'uber', 'kfc', 'mcdonald', 'pizza hut',
        'domino', 'hardee', 'subway', 'gloria jeans', 'metro', 'naheed', 'imtiaz',
        'shell', 'pso', 'caltex', 'total', 'serena', 'pearl continental', 'khaadi',
        'alkaram', 'gul ahmed', 'junaid jamshed', 'j.',
    ]
    for m in merchants:
        if m in t:
            # keep original casing-ish
            return m.title().replace('J.', 'J.')
    return 'Various Merchants'


@dataclass(frozen=True)
class BankSource:
    code: str
    name: str
    home_url: str


class LivePakistanBankScraper:
    """
    Best-effort live scraper for Pakistan bank discount/offer pages.

    Notes:
    - Some banks use strong bot protection; in that case we log and return [].
    - Uses Playwright optionally for JS-heavy pages (controlled by SCRAPING_USE_BROWSER=1/0).
    """

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            }
        )
        self.use_browser = os.environ.get("SCRAPING_USE_BROWSER", "1") == "1"

        # Keep this list focused on sources that are reachable in Pakistan; you can add more.
        self.sources: dict[str, BankSource] = {
            "BAFL": BankSource(code="BAFL", name="Bank Alfalah", home_url="https://www.bankalfalah.com/"),
            "MEZAN": BankSource(code="MEZAN", name="Meezan Bank", home_url="https://www.meezanbank.com/"),
            "SCB": BankSource(code="SCB", name="Standard Chartered Pakistan", home_url="https://www.sc.com/pk/"),
            "MCB": BankSource(code="MCB", name="MCB Bank", home_url="https://www.mcb.com.pk/"),
            # Often blocked:
            "HBL": BankSource(code="HBL", name="Habib Bank Limited", home_url="https://www.hbl.com/"),
            "UBL": BankSource(code="UBL", name="United Bank Limited", home_url="https://www.ubl.com.pk/"),
        }

    def fetch_html(self, url: str, timeout: int = 30) -> Optional[str]:
        # First try plain HTTP
        try:
            r = self.session.get(url, timeout=timeout)
            if r.status_code == 200 and not _is_blocked_html(r.text):
                return r.text
            logger.info("HTTP fetch not usable (%s) for %s", r.status_code, url)
        except Exception as e:
            logger.info("HTTP fetch failed for %s: %s", url, e)

        if not self.use_browser:
            return None

        # Fallback to Playwright (some sites are JS-heavy)
        try:
            from playwright.sync_api import sync_playwright  # type: ignore
        except Exception as e:
            logger.warning("Playwright not available, cannot browser-fetch %s: %s", url, e)
            return None

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(2500)
                html = page.content()
                browser.close()

            if _is_blocked_html(html):
                logger.warning("Browser fetch blocked for %s", url)
                return None
            return html
        except Exception as e:
            logger.warning("Browser fetch failed for %s: %s", url, e)
            return None

    def discover_offer_pages(self, home_url: str, max_pages: int = 4) -> list[str]:
        html = self.fetch_html(home_url)
        if not html:
            return []
        soup = BeautifulSoup(html, "html.parser")

        keywords = ("offer", "offers", "promotion", "promotions", "discount", "deals", "campaign")
        candidates: list[str] = []

        for a in soup.select("a[href]"):
            href = a.get("href", "").strip()
            if not href or href.startswith("#") or href.lower().startswith("javascript:"):
                continue
            text = (a.get_text(" ", strip=True) or "").lower()
            if any(k in href.lower() for k in keywords) or any(k in text for k in keywords):
                full = urljoin(home_url, href)
                if _same_domain(full, home_url):
                    candidates.append(full)

        # De-dup preserving order
        seen = set()
        uniq = []
        for u in candidates:
            if u not in seen:
                seen.add(u)
                uniq.append(u)
        return uniq[:max_pages]

    def extract_offers_from_page(self, html: str, page_url: str, bank: BankSource) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")
        offers: list[dict] = []

        # Card-like blocks
        blocks = soup.select(
            '[class*="offer"], [class*="promo"], [class*="promotion"], [class*="deal"]'
        )
        if not blocks:
            blocks = soup.find_all(["article", "section", "div"], limit=250)

        for block in blocks:
            text = block.get_text(" ", strip=True)
            if not text:
                continue
            low = text.lower()
            if not any(k in low for k in ["discount", "cashback", "offer", "promotion", "%", "emi", "deal"]):
                continue

            title_el = block.find(["h1", "h2", "h3", "h4", "strong"])
            title = (title_el.get_text(" ", strip=True) if title_el else text[:120]).strip()
            if len(title) < 6:
                continue

            desc_el = block.find("p")
            description = (desc_el.get_text(" ", strip=True) if desc_el else text).strip()

            link_el = block.find("a", href=True)
            source_url = urljoin(page_url, link_el["href"]) if link_el else page_url

            offers.append(
                {
                    "title": title[:255],
                    "description": description[:2000],
                    "bank_code": bank.code,
                    "bank_name": bank.name,
                    "offer_type": _detect_offer_type(f"{title} {description}"),
                    "discount_percentage": _extract_discount_percent(f"{title} {description}"),
                    "merchant": _extract_merchant(f"{title} {description}"),
                    "city": _extract_city(f"{title} {description}"),
                    "valid_from": timezone.now().date(),
                    "valid_to": (timezone.now().date() + timedelta(days=60)),
                    "source_url": source_url,
                    "scraped_at": timezone.now().isoformat(),
                    "is_active": True,
                }
            )

        # de-dup by (title, source_url)
        seen = set()
        out = []
        for o in offers:
            key = (o["title"], o["source_url"])
            if key in seen:
                continue
            seen.add(key)
            out.append(o)
        return out[:30]

    def scrape_bank(self, bank_code: str) -> tuple[str, list[dict]]:
        bank = self.sources.get(bank_code.upper())
        if not bank:
            return bank_code, []

        pages = self.discover_offer_pages(bank.home_url)
        if not pages:
            # as a fallback, try the homepage itself
            pages = [bank.home_url]

        all_offers: list[dict] = []
        for page_url in pages:
            html = self.fetch_html(page_url)
            if not html:
                continue
            all_offers.extend(self.extract_offers_from_page(html, page_url, bank))

        # final de-dup
        seen = set()
        uniq = []
        for o in all_offers:
            key = (o["title"], o["source_url"])
            if key in seen:
                continue
            seen.add(key)
            uniq.append(o)
        return bank.code, uniq[:25]

    def scrape_all_banks(self) -> dict[str, list[dict]]:
        results: dict[str, list[dict]] = {}
        for code in self.sources.keys():
            try:
                b, offers = self.scrape_bank(code)
                results[b] = offers
                logger.info("Live scraped %s offers from %s", len(offers), b)
            except Exception as e:
                logger.error("Live scraping failed for %s: %s", code, e)
                results[code] = []
        return results



