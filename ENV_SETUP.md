# Environment Variables Setup Guide

## 📁 Files Created

1. **backend/.env** - Backend environment variables
2. **frontend/.env** - Frontend environment variables

## 🔑 Environment Variables

### Backend (.env)
```
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
AWS_ACCESS_KEY_ID=AKIAxxxxxxxxxxxx
AWS_SECRET_ACCESS_KEY=xxxxxxxxxxxxxx
```

### Frontend (.env)
```
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
REACT_APP_AWS_ACCESS_KEY_ID=AKIAxxxxxxxxxxxx
REACT_APP_AWS_SECRET_ACCESS_KEY=xxxxxxxxxxxxxx
```

## 📍 Where These Variables Are Used

### Backend

#### 1. OPENAI_API_KEY
- **File**: `backend/chatbot/views.py`
- **Usage**: 
  ```python
  api_key = os.getenv('OPENAI_API_KEY') or getattr(settings, 'OPENAI_API_KEY', '')
  client = OpenAI(api_key=api_key)
  ```
- **File**: `backend/backend/settings.py`
- **Usage**: 
  ```python
  OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
  ```

#### 2. AWS_ACCESS_KEY_ID & AWS_SECRET_ACCESS_KEY
- **File**: `backend/backend/settings.py`
- **Usage**: 
  ```python
  AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', '')
  AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', '')
  AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
  ```
- **Access in code**: 
  ```python
  from django.conf import settings
  access_key = settings.AWS_ACCESS_KEY_ID
  secret_key = settings.AWS_SECRET_ACCESS_KEY
  ```

### Frontend

#### 1. REACT_APP_OPENAI_API_KEY
- **Access**: `process.env.REACT_APP_OPENAI_API_KEY`
- **Example**:
  ```typescript
  const openaiKey = process.env.REACT_APP_OPENAI_API_KEY;
  ```

#### 2. REACT_APP_AWS_ACCESS_KEY_ID & REACT_APP_AWS_SECRET_ACCESS_KEY
- **Access**: `process.env.REACT_APP_AWS_ACCESS_KEY_ID` and `process.env.REACT_APP_AWS_SECRET_ACCESS_KEY`
- **Example**:
  ```typescript
  const awsAccessKey = process.env.REACT_APP_AWS_ACCESS_KEY_ID;
  const awsSecretKey = process.env.REACT_APP_AWS_SECRET_ACCESS_KEY;
  ```

## 🔄 How It Works

### Backend
- The `.env` file is automatically loaded by `python-dotenv` in `backend/backend/settings.py`:
  ```python
  from dotenv import load_dotenv
  load_dotenv()
  ```
- Variables are accessible via `os.environ.get()` or `settings.VARIABLE_NAME`

### Frontend
- React automatically loads environment variables with `REACT_APP_` prefix from `.env`
- Variables are accessible via `process.env.REACT_APP_VARIABLE_NAME`
- **Important**: Restart the React dev server after changing `.env` file

## ⚠️ Important Notes

1. **Replace Placeholder Values**: Update the `xxxxxxxx` placeholders with your actual API keys
2. **Security**: Never commit `.env` files to git (already in `.gitignore`)
3. **Restart Required**: 
   - Backend: Restart Django server after changing `.env`
   - Frontend: Restart React dev server after changing `.env`
4. **Frontend Variables**: Only variables starting with `REACT_APP_` are exposed to the browser

## 🚀 Usage Examples

### Backend - Using AWS Credentials
```python
import boto3
from django.conf import settings

s3_client = boto3.client(
    's3',
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION
)
```

### Frontend - Using Environment Variables
```typescript
// In any React component or service
const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';
const openaiKey = process.env.REACT_APP_OPENAI_API_KEY;
```

## ✅ Verification

To verify the setup:
1. Check that `.env` files exist in both `backend/` and `frontend/` directories
2. Restart both servers
3. Check logs for successful loading (backend will log if OpenAI key is found)
