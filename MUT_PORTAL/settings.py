
import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-&ufm^rb#bc!uln!v8zfhj)!h=24l@8&dx-jb0xivi&3l8hck!n'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'portal',
    'django.contrib.humanize',
]

AUTH_USER_MODEL = 'portal.User'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'MUT_PORTAL.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates'
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'portal.context_processors.ai_chatbot_context',  # ← Add this line
            ],
        },
    },
]

# AI Chatbot Settings (Optional - add these for customization)
AI_CHATBOT_SETTINGS = {
    'ENABLED': True,
    'SESSION_TIMEOUT_HOURS': 24,
    'MAX_MESSAGE_LENGTH': 1000,
    'TYPING_DELAY_SECONDS': 1,
    'SUGGESTIONS_COUNT': 5,
    'ALERTS_CHECK_INTERVAL': 60,  # seconds
    'CONFIDENCE_THRESHOLD': 70,  # percentage
}

# If using Celery for background tasks
CELERY_BEAT_SCHEDULE = {
    'check-proactive-alerts': {
        'task': 'portal.tasks.check_proactive_alerts',
        'schedule': 3600.0,  # Run every hour
    },
    'clean-old-sessions': {
        'task': 'portal.tasks.clean_old_sessions',
        'schedule': 86400.0,  # Run daily
    },
}


WSGI_APPLICATION = 'MUT_PORTAL.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'mut_portal_db',      # Database name
        'USER': 'postgres',           # DB username
        'PASSWORD': 'cp7kvt',  # DB password
        'HOST': 'localhost',          # Or IP if remote
        'PORT': '5432',               # Default PostgreSQL port
    }
}



# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS=[
    os.path.join(BASE_DIR , 'static'),
]
# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

"""
Add these settings to your Django settings.py file
"""

# ============= M-PESA CONFIGURATION =============

# M-Pesa Environment ('sandbox' or 'production')
MPESA_ENVIRONMENT = 'sandbox'  # Change to 'production' when going live

# M-Pesa Credentials
# Get these from https://developer.safaricom.co.ke/
MPESA_CONSUMER_KEY = os.getenv('MPESA_CONSUMER_KEY', '')
MPESA_CONSUMER_SECRET = os.getenv('MPESA_CONSUMER_SECRET', '')
MPESA_SHORTCODE = os.getenv('MPESA_SHORTCODE', '')  # Your paybill/till number
MPESA_PASSKEY = os.getenv('MPESA_PASSKEY', '')  # Lipa Na M-Pesa Online Passkey

# M-Pesa Callback URL
# This should be a publicly accessible URL that M-Pesa can reach
# Example: https://yourdomain.com/mpesa/callback/
MPESA_CALLBACK_URL = os.getenv('MPESA_CALLBACK_URL', 'https://yourdomain.com/mpesa/callback/')


# ============= SMS CONFIGURATION =============

# Africa's Talking Configuration (or use your preferred SMS provider)
AFRICASTALKING_USERNAME = os.getenv('AFRICASTALKING_USERNAME', 'sandbox')
AFRICASTALKING_API_KEY = os.getenv('AFRICASTALKING_API_KEY', '')


# ============= HOSTEL BOOKING CONFIGURATION =============

# Bed reservation timeout (in minutes)
BED_RESERVATION_TIMEOUT = 15  # Beds reserved for 15 minutes

# Payment verification polling interval (in seconds)
PAYMENT_CHECK_INTERVAL = 4

# Maximum payment verification attempts
MAX_PAYMENT_ATTEMPTS = 30  # 30 attempts * 4 seconds = 2 minutes


# Student ID M-Pesa Configuration
STUDENT_ID_MPESA_CONSUMER_KEY = 'your_consumer_key'
STUDENT_ID_MPESA_CONSUMER_SECRET = 'your_consumer_secret'
STUDENT_ID_MPESA_SHORTCODE = 'your_shortcode'
STUDENT_ID_MPESA_PASSKEY = 'your_passkey'
STUDENT_ID_MPESA_CALLBACK_URL = 'https://yourdomain.com/student/id-payment-callback/'

# ============= EMAIL SETTINGS (if not already configured) =============
# Configure your email backend for notifications
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'  # or your email provider
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@example.com'
EMAIL_HOST_PASSWORD = 'your-email-password'
DEFAULT_FROM_EMAIL = 'University <noreply@university.ac.ke>'


# ============= SMS SETTINGS (Optional) =============
# If you want to send SMS notifications
SMS_API_KEY = 'your_sms_api_key'
SMS_USERNAME = 'your_sms_username'
SMS_SENDER_ID = 'UNIVERSITY'

# ============= FILE UPLOAD SETTINGS =============
# Maximum file size for ID photos (2MB)
MAX_ID_PHOTO_SIZE = 2 * 1024 * 1024  # 2MB in bytes

# Allowed image formats
ALLOWED_ID_PHOTO_FORMATS = ['jpg', 'jpeg', 'png']
