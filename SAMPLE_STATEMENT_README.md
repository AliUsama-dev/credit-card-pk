# Sample Pakistani Bank Statement PDF

## 📄 File: `sample_pakistani_bank_statement.pdf`

This is a sample credit card statement PDF that you can use to test the Transactions & Analysis feature.

## 📊 What's Included

The PDF contains **25 realistic transactions** from Pakistani merchants:

- **Dining** (5 transactions): KFC, McDonald's, Pizza Hut, Cafe Aylanto, Burger King
- **Groceries** (4 transactions): Hyperstar, Imtiaz, Al-Fatah, Naheed
- **Fuel** (3 transactions): Shell, Caltex, Total
- **Shopping** (3 transactions): Dolmen Mall, Centaurus Mall, Packages Mall
- **Online Shopping** (3 transactions): Daraz, Shophive, Telemart
- **Utilities** (3 transactions): K-Electric, PTCL, SSGC
- **Entertainment** (2 transactions): Cinepax, Nishat Cinema
- **Travel** (2 transactions): Serena Hotel, Airline Booking

**Total Amount: PKR 201,600.00**

## 🚀 How to Use

1. **Go to Transactions & Analysis page** in the application
2. **Click "Upload Statement"** button
3. **Select the PDF file**: `sample_pakistani_bank_statement.pdf`
4. **(Optional)** Select a card from the dropdown
5. **Click "Upload"**
6. The system will:
   - Parse all transactions from the PDF
   - Categorize each transaction automatically
   - Analyze savings opportunities using % OFF offers from Peekaboo and Partners Offers
   - Show you potential savings if you used different cards

## 🔄 Regenerate the PDF

If you want to create a new sample PDF with different transactions:

```bash
cd backend
python transactions/sample_statement_generator.py
```

The PDF will be generated in the current directory.

## 📝 PDF Format

The PDF is formatted to match real Pakistani bank statements:
- Date format: `DD/MM/YYYY` (e.g., 15/01/2024)
- Amount format: `PKR 1,234.56` (with commas and 2 decimal places)
- Merchant names: Real Pakistani business names and locations
- Statement period: January 2024

## ✅ Testing Features

This sample PDF helps you test:
- ✅ PDF parsing and extraction
- ✅ Transaction categorization
- ✅ Savings analysis based on % OFF offers
- ✅ Card recommendations
- ✅ Category-wise spending breakdown
- ✅ Potential savings calculations

## 💡 Notes

- All transactions are **fictional** and for testing purposes only
- The PDF format matches what the parser expects (date, merchant, amount on each line)
- The system will automatically match transactions to Peekaboo/Partners Offers categories
- Savings are calculated based on actual % OFF offers available for your cards
