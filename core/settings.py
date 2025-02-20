"""
Django settings for core project.

Generated by 'django-admin startproject' using Django 5.1.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

from pathlib import Path
from decouple import config
import os
from datetime import timedelta
from django.core.management.utils import get_random_secret_key
from celery.schedules import crontab

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = '/static/'  # Add a leading slash and trailing slash
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/
# Application definition

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'drf_spectacular',
    'rest_framework',
    'rest_framework_simplejwt.token_blacklist',
    "corsheaders",
    'import_export',
    'Log',
    'pandal',
    'pujo',
    'user',
    'reviews'
]

AUTH_USER_MODEL = 'user.User'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'EXCEPTION_HANDLER': 'core.exceptions.custom_exception_handler',
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=6),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "USER_AUTHENTICATION_RULE": "rest_framework_simplejwt.authentication.default_user_authentication_rule",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "TOKEN_USER_CLASS": "rest_framework_simplejwt.models.TokenUser",
}


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    "corsheaders.middleware.CorsMiddleware",
    "core.MiddleWares.middleware.LoggingMiddleware",
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'


SPECTACULAR_SETTINGS = {
    'TITLE': "Pujo Atlas Backend",
    'DESCRIPTION': 'API documentation',
    'VERSION': '1.1.0',
    'SERVERS': [
        {
            'url': 'https://atlas-api.ourkolkata.in/',
            'description': 'Production Server'
        },
        {
            'url': 'http://localhost:3000/',
            'description': 'Development Server'
        },
    ],
}

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

WSGI_APPLICATION = 'core.wsgi.application'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',  # Default
]


# DJANGO IMPORT EXPORT 
IMPORT_EXPORT_USE_TRANSACTIONS = True

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DJANGO_DB_NAME'),
        'USER': config('DJANGO_DB_USER'),
        'PASSWORD': config('DJANGO_DB_PASSWORD'),
        'HOST': config('DJANGO_DB_HOST'),
        'PORT': config('DJANGO_DB_PORT'),
    }
}

MINIO_URL = config('MINIO_URL')
MINIO_ACCESS_KEY = config('MINIO_ACCESS_KEY')
MINIO_SECRET_KEY = config('MINIO_SECRET_KEY')
MINIO_BUCKET_NAME = config('MINIO_BUCKET_NAME')

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = get_random_secret_key()
DEBUG = config('DEBUG', cast=bool)
ALLOWED_HOSTS = ["api-atlas.ourkolkata.in",'localhost', 'atlas-api.ourkolkata.in', '127.0.0.1',"ec2-3-111-147-124.ap-south-1.compute.amazonaws.com"]
# CORS_ALLOWED_ORIGINS = [
#     "http://localhost:3001",
#     "http://127.0.0.1:3001",
#     "http://localhost:4321",
# ]

# allowing all sub domains to access
# CORS_ALLOWED_ORIGIN_REGEXES = [
#     r"^https?://.*\.ourkolkata\.in$",
# ]

CORS_ALLOW_ALL_ORIGINS = True

# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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

# logger

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'django_debug.log',
            'formatter': 'verbose',
        },
         'database': {
            'class': 'Log.handlers.DatabaseLogHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file' , 'database'],
            'level': 'INFO',
        },
        'pujo': {
            'handlers': ['console', 'file' , 'database'],
            'level': 'INFO',
            'propagate': False,
        },
        'user': {
            'handlers': ['console', 'file' , 'database'],
            'level': 'INFO',
            'propagate': False,
        },
        'reviews': {
            'handlers': ['console', 'file' , 'database'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Time zone for Celery
CELERY_TIMEZONE = 'Asia/Kolkata'
# Disable UTC to use the specified timezone
CELERY_ENABLE_UTC = False
CELERY_BEAT_SCHEDULE = {
    'reset-trending': {
        'task': 'core.task.update_pujo_scores',
        'schedule': crontab(hour='5', minute='0'),  # Every day at 5 AM
    },
    'backup-logs': {
        'task': 'core.task.backup_logs_to_minio',
        'schedule': crontab(hour='4', minute='30'),  # Every day at 4:30 AM
    },
}



# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

SESSION_COOKIE_SECURE = True

CSRF_COOKIE_SECURE = True


# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
