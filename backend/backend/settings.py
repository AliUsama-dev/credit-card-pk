import os
from datetime import timedelta
from pathlib import Path

try:
    # Optional: if installed, load .env automatically in local dev
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent

# Media settings
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Create media directories if they don't exist
media_dirs = ['media', 'media/bank_logos', 'media/merchant_logos', 'media/profiles', 'media/statements']
for dir_name in media_dirs:
    dir_path = os.path.join(BASE_DIR, dir_name)
    os.makedirs(dir_path, exist_ok=True)

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-change-me')

DEBUG = os.environ.get('DJANGO_DEBUG', '1') == '1'

ALLOWED_HOSTS = [h.strip() for h in os.environ.get('DJANGO_ALLOWED_HOSTS', '*').split(',') if h.strip()]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party apps
    'rest_framework',
    'corsheaders',
    'rest_framework_simplejwt',
    'django_filters',
    'django_celery_beat',
    'django_celery_results',
    
    # Local apps
    'users',
    'cards',
    'transactions',
    'offers',
    'chatbot',
    'scraping',
    'admin_panel',
    'planning',
    'notifications',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'backend.urls'

# backend/settings.py

# Add context processors
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'backend.context_processors.media_urls',  # Add this
            ],
        },
    },
]

WSGI_APPLICATION = 'backend.wsgi.application'

DATABASES = {
    # Default: SQLite (works out-of-the-box)
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.environ.get('SQLITE_PATH', str(BASE_DIR / 'db.sqlite3')),
        'OPTIONS': {
            'timeout': 30,  # Increase timeout to 30 seconds for concurrent operations
        },
    },
}

# Optional: PostgreSQL via env vars (set DB_ENGINE=postgres)
if os.environ.get('DB_ENGINE', '').lower() in {'postgres', 'postgresql'}:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB', 'credit_card_optimizer'),
        'USER': os.environ.get('POSTGRES_USER', 'cc_user'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'password123'),
        'HOST': os.environ.get('POSTGRES_HOST', 'localhost'),
        'PORT': os.environ.get('POSTGRES_PORT', '5432'),
    }


AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Karachi'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'users.User'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
    ),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
}

CORS_ALLOW_ALL_ORIGINS = True

# If you later lock down CORS, add these:
# CORS_ALLOWED_ORIGINS = [
#     'http://localhost:3000',
# ]

CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Karachi'

# In local dev, run Celery tasks inline so scraping works without Redis/Celery workers
CELERY_TASK_ALWAYS_EAGER = os.environ.get('CELERY_TASK_ALWAYS_EAGER', '1') == '1'
CELERY_TASK_EAGER_PROPAGATES = True


# Email settings (for verification)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-password'

# File upload settings
MAX_UPLOAD_SIZE = 5242880  # 5MB
ALLOWED_STATEMENT_TYPES = ['application/pdf']

# OpenAI settings
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'debug.log'),
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'scraping': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}


# backend/settings.py - Add these settings

# Celery Configuration
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Karachi'
CELERY_ENABLE_UTC = True
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# Celery Beat Schedule
CELERY_BEAT_SCHEDULE = {
    'scrape-hourly-offers': {
        'task': 'scraping.tasks.scheduled_hourly_scraping',
        'schedule': 3600.0,  # Run every 1 hour (3600 seconds)
        'args': (),
    },
    'scrape-daily-offers': {
        'task': 'scraping.tasks.scheduled_daily_scraping',
        'schedule': 86400.0,  # Run every 24 hours (86400 seconds)
        'args': (),
    },
    'scrape-user-cards-entities-deals': {
        'task': 'scraping.tasks_peekaboo.scrape_all_user_cards_deals',
        'schedule': 7200.0,  # Run every 2 hours (7200 seconds)
        'args': (),
    },
    'update-expired-offers': {
        'task': 'offers.tasks.update_expired_offers',
        'schedule': 3600.0,  # Run every hour
        'args': (),
    },
    # New Peekaboo API scraping tasks
    'scrape-peekaboo-entities': {
        'task': 'scraping.tasks_peekaboo.scrape_peekaboo_entities',
        'schedule': 3600.0,  # Run every hour
        'args': (),
    },
    'scrape-peekaboo-categories': {
        'task': 'scraping.tasks_peekaboo.scrape_peekaboo_categories',
        'schedule': 3600.0,  # Run every hour
        'args': (),
    },
    'scrape-peekaboo-deals': {
        'task': 'scraping.tasks_peekaboo.scrape_peekaboo_deals',
        'schedule': 3600.0,  # Run every hour
        'args': (),
    },
    'update-expired-peekaboo-deals': {
        'task': 'scraping.tasks_peekaboo.update_expired_peekaboo_deals',
        'schedule': 3600.0,  # Run every hour
        'args': (),
    },
    'scrape-all-user-cards-deals': {
        'task': 'scraping.tasks_peekaboo.scrape_all_user_cards_deals',
        'schedule': 7200.0,  # Run every 2 hours (7200 seconds)
        'args': (),
    },
    # Notification tasks
    'send-expiring-offer-notifications': {
        'task': 'notifications.tasks.send_expiring_offer_notifications',
        'schedule': 3600.0,  # Run every hour
        'args': (),
    },
    'send-scheduled-purchase-reminders': {
        'task': 'notifications.tasks.send_scheduled_purchase_reminders',
        'schedule': 3600.0,  # Run every hour
        'args': (),
    },
    'send-new-offer-notifications': {
        'task': 'notifications.tasks.send_new_offer_notifications',
        'schedule': 3600.0,  # Run every hour
        'args': (),
    },
}


# JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    
    'JTI_CLAIM': 'jti',
    
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}