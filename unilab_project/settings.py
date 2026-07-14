import os
import json
from pathlib import Path

from app_paths import (
    APP_ROOT,
    STATIC_DIR,
    TEMPLATES_DIR,
    MEDIA_DIR,
    DB_CONFIG_FILE,
)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY') or 'django-insecure-super-secret-key-diagnostic'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Allow local machine and LAN connections for local desktop deployment
ALLOWED_HOSTS = ['*']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Unilab Modular Applications
    'core',
    'accounts',
    'patients',
    'tests',
    'reports',
]

MIDDLEWARE = [
    # Custom redirect interceptor for first-time configuration.
    # Placed at the top to prevent session/auth middlewares from triggering 
    # connection checks when database setup is incomplete.
    'core.middleware.UnilabSetupMiddleware',

    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'unilab_project.urls'

# Support both Jinja2 (for unmodified Flask templates) and standard Django template syntax
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.jinja2.Jinja2',
        'DIRS': [TEMPLATES_DIR],
        'APP_DIRS': True,
        'OPTIONS': {
            'environment': 'unilab_project.jinja2.environment',
        },
    },
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [TEMPLATES_DIR],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'unilab_project.wsgi.application'

# Dynamic MySQL Database Configuration Loader
# Resolves database credentials dynamically from local APPDATA storage 
# to ensure PyInstaller environment persistence.
MYSQL_HOST = 'localhost'
MYSQL_USER = 'root'
MYSQL_PASSWORD = ''
MYSQL_DB = 'diagnostic_lab'
IS_CONFIGURED = False

config_path = DB_CONFIG_FILE

if os.path.exists(config_path):
    try:
        with open(config_path, 'r') as f:
            data = json.load(f)
            MYSQL_HOST = data.get('host', 'localhost')
            MYSQL_USER = data.get('user', 'root')
            MYSQL_PASSWORD = data.get('password', '')
            MYSQL_DB = data.get('database', 'diagnostic_lab')
            
            # Check connection compatibility
            import mysql.connector
            conn = mysql.connector.connect(
                host=MYSQL_HOST,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                database=MYSQL_DB
            )
            conn.close()
            IS_CONFIGURED = True
    except Exception:
        IS_CONFIGURED = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': MYSQL_DB,
        'USER': MYSQL_USER,
        'PASSWORD': MYSQL_PASSWORD,
        'HOST': MYSQL_HOST,
        'PORT': '3306',
        'OPTIONS': {
            'charset': 'utf8mb4',
        }
    }
}

# Custom User Model & Authentication Backends
AUTH_USER_MODEL = 'accounts.User'

AUTHENTICATION_BACKENDS = [
    'accounts.backends.WerkzeugAuthBackend',
    'django.contrib.auth.backends.ModelBackend',
]

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'accounts.hashers.WerkzeugPasswordHasher', # Fallback bridging verification
]

# Password validation
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
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata' # Match local time representation
USE_I18N = True

# Disable timezone offset conversion to match legacy Flask local time lookups
# and prevent NULL exceptions on Windows MySQL timezone conversions
USE_TZ = False

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    STATIC_DIR,
]

# Media uploads (user profile photos)
MEDIA_URL = '/media/'
MEDIA_ROOT = MEDIA_DIR

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
