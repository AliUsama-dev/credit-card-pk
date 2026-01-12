# Peekaboo Deals - Complete Implementation Guide

## Overview
This document explains the complete implementation of Peekaboo deals scraping, card association matching, and frontend display.

## Features Implemented

### 1. **Deal Information Display**
- ✅ **Description**: Full deal description with expandable "Show More/Less" functionality
- ✅ **Target Branches**: Shows all branch locations where the deal is available
- ✅ **Linked Cards**: Displays which cards the deal applies to (from database matching)
- ✅ **Associations**: Shows raw card associations from Peekaboo API if no database match found
- ✅ **Bank Information**: Shows both linked bank (from database) and source entity (from API)

### 2. **Card Association Matching**
The system uses **5 matching strategies** to link Peekaboo API card associations to database cards:

#### Strategy 1: Exact Match
- Matches card name exactly (case-insensitive)
- Example: "HBL World Elite DebitCard" → "HBL World Elite Debit Card"

#### Strategy 2: Normalized Match
- Removes "Card" suffix and matches
- Example: "HBL World Elite DebitCard" → "HBL World Elite Debit"

#### Strategy 3: Keyword Matching
- Extracts meaningful words (skips: hbl, ubl, mcb, card, debit, credit, the, a, an)
- Matches cards containing all meaningful words
- Example: "HBL World Elite DebitCard" → matches cards with "World" AND "Elite"

#### Strategy 4: First Word + Type Match
- Uses first meaningful word + card type (DEBIT/CREDIT)
- Example: "World" + "DEBIT" → "HBL World Debit Card"

#### Strategy 5: Fallback
- If no match found, uses first card of matching type for the bank

### 3. **Database Structure**

#### PeekabooDeal Model
```python
- target_branches: JSONField  # {branch_id: branch_name}
- linked_cards: ManyToManyField(CreditCard)  # Matched cards from database
- associations: JSONField  # Raw associations from API
- description: TextField  # Full deal description
- source_entity_name: CharField  # Bank name from API
```

### 4. **Frontend Display**

#### Deal Card Components:
1. **Title & Image**: Deal title and promotional image
2. **Merchant Info**: Target entity name and logo
3. **Discount Badge**: Percentage off (e.g., "40% OFF")
4. **Description**: Expandable description with "Show More/Less"
5. **Target Branches**: Chips showing branch locations (max 3, then "+X more")
6. **Applicable Cards**: Highlighted section showing:
   - Linked cards (from database matches) - shown as primary chips
   - Associations (from API if no match) - shown as outlined chips
7. **Details Section**:
   - City
   - Category
   - Bank (linked from database)
   - Source Entity (from API)
   - Expiry date
   - Days remaining
8. **Status Badges**:
   - Active/Inactive
   - Redeemable
   - Card count badge

### 5. **"My Card Deals" Filtering**

The "My Card Deals" tab shows deals where:
- Deal's `linked_cards` contains any of the user's cards
- OR Deal's `bank` matches any of the user's card banks

This ensures users only see deals relevant to their cards.

## API Endpoints

### Peekaboo API Endpoints Used:
1. **`/api/v7/category`**: Fetch categories
2. **`/api/v6/sourceEntities`**: Fetch entities/merchants
3. **`/api/v8/entity/deals`**: Fetch deals (with city, country, filters)
4. **`/api/v8/entity/detail`**: Fetch entity details (optional, for richer merchant data)

### Backend API Endpoints:
- `GET /api/offers/peekaboo/deals/`: Get all deals (with filters)
- `GET /api/offers/peekaboo/deals/my-cards/`: Get deals for user's cards
- `GET /api/offers/peekaboo/categories/`: Get categories
- `GET /api/offers/peekaboo/entities/`: Get entities
- `POST /api/offers/peekaboo/scrape/`: Trigger manual scraping

## Scraping Process

### Automated (Hourly via Celery Beat):
1. Scrape categories from `/api/v7/category`
2. Scrape entities from `/api/v6/sourceEntities`
3. Scrape deals from `/api/v8/entity/deals` for all cities
4. Process each deal:
   - Extract associations
   - Match to database cards (5 strategies)
   - Link to bank
   - Link to entity
   - Save/update deal

