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
            'GROCERIES': ['hyperstar', 'imtiaz', 'al-fatah', 'chase', 'naheed'],
            'DINING': ['kfc', 'mcdonald', 'burger', 'pizza', 'restaurant', 'cafe'],
            'FUEL': ['shell', 'caltex', 'total', 'gas', 'petrol'],
            'SHOPPING': ['malls', 'store', 'shop', 'retail', 'brand'],
            'TRAVEL': ['airline', 'hotel', 'travel', 'booking'],
            'UTILITIES': ['iesco', 'k-electric', 'ssgc', 'ptcl'],
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
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Extract date
            date_match = None
            for pattern in self.date_patterns:
                match = re.search(pattern, line)
                if match:
                    date_match = match.group()
                    break
            
            # Extract amount
            amount_match = re.search(self.amount_pattern, line)
            
            if date_match and amount_match:
                try:
                    # Extract merchant (rest of the line excluding date and amount)
                    merchant_start = line.find(date_match) + len(date_match)
                    merchant_end = line.find(amount_match)
                    merchant = line[merchant_start:merchant_end].strip()
                    
                    # Clean merchant name
                    merchant = self.clean_merchant_name(merchant)
                    
                    # Parse date
                    transaction_date = self.parse_date(date_match)
                    
                    # Parse amount
                    amount = float(amount_match.group().replace(',', ''))
                    
                    # Determine category
                    category = self.categorize_transaction(merchant)
                    
                    transaction = {
                        'date': transaction_date,
                        'merchant': merchant,
                        'amount': amount,
                        'category': category,
                        'original_text': line
                    }
                    
                    transactions.append(transaction)
                    
                except Exception as e:
                    print(f"Error parsing line: {line}, Error: {e}")
                    continue
        
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