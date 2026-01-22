import pdfplumber
import re
from datetime import datetime
from typing import List, Dict
import pytesseract
from PIL import Image
import io

class StatementParser:
    def __init__(self):
        self.date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{4}',
            r'\d{1,2}-\d{1,2}-\d{4}',
            r'\d{1,2}\s+\w+\s+\d{4}',
        ]
        
        self.amount_pattern = r'[\d,]+\.\d{2}'
        self.merchant_patterns = {
            'GROCERIES': ['hyperstar', 'imtiaz', 'al-fatah', 'chase', 'naheed', 'supermarket', 'super store', 'grocery'],
            'DINING': ['kfc', 'mcdonald', 'burger', 'pizza', 'restaurant', 'cafe', 'aylanto', 'dining'],
            'FUEL': ['shell', 'caltex', 'total', 'gas', 'petrol', 'fuel', 'petrol pump', 'petrol station', 'fuel station'],
            'SHOPPING': ['malls', 'mall', 'store', 'shop', 'retail', 'brand', 'dolmen', 'centaurus', 'packages'],
            'TRAVEL': ['airline', 'hotel', 'travel', 'booking', 'serena', 'airline ticket'],
            'UTILITIES': ['iesco', 'k-electric', 'ssgc', 'ptcl', 'electric', 'bill payment', 'gas bill'],
            'ENTERTAINMENT': ['cinema', 'cinepax', 'nishat', 'entertainment', 'movie'],
            'ONLINE_SHOPPING': ['daraz', 'shophive', 'telemart', 'online', 'e-store', 'ecommerce'],
        }
    
    def parse_pdf_statement(self, pdf_path: str) -> List[Dict]:
        """Parse PDF credit card statement"""
        transactions = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    
                    if text:
                        # Extract transactions from text
                        page_transactions = self.extract_transactions_from_text(text)
                        transactions.extend(page_transactions)
                    else:
                        # Use OCR for scanned PDFs
                        page_image = page.to_image(resolution=300)
                        ocr_text = pytesseract.image_to_string(page_image.original)
                        page_transactions = self.extract_transactions_from_text(ocr_text)
                        transactions.extend(page_transactions)
            
            # Deduplicate and clean transactions
            transactions = self.clean_transactions(transactions)
            
        except Exception as e:
            print(f"Error parsing PDF: {e}")
            raise
        
        return transactions
    
    def extract_transactions_from_text(self, text: str) -> List[Dict]:
        """Extract transactions from statement text"""
        transactions = []
        lines = text.split('\n')
        
        # Debug: log first few lines
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"Parsing {len(lines)} lines from PDF")
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Skip header rows
            if any(header in line.upper() for header in ['DATE', 'MERCHANT', 'AMOUNT', 'TRANSACTION DETAILS', 'STATEMENT']):
                continue
            
            # Extract date (try all patterns)
            date_match = None
            date_match_obj = None
            for pattern in self.date_patterns:
                match = re.search(pattern, line)
                if match:
                    date_match = match.group()
                    date_match_obj = match
                    break
            
            if not date_match:
                continue
            
            # Extract amount (improved pattern to handle various formats)
            # Try multiple amount patterns
            amount_patterns = [
                r'[\d,]+\.\d{2}',  # Standard: 1,250.00
                r'\d+\.\d{2}',     # Without comma: 1250.00
                r'[\d,]+',         # Without decimals: 1,250
            ]
            
            amount_match = None
            amount_str = None
            for pattern in amount_patterns:
                match = re.search(pattern, line)
                if match:
                    # Make sure it's not part of a date
                    match_start = match.start()
                    match_end = match.end()
                    # Check if it's after the date (not part of date)
                    if match_start > date_match_obj.end():
                        amount_match = match
                        amount_str = match.group()
                        break
            
            if date_match and amount_match:
                try:
                    # Extract merchant (between date and amount)
                    date_end = date_match_obj.end()
                    amount_start = amount_match.start()
                    merchant = line[date_end:amount_start].strip()
                    
                    # Clean merchant name
                    merchant = self.clean_merchant_name(merchant)
                    
                    if not merchant:
                        # If no merchant found, skip
                        continue
                    
                    # Parse date
                    transaction_date = self.parse_date(date_match)
                    
                    # Parse amount (remove commas, ensure decimal)
                    amount_clean = amount_str.replace(',', '')
                    if '.' not in amount_clean:
                        amount_clean += '.00'
                    amount = float(amount_clean)
                    
                    # Skip if amount is 0 or negative
                    if amount <= 0:
                        continue
                    
                    # Determine category
                    category = self.categorize_transaction(merchant)
                    
                    transaction = {
                        'date': transaction_date,
                        'merchant': merchant,
                        'amount': amount,
                        'category': category,
                        'description': f'{merchant} - {category}'
                    }
                    
                    transactions.append(transaction)
                    logger.debug(f"Parsed transaction: {date_match} {merchant} {amount}")
                    
                except Exception as e:
                    logger.warning(f"Error parsing line: {line}, Error: {e}")
                    continue
        
        logger.info(f"Extracted {len(transactions)} transactions from PDF")
        return transactions
    
    def clean_merchant_name(self, merchant: str) -> str:
        """Clean merchant name"""
        # Remove common prefixes/suffixes
        remove_patterns = [
            r'^\d+\s*',
            r'\s+\d+$',
            r'[*#]+',
            r'CREDIT|DEBIT|PAYMENT',
            r'AUTHORIZATION',
        ]
        
        for pattern in remove_patterns:
            merchant = re.sub(pattern, '', merchant, flags=re.IGNORECASE)
        
        return merchant.strip()
    
    def parse_date(self, date_str: str) -> datetime:
        """Parse date string to datetime"""
        formats = ['%d/%m/%Y', '%d-%m-%Y', '%d %b %Y', '%d %B %Y']
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        # Default to current date if parsing fails
        return datetime.now()
    
    def categorize_transaction(self, merchant: str) -> str:
        """Categorize transaction based on merchant"""
        merchant_lower = merchant.lower()
        
        for category, keywords in self.merchant_patterns.items():
            if any(keyword in merchant_lower for keyword in keywords):
                return category
        
        return 'OTHER'
    
    def clean_transactions(self, transactions: List[Dict]) -> List[Dict]:
        """Clean and deduplicate transactions"""
        seen = set()
        cleaned = []
        
        for transaction in transactions:
            # Create unique key
            key = f"{transaction['date']}_{transaction['merchant']}_{transaction['amount']}"
            
            if key not in seen:
                seen.add(key)
                cleaned.append(transaction)
        
        return cleaned