# Peekaboo Deals - Card Associations & Linking

## Overview
The system now extracts and links card associations from Peekaboo API deals. When a deal has an `associations` field (like "HBL World Elite DebitCard"), it automatically links the deal to the corresponding credit card in the database.

## Features Implemented

### 1. **Card Associations Extraction**
- Extracts `associations` array from Peekaboo API deals
- Each association contains:
  - `name`: Card name (e.g., "HBL World Elite DebitCard")
  - `image`: Card image URL
  - `typeId`: Association type ID
  - `sourceEntityAssociationId`: Source association ID

### 2. **Automatic Card Linking**
- Matches association card names to `CreditCard` records in database
- Links deals to cards via many-to-many relationship (`linked_cards`)
- Falls back to bank-level matching if specific card not found

### 3. **Source Entity (Bank) Information**
- Extracts `sourceEntityId`, `sourceEntityName`, `sourceEntityLogo` from deals
- Stores bank information from Peekaboo API
- Used for bank identification and matching

### 4. **My Card Deals Filtering**
- Filters deals by user's specific cards (via `linked_cards`)
- Falls back to bank-level filtering if no card match
- Shows only deals relevant to user's cards

## Database Changes

### New Fields in `PeekabooDeal`:
- `associations`: JSONField storing raw associations from API
- `linked_cards`: ManyToManyField linking to CreditCard records
- `source_entity_id`: Bank ID from API
- `source_entity_name`: Bank name from API
- `source_entity_logo`: Bank logo URL from API

## Usage

### 1. Flush Database (Start Fresh)
```bash
cd backend
source ../venv/bin/activate
python manage.py flush_db --keep-superusers
```

This will:
- Delete all offers, deals, transactions, user cards
- Keep superuser accounts
- Preserve banks and credit card templates

### 2. Scrape Peekaboo Data
1. Sign up and login
2. Go to Peekaboo Deals page
3. Click "Scrape Now"
4. System will:
   - Scrape entities (merchants)
   - Scrape categories
   - Scrape deals for all cities
   - Extract and link card associations

### 3. Add Your Cards
1. Go to Cards page
2. Select your bank
3. Select your card (all cards for that bank are shown)
4. Enter card details (last 4 digits, expiry)
5. Save

### 4. View Deals
- **All Deals**: Shows all scraped deals
- **My Card Deals**: Shows only deals for your cards

## Card Matching Logic

The system matches cards using:
1. **Exact Match**: Card name contains association name
2. **Fuzzy Match**: Matches key words from card name
3. **Bank Match**: If no card match, links to bank level

Example:
- Association: "HBL World Elite DebitCard"
- Matches: CreditCard with name containing "HBL" and "World" or "Elite"

## API Response Structure

### Deal with Associations:
```json
{
  "dealId": 70562,
  "title": "40% off",
  "associations": [
    {
      "typeId": 1729,
      "name": "HBL World Elite DebitCard",
      "image": "https://...",
      "order": 9,
      "sourceEntityAssociationId": 2059
    }
  ],
  "sourceEntityId": 32,
  "sourceEntityName": "Habib Bank Limited",
  "sourceEntityLogo": "https://..."
}
```

## Frontend Display

Deals now show:
- **Linked Cards**: List of cards this deal applies to
- **Source Entity**: Bank information from API
- **Associations**: Raw association data

## Next Steps

1. **Populate Credit Cards**: Ensure all Pakistani bank cards are in database
2. **Improve Matching**: Enhance card name matching algorithm
3. **Card Creation**: Auto-create cards from associations if not found