### Manual Trigger:
- User clicks "Scrape Now" button
- Triggers all scraping tasks
- Updates data in real-time

## Example: HBL Deal Matching

### API Response:
```json
{
  "associations": [
    {
      "name": "HBL World Elite DebitCard",
      "typeId": 1729
    }
  ],
  "sourceEntityName": "Habib Bank Limited"
}
```

### Matching Process:
1. **Extract**: "HBL World Elite DebitCard"
2. **Normalize**: "HBL World Elite Debit"
3. **Find Bank**: "Habib Bank Limited" → HBL Bank
4. **Match Card**:
   - Strategy 1: Exact match? No
   - Strategy 2: Normalized? No
   - Strategy 3: Keywords "World" + "Elite"? Yes! → "HBL World Elite Debit Card" or "HBL Prestige World Elite Debit Card"
5. **Link**: Deal linked to matched card(s)

### Frontend Display:
- Shows "HBL World Elite Debit Card" chip in "Applicable Cards" section
- Deal appears in "My Card Deals" if user has this card

## Seed Data

### Pakistani Banks & Cards:
- **15 Banks** seeded (A-Z sorted)
- **103+ Cards** with real names from bank websites
- Includes variations like:
  - "HBL World Elite Debit Card" (for matching "HBL World Elite DebitCard")
  - "HBL World Business Debit Card" (for matching "HBL World Business DebitCard")
  - "HBL Titanium Debit Card" (for matching "HBL Titanium DebitCard")

## Usage Flow

### 1. Initial Setup:
```bash
# Seed banks and cards
python manage.py seed_pakistani_banks

# Scrape deals
# - Automatic: Runs hourly via Celery Beat
# - Manual: Click "Scrape Now" button
```

### 2. User Flow:
1. **Sign Up & Login**
2. **Add Cards**:
   - Select bank (all Pakistani banks A-Z)
   - Select card (only cards for that bank)
   - Enter details and save
3. **View Deals**:
   - **All Deals Tab**: All scraped deals
   - **My Card Deals Tab**: Only deals for user's cards
4. **Filter Deals**:
   - By City
   - By Category
   - By Bank
   - By Search Query
   - Show/Hide Expired

### 3. Deal Information:
Each deal card shows:
- Full description (expandable)
- Branch locations
- Applicable cards (highlighted)
- Bank information
- Expiry date & days remaining
- Active/Inactive status

## Data Flow

```
Peekaboo API
    ↓
Scraping Tasks (Celery)
    ↓
Process Deals:
  - Extract associations
  - Match to cards (5 strategies)
  - Link to bank
  - Link to entity
    ↓
Save to Database
    ↓
API Serialization
    ↓
Frontend Display
    ↓
User Views:
  - All Deals
  - My Card Deals (filtered)
```

## Key Features

✅ **Real Data**: All data scraped from Peekaboo API (no hardcoded data)
✅ **Card Matching**: Intelligent 5-strategy matching system
✅ **Branch Information**: Shows all branch locations
✅ **Card Associations**: Displays which cards each deal applies to
✅ **User Filtering**: "My Card Deals" shows only relevant deals
✅ **Expandable Descriptions**: Full deal details with show more/less
✅ **Professional UI**: Modern, clean design with proper information hierarchy

## Troubleshooting

### No cards showing in "My Card Deals"?
1. Ensure you've added your cards
2. Ensure deals have been scraped
3. Check that associations were extracted and matched
4. Check backend logs for matching attempts

### Cards not matching?
1. Check seed data includes card variations
2. Check matching logic in `tasks_peekaboo.py`
3. Check backend logs for matching attempts
4. Verify card names in database match association names

### Deals not showing?
1. Run scraping manually: Click "Scrape Now"
2. Check Celery is running (for hourly scraping)
3. Check filters are not too restrictive
4. Check backend logs for scraping errors

## Summary

The system now:
- ✅ Scrapes real data from Peekaboo API
- ✅ Matches card associations to database cards (5 strategies)
- ✅ Displays full deal information (description, branches, cards)
- ✅ Filters "My Card Deals" by user's cards
- ✅ Shows professional, complete information
- ✅ Updates hourly automatically
- ✅ Supports manual scraping

Everything is working and ready to use! 🎉

