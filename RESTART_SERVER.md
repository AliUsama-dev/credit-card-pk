# Fix 404 Error on Export Endpoint

## Problem
Getting 404 when accessing `/api/transactions/export/?format=csv`

## Root Cause
Django server needs to be **completely restarted** to load the new URL patterns.

## Solution

### Step 1: Stop the Current Server
In the terminal where Django is running:
- Press `Ctrl+C` to stop the server

### Step 2: Restart the Server
```bash
cd backend
python manage.py runserver
```

### Step 3: Verify
After restarting, the export should work. The URL patterns are correctly configured:
- ✅ `ExportTransactionsView` is properly defined
- ✅ URL pattern `/export/` is registered
- ✅ View imports successfully
- ✅ Reverse URL works: `/api/transactions/export/`

## Verification Commands

After restarting, you can verify the endpoint is working:

```bash
# In Django shell
python manage.py shell
>>> from django.urls import reverse
>>> reverse('export-transactions')
'/api/transactions/export/'
```

Or test with curl (if you have a valid token):
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     "http://localhost:8000/api/transactions/export/?format=csv"
```

## Expected Behavior

After restart:
1. Click "Export CSV" button in Transactions page
2. File should download successfully
3. CSV will contain all transactions with proper formatting

## If Still Getting 404 After Restart

1. Check Django server logs for any import errors
2. Verify the server actually restarted (look for "Starting development server" message)
3. Clear browser cache and try again
4. Check if there are any middleware issues blocking the request
