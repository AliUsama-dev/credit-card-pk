# Complete Setup Guide - Pakistani Banks & Cards

## Overview
This guide explains how to set up the system with all Pakistani banks and their credit/debit cards, and how the card selection works.

## Step 1: Flush Database (Start Fresh)

```bash
cd backend
source ../venv/bin/activate
python manage.py flush_db --keep-superusers
```

This will:
- Delete all user data, offers, deals, transactions
- **Preserve** banks and credit cards (if they exist)
- Keep superuser accounts

## Step 2: Seed Pakistani Banks & Cards

```bash
python manage.py seed_pakistani_banks
```

This will create:
- **15 Pakistani Banks** (sorted A-Z):
  1. Allied Bank Limited (ABL)
  2. Askari Bank
  3. Bank Alfalah
  4. Bank Islami
  5. Bank of Punjab (BOP)
  6. Faysal Bank
  7. First Women Bank
  8. HBL (Habib Bank Limited)
  9. JS Bank
  10. MCB Bank (Muslim Commercial Bank)
  11. Meezan Bank
  12. Sindh Bank
  13. Soneri Bank
  14. Standard Chartered Bank
  15. UBL (United Bank Limited)

- **103 Credit/Debit Cards** including:
  - HBL: 15 cards (PayPak, Classic, Gold, World, Platinum, Prestige, etc.)
  - Meezan Bank: 9 cards
  - UBL: 8 cards
  - MCB: 8 cards
  - Bank Alfalah: 8 cards
  - And more for all banks

## Step 3: User Flow

### 3.1 Sign Up & Login
- Create a new account or use existing superuser

### 3.2 Add Your Cards
1. Go to **Cards** page
2. Click **"Add Card"** button
3. **Step 1**: Select Bank
   - Dropdown shows all Pakistani banks (sorted A-Z)
   - Example: Select "HBL (Habib Bank Limited)"
4. **Step 2**: Select Card
   - Dropdown shows **only cards for selected bank**
   - Example: If HBL selected, shows:
     - HBL PayPak Debit Card
     - HBL Classic Debit Card
     - HBL Gold Debit Card
     - HBL World Debit Card
     - HBL Platinum Credit Card
     - etc.
5. **Step 3**: Enter Details
   - Last 4 digits of card
   - Expiry date (MM/YY format)
   - Mark as primary (optional)
6. Click **"Add Card"**

### 3.3 Scrape Peekaboo Deals
1. Go to **Peekaboo Deals** page
2. Click **"Scrape Now"** button
3. System will:
   - Scrape entities (merchants)
   - Scrape categories
   - Scrape deals for all cities
   - Extract card associations (e.g., "HBL World Elite DebitCard")
   - Link deals to matching cards in database

### 3.4 View Deals

#### All Deals Tab
- Shows all scraped deals
- Filter by: City, Category, Bank, Search

#### My Card Deals Tab
- Shows **only deals for your cards**
- Filters deals where:
  - Deal is linked to your specific card (via associations)
  - OR Deal is linked to your bank (if no specific card match)

## Card Matching Logic

When scraping deals, the system:

1. **Extracts Associations**: Gets card names from `associations` array
   ```json
   {
     "associations": [
       {"name": "HBL World Elite DebitCard"}
     ]
   }
   ```

2. **Matches to Database Cards**:
   - Searches for card with name containing "HBL" and "World" or "Elite"
   - Links deal to that card via `linked_cards` many-to-many relationship

3. **Falls Back to Bank Level**:
   - If no specific card match, links to bank level
   - User still sees deals for their bank

## Database Structure

### Banks Table
- Stores all Pakistani banks
- Sorted alphabetically (A-Z)

### Credit Cards Table
- Stores all cards for each bank
- Linked to bank via ForeignKey
- Filtered by bank when user selects bank

### Peekaboo Deals Table
- Stores scraped deals
- `linked_cards`: ManyToManyField - links to specific cards
- `bank`: ForeignKey - links to bank
- `associations`: JSONField - stores raw association data

## Frontend Card Selection

The frontend uses **Django-style choice fields**:

1. **Bank Selection**:
   - Dropdown with all banks (sorted A-Z)
   - When bank selected, triggers card filtering

2. **Card Selection**:
   - Dropdown shows only cards for selected bank
   - Disabled until bank is selected
   - Shows card name and type

## Example Flow

1. User selects **"HBL (Habib Bank Limited)"**
2. Card dropdown shows:
   - HBL PayPak Debit Card
   - HBL Classic Debit Card
   - HBL Gold Debit Card
   - HBL World Debit Card
   - HBL Platinum Credit Card
   - etc. (all 15 HBL cards)

3. User selects **"HBL World Debit Card"**
4. Enters card details and saves

5. When scraping:
   - Deal with association "HBL World Elite DebitCard" is found
   - System matches to "HBL World Debit Card" (fuzzy match)
   - Deal appears in "My Card Deals"

## Troubleshooting

### No banks showing after flush?
Run: `python manage.py seed_pakistani_banks`

### Cards not showing for selected bank?
- Check that cards exist in database: `python manage.py shell` → `CreditCard.objects.filter(bank__name="HBL").count()`
- Check frontend console for filtering logs

### Deals not showing in "My Card Deals"?
- Ensure you've added your cards
- Ensure deals have been scraped
- Check that associations were extracted and linked

## Commands Summary

```bash
# Flush database (preserves banks/cards)
python manage.py flush_db --keep-superusers

# Seed banks and cards
python manage.py seed_pakistani_banks

# Run migrations
python manage.py migrate

# Check system
python manage.py check
```

## Complete Test Flow

1. **Flush & Seed**:
   ```bash
   python manage.py flush_db --keep-superusers
   python manage.py seed_pakistani_banks
   ```

2. **Sign Up**: Create new account

3. **Add Card**: 
   - Select "HBL (Habib Bank Limited)"
   - Select "HBL World Debit Card"
   - Enter details and save

4. **Scrape Deals**:
   - Go to Peekaboo Deals
   - Click "Scrape Now"
   - Wait for completion

5. **View Deals**:
   - Check "All Deals" tab
   - Check "My Card Deals" tab (should show HBL deals)

All functionality is now complete and ready to use! 🎉

