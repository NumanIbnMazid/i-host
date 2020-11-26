"""
Django settings for ihost project.
Generated by 'django-admin startproject' using Django 3.1.2.
For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/
For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""

import os
from pathlib import Path
from rest_framework.settings import api_settings
import environ
from datetime import timedelta


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
env.read_env(env_file=os.path.join(BASE_DIR, '.env'))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env.str('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
if env.bool('DEBUG', default=''):
    DEBUG = env.bool('DEBUG')
else:
    DEBUG = True

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')


# Application definition

LIBRARY_APPS = [
    'django.contrib.postgres',
    # 'debug_toolbar',
    'rest_framework',
    'django_extensions',
    # 'rest_framework.authtoken',
    "knox",
    "drf_yasg2",
    "storages",
    'corsheaders',
    'drf_extra_fields',
    'softdelete',
    'rest_framework_tracking',
    'autofixture',
    # "mockups",
]
DJANGO_APPS = [
    'account_management',
    'restaurant',
]
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

]+LIBRARY_APPS+DJANGO_APPS

AUTH_USER_MODEL = 'account_management.UserAccount'

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

INTERNAL_IPS = [
    # ...
    '127.0.0.1',
    # ...
]


REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ('knox.auth.TokenAuthentication',),
    # # 'DEFAULT_AUTHENTICATION_CLASSES': [
    # #     'rest_framework.authentication.BasicAuthentication',
    # #     'rest_framework.authentication.SessionAuthentication',
    # # ],
    # 'DEFAULT_AUTHENTICATION_CLASSES': (

    #     'rest_framework_simplejwt.authentication.JWTAuthentication',
    # ),
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend']
}

SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header'
        }
    },
    'JSON_EDITOR': True,
}

ROOT_URLCONF = 'ihost.urls'

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

WSGI_APPLICATION = 'ihost.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases
if env.str('DATABASE_URL', default=''):
    DATABASES = {
        'default': env.db(),
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    # {
    #     'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    # },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    # {
    #     'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    # },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

STATIC_URL = '/static/'
MEDIA_URL = '/media/'
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

PRODUCTION_ACTIVATED = env.bool('PRODUCTION_ACTIVATED')
STATIC_ROOT = 'static'
MEDIA_ROOT = 'media'

if PRODUCTION_ACTIVATED:
    AWS_STORAGE_BUCKET_NAME = env.str(
        "AWS_STORAGE_BUCKET_NAME", default="ihost-space-dev")
else:
    AWS_STORAGE_BUCKET_NAME = env.str(
        "AWS_STORAGE_BUCKET_NAME_DEV", default="ihost-space-dev")

AWS_ACCESS_KEY_ID = env.str('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = env.str('AWS_SECRET_ACCESS_KEY')

AWS_S3_CUSTOM_DOMAIN = env.str(
    "AWS_S3_CUSTOM_DOMAIN", default="ihost-space.sgp1.cdn.digitaloceanspaces.com")
AWS_S3_CUSTOM_DOMAIN += '/'+AWS_STORAGE_BUCKET_NAME
AWS_S3_ENDPOINT_URL = env.str("AWS_S3_ENDPOINT_URL", default="")
# AWS_STORAGE_BUCKET_NAME = 'gozayaan'
# AWS_S3_CUSTOM_DOMAIN = 'gozayaan.sgp1.digitaloceanspaces.com'
# AWS_S3_ENDPOINT_URL = 'https://sgp1.digitaloceanspaces.com'
# General optimization for faster delivery
AWS_IS_GZIPPED = True
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
}
AWS_QUERYSTRING_AUTH = False
AWS_DEFAULT_ACL = 'public-read'

# static files location
AWS_LOCATION = env.str("AWS_LOCATION", default="static")
STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
# AWS_S3_ENDPOINT_URL
STATIC_URL = "https://%s/%s/" % (AWS_S3_CUSTOM_DOMAIN, AWS_LOCATION)
# media file location
AWS_MEDIA_LOCATION = env.str("AWS_MEDIA_LOCATION", default="media")
DEFAULT_FILE_STORAGE = 'utils.storage_backends.MediaStorage'


# AWS_S3_CUSTOM_DOMAIN
MEDIA_URL = "https://%s/%s/" % (AWS_S3_CUSTOM_DOMAIN, AWS_MEDIA_LOCATION)


CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]
REST_KNOX = {
    # 'SECURE_HASH_ALGORITHM': 'cryptography.hazmat.primitives.hashes.SHA512',
    # 'AUTH_TOKEN_CHARACTER_LENGTH': 64,
    'TOKEN_TTL': timedelta(hours=9900000),
    # 'USER_SERIALIZER': None,
    # 'TOKEN_LIMIT_PER_USER': None,
    # 'AUTO_REFRESH': False,
    # 'MIN_REFRESH_INTERVAL': 60,
    # 'AUTH_HEADER_PREFIX': 'Token',
    # 'EXPIRY_DATETIME_FORMAT': api_settings.DATETIME_FORMAT,
}
