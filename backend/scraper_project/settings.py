# File: backend/scraper_project/settings.py

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
# BASE_DIR is your 'backend' folder
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

SECRET_KEY = 'django-insecure-kpncfayqw=cdu_gcjv55kbcun-ae*t(q+eg8pjg+@y&q9539b+' # Change this!
DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# Application definition
INSTALLED_APPS = [
    'daphne', # Must be first
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'whitenoise.runserver_nostatic', # For serving static files

    # 3rd Party Apps
    'rest_framework',
    'corsheaders',
    'channels',
    
    # Your Apps
    'scraper_api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # Whitenoise middleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    # CORS is no longer needed in this setup, but harmless to leave
    'corsheaders.middleware.CorsMiddleware', 
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'scraper_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # --- THIS IS CORRECT ---
        # Tells Django to look in your React 'dist' folder for index.html
        'DIRS': [BASE_DIR.parent / 'frontend/dist'], 
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


WSGI_APPLICATION = 'scraper_project.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
# This is where 'collectstatic' will put all admin files
STATIC_ROOT = BASE_DIR / "staticfiles"

# --- THIS IS THE FIX ---
# Tells Django to look in your React 'dist' folder.
# When the browser asks for '/static/assets/index.js',
# Django will look in 'frontend/dist/assets/index.js'
STATICFILES_DIRS = [
    BASE_DIR.parent / "frontend/dist",
]
# --- END FIX ---

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- Custom Settings ---

# --- REMOVED CORS_ALLOWED_ORIGINS ---
# No longer needed, as React and Django are on the same domain.
# ------------------------------------

# ASGI (Asynchronous Server Gateway Interface)
ASGI_APPLICATION = 'scraper_project.asgi.application'

# CHANNEL_LAYERS (for WebSockets)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}

# CELERY (for Background Tasks)
CELERY_BROKER_URL = "redis://127.0.0.1:6379/0"
CELERY_RESULT_BACKEND = "redis://127.0.0.1:6379/0"
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

# --- CELERY QUEUES ---
CELERY_TASK_QUEUES = {
    'fast_queue': {
        'exchange': 'fast_queue',
        'routing_key': 'fast_queue',
    },
    'profile_queue': {
        'exchange': 'profile_queue',
        'routing_key': 'profile_queue',
    },
}
CELERY_TASK_DEFAULT_QUEUE = 'fast_queue'
# --- END CELERY QUEUES ---