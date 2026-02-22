import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(override=False)

BASE_DIR = Path(__file__).resolve().parent.parent

DJANGO_ENV = os.getenv('DJANGO_ENV', 'development')

SECRET_KEY = os.getenv('SECRET_KEY', '')
DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1')
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,moysklad_integration').split(',')

# CSRF
CSRF_TRUSTED_ORIGINS = [
    origin for origin in os.getenv('CSRF_TRUSTED_ORIGINS', '').split(',') if origin
]

# Application definition
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
    'drf_spectacular',

    # Local apps
    'integration',
    'references',
    'products',
    'cards',
    'pricing',
    'mapping',
    'catalog',
]

# Legacy app — only in development
if DJANGO_ENV != 'production':
    INSTALLED_APPS.append('legacy')

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

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'config.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'pim_db'),
        'USER': os.getenv('DB_USER', 'postgresuser'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', 'db'),
        'PORT': os.getenv('DB_PORT', '5432'),
    },
}

# Legacy database — only in development
if DJANGO_ENV != 'production':
    DATABASES['legacy'] = {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('LEGACY_DB_NAME', 'decorkz_db'),
        'USER': os.getenv('LEGACY_DB_USER', 'postgresuser'),
        'PASSWORD': os.getenv('LEGACY_DB_PASSWORD', ''),
        'HOST': os.getenv('LEGACY_DB_HOST', 'db'),
        'PORT': os.getenv('LEGACY_DB_PORT', '5432'),
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Asia/Almaty'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
}

# CORS
CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', 'http://localhost:3000').split(',')
CORS_ALLOW_CREDENTIALS = True

# МойСклад настройки
MOYSKLAD_API_URL = os.getenv('MOYSKLAD_API_URL', 'https://api.moysklad.ru/api/remap/1.2')
MOYSKLAD_LOGIN = os.getenv('MOYSKLAD_LOGIN', '')
MOYSKLAD_PASSWORD = os.getenv('MOYSKLAD_PASSWORD', '')
MOYSKLAD_TOKEN = os.getenv('MOYSKLAD_TOKEN', '')

# Spectacular settings
SPECTACULAR_SETTINGS = {
    'TITLE': 'МойСклад Integration API',
    'DESCRIPTION': 'API для интеграции с МойСклад',
    'VERSION': '1.0.0',
}

# Production security settings
if DJANGO_ENV == 'production':
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    CSRF_COOKIE_HTTPONLY = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True