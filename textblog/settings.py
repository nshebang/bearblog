import logging
import os
import dj_database_url
from django.utils.log import DEFAULT_LOGGING
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PROJECT_NAME = "🐼 BEARBLOG 🐼"

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET')
HEROKU_BEARER_TOKEN = os.getenv('HEROKU_BEARER_TOKEN')
LEMONSQUEEZY_SIGNATURE = os.getenv('LEMONSQUEEZY_SIGNATURE')
SLACK_WEBHOOK = os.getenv('SLACK_WEBHOOK')

DEBUG = (os.getenv('DEBUG') == 'True')

# Logging settings
if not DEBUG:
    def before_send(event, hint):
        """Don't log django.DisallowedHost errors."""
        if 'log_record' in hint:
            if hint['log_record'].name == 'django.security.DisallowedHost':
                return None

        return event

    DEFAULT_LOGGING['handlers']['console']['filters'] = []

    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'slack': {
                'class': 'textblog.logger.SlackExceptionHandler',
                'level': 'ERROR',
            },
        },
        'loggers': {
            'django.security.DisallowedHost': {
                'handlers': ['slack'],
                'level': 'CRITICAL',
                'propagate': False,
            },
        },
        'root': {
            'handlers': ['slack'],
            'level': 'ERROR',
        },
    }

    # ADMINS = (('Webmaster', os.getenv('ADMIN_EMAIL')),)

# Host & proxy
ALLOWED_HOSTS = ['*']
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True

X_FRAME_OPTIONS = 'ALLOWALL'

INTERNAL_IPS = ['127.0.0.1']

# Application definition
SITE_ID = 1

INSTALLED_APPS = [
    'judoscale.django',
    'django.contrib.admin',
    'django.contrib.sites',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'blogs.apps.BlogsConfig',
    'allauth.account',
    'allauth.socialaccount',
    'debug_toolbar',
    'pygmentify',
]

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)

MIDDLEWARE = [
    'django.middleware.gzip.GZipMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'blogs.middleware.XClacksOverheadMiddleware'
]

ROOT_URLCONF = 'textblog.urls'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.normpath(os.path.join(BASE_DIR, 'templates')),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.request',
                'blogs.context_processors.tz'
            ],
        },
    },
]


WSGI_APPLICATION = 'textblog.wsgi.application'

# All-auth setup
ACCOUNT_AUTHENTICATION_METHOD = 'email'
#if not DEBUG:
ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_CONFIRM_EMAIL_ON_GET = False
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USERNAME_REQUIRED = True
ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE = True
ACCOUNT_DEFAULT_HTTP_PROTOCOL = "https"

# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

CONN_MAX_AGE = 1
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'dev.db'),
    }
}

if os.getenv('DATABASE_URL'):
    db_from_env = dj_database_url.config(conn_max_age=600)
    DATABASES['default'].update(db_from_env)

DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10 MB

# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'es'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files
STATIC_ROOT = BASE_DIR / "staticfiles"
STATIC_URL = "static/"
GEOIP_PATH = "geoip/"

# Enable WhiteNoise's GZip compression of static assets.
STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"

LOGIN_REDIRECT_URL = '/dashboard/'

# Emailer

DEFAULT_FROM_EMAIL = "Ichoria★Blogs <noreplyichoria@cock.li>"
SERVER_EMAIL = "Ichoria★Blogs <noreplyichoria@cock.li>"
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'mail.cock.li'
EMAIL_HOST_USER = 'noreplyichoria@cock.li'
EMAIL_HOST_PASSWORD = os.getenv('MAILGUN_PASSWORD', False)
EMAIL_PORT = 587
EMAIL_USE_TLS = True

EMAILOCTOPUS_API = os.getenv('EMAILOCTOPUS_API', False)

# Referrer policy
SECURE_REFERRER_POLICY = "origin-when-cross-origin"
