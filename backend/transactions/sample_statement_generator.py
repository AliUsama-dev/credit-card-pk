#!/usr/bin/env python3
"""
Sample Pakistani Bank Credit Card Statement Generator
Creates a realistic PDF statement with transactions that can be parsed by the system
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime, timedelta
import os

# Sample transactions for Pakistani banks
TRANSACTIONS = [
    # Dining
    {'date': '15/01/2024', 'merchant': 'KFC Gulberg Lahore', 'amount': 1250.00, 'category': 'DINING'},
    {'date': '18/01/2024', 'merchant': 'McDonald\'s DHA Karachi', 'amount': 850.00, 'category': 'DINING'},
    {'date': '22/01/2024', 'merchant': 'Pizza Hut Clifton', 'amount': 2100.00, 'category': 'DINING'},
    {'date': '25/01/2024', 'merchant': 'Cafe Aylanto DHA', 'amount': 3500.00, 'category': 'DINING'},
    {'date': '28/01/2024', 'merchant': 'Burger King F-7 Islamabad', 'amount': 1100.00, 'category': 'DINING'},
    
    # Groceries
    {'date': '16/01/2024', 'merchant': 'Hyperstar DHA Phase 5', 'amount': 8500.00, 'category': 'GROCERIES'},
    {'date': '20/01/2024', 'merchant': 'Imtiaz Super Store', 'amount': 4200.00, 'category': 'GROCERIES'},
    {'date': '24/01/2024', 'merchant': 'Al-Fatah Supermarket', 'amount': 6800.00, 'category': 'GROCERIES'},
    {'date': '27/01/2024', 'merchant': 'Naheed Supermarket', 'amount': 3100.00, 'category': 'GROCERIES'},
    
    # Fuel
    {'date': '17/01/2024', 'merchant': 'Shell Petrol Station', 'amount': 5000.00, 'category': 'FUEL'},
    {'date': '21/01/2024', 'merchant': 'Caltex Fuel Station', 'amount': 4500.00, 'category': 'FUEL'},
    {'date': '26/01/2024', 'merchant': 'Total Petrol Pump', 'amount': 3800.00, 'category': 'FUEL'},
    
    # Shopping
    {'date': '19/01/2024', 'merchant': 'Dolmen Mall Clifton', 'amount': 12500.00, 'category': 'SHOPPING'},
    {'date': '23/01/2024', 'merchant': 'Centaurus Mall Islamabad', 'amount': 8900.00, 'category': 'SHOPPING'},
    {'date': '29/01/2024', 'merchant': 'Packages Mall Lahore', 'amount': 15200.00, 'category': 'SHOPPING'},
    
    # Online Shopping
    {'date': '18/01/2024', 'merchant': 'Daraz Online Store', 'amount': 4500.00, 'category': 'ONLINE_SHOPPING'},
    {'date': '22/01/2024', 'merchant': 'Shophive Electronics', 'amount': 25000.00, 'category': 'ONLINE_SHOPPING'},
    {'date': '26/01/2024', 'merchant': 'Telemart Online', 'amount': 12300.00, 'category': 'ONLINE_SHOPPING'},
    
    # Utilities
    {'date': '20/01/2024', 'merchant': 'K-Electric Bill Payment', 'amount': 8500.00, 'category': 'UTILITIES'},
    {'date': '25/01/2024', 'merchant': 'PTCL Bill Payment', 'amount': 3200.00, 'category': 'UTILITIES'},
    {'date': '28/01/2024', 'merchant': 'SSGC Gas Bill', 'amount': 2800.00, 'category': 'UTILITIES'},
    
    # Entertainment
    {'date': '19/01/2024', 'merchant': 'Cinepax Cinema', 'amount': 1800.00, 'category': 'ENTERTAINMENT'},
    {'date': '24/01/2024', 'merchant': 'Nishat Cinema', 'amount': 2200.00, 'category': 'ENTERTAINMENT'},
    
    # Travel
    {'date': '21/01/2024', 'merchant': 'Serena Hotel Booking', 'amount': 15000.00, 'category': 'TRAVEL'},
    {'date': '27/01/2024', 'merchant': 'Airline Ticket Booking', 'amount': 45000.00, 'category': 'TRAVEL'},
]

def format_amount(amount):
    """Format amount with commas and 2 decimal places"""
    return f"{amount:,.2f}"

def generate_statement_pdf(output_path='sample_pakistani_bank_statement.pdf'):
    """Generate a sample Pakistani bank credit card statement PDF"""
    
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1a237e'),
        alignment=TA_CENTER,
        spaceAfter=30,
    )
    
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#424242'),
        alignment=TA_LEFT,
    )
    
    # Bank Header
    story.append(Paragraph("AL BARAKA BANK LIMITED", title_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Account Information
    account_info = [
        ['Account Holder:', 'Muhammad Ahmed Khan'],
        ['Card Number:', '**** **** **** 1234'],
        ['Statement Period:', '01/01/2024 - 31/01/2024'],
        ['Statement Date:', datetime.now().strftime('%d/%m/%Y')],
    ]
    
    account_table = Table(account_info, colWidths=[2*inch, 4*inch])
    account_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e3f2fd')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    story.append(account_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Transaction Header
    story.append(Paragraph("TRANSACTION DETAILS", styles['Heading2']))
    story.append(Spacer(1, 0.2*inch))
    
    # Prepare transaction data
    transaction_data = [['Date', 'Merchant', 'Amount (PKR)']]
    
    total_amount = 0
    for txn in TRANSACTIONS:
        date = txn['date']
        merchant = txn['merchant']
        amount = format_amount(txn['amount'])
        transaction_data.append([date, merchant, amount])
        total_amount += txn['amount']
    
    # Transaction Table
    transaction_table = Table(transaction_data, colWidths=[1.2*inch, 4*inch, 1.5*inch])
    transaction_table.setStyle(TableStyle([
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1976d2')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, 0), 12),
        
        # Data rows
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),
        ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        
        # Alternating row colors
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
    ]))
    story.append(transaction_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Summary
    summary_data = [
        ['Total Transactions:', str(len(TRANSACTIONS))],
        ['Total Amount:', f"PKR {format_amount(total_amount)}"],
    ]
    
    summary_table = Table(summary_data, colWidths=[2*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e3f2fd')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Footer
    footer_text = """
    <b>Important Notes:</b><br/>
    • This is a sample statement for testing purposes only<br/>
    • All transactions are fictional<br/>
    • For any queries, please contact your bank<br/>
    """
    story.append(Paragraph(footer_text, styles['Normal']))
    
    # Build PDF
    doc.build(story)
    print(f"✅ Sample statement generated: {output_path}")
    print(f"📊 Total transactions: {len(TRANSACTIONS)}")
    print(f"💰 Total amount: PKR {format_amount(total_amount)}")
    
    return output_path

if __name__ == '__main__':
    # Generate the PDF
    output_file = generate_statement_pdf()
    print(f"\n📄 You can now upload '{output_file}' to the Transactions page for analysis!")
