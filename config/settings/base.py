import environ
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DEBUG=(bool, True),
)

env_files = [
    Path.home() / '.env',
    BASE_DIR / '.env',
    Path(os.environ['ENV_FILE']) if os.environ.get('ENV_FILE') else None,
]

for env_file in env_files:
    if env_file and env_file.exists():
        environ.Env.read_env(str(env_file), overwrite=True)

SECRET_KEY = env('SECRET_KEY', default='django-insecure-change-me-in-production')

DEBUG = env('DEBUG', default=True)

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    'django_htmx',
    'cloudinary_storage',
    'cloudinary',

    'allauth',
    'allauth.account',
    'allauth.socialaccount',

    'apps.accounts',
    'apps.tasks',
    'apps.messaging',
    'apps.reputation',
    'apps.badges',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django_htmx.middleware.HtmxMiddleware',
]

ROOT_URLCONF = 'config.urls'

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
                'apps.accounts.context_processors.review_notifications',
                'apps.accounts.context_processors.unread_counts',
                'apps.accounts.context_processors.firebase_settings',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

AUTH_USER_MODEL = 'accounts.CustomUser'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

ACCOUNT_ADAPTER = 'apps.accounts.adapters.AccountAdapter'
SOCIALACCOUNT_ADAPTER = 'apps.accounts.adapters.SocialAccountAdapter'

ACCOUNT_USER_MODEL_USERNAME_FIELD = 'email'
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
ACCOUNT_SIGNUP_REDIRECT_URL = 'accounts:social_complete'
SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True

FIREBASE_APP_NAME = 'sidequest'
FIREBASE_SERVICE_ACCOUNT_PATH = env('FIREBASE_SERVICE_ACCOUNT_PATH', default='')
FIREBASE_API_KEY = env('FIREBASE_API_KEY', default='')
FIREBASE_AUTH_DOMAIN = env('FIREBASE_AUTH_DOMAIN', default='')
FIREBASE_PROJECT_ID = env('FIREBASE_PROJECT_ID', default='')
FIREBASE_STORAGE_BUCKET = env('FIREBASE_STORAGE_BUCKET', default='')
FIREBASE_MESSAGING_SENDER_ID = env('FIREBASE_MESSAGING_SENDER_ID', default='')
FIREBASE_APP_ID = env('FIREBASE_APP_ID', default='')
GOOGLE_CLIENT_ID = env('GOOGLE_CLIENT_ID', default='')
GOOGLE_CLIENT_SECRET = env('GOOGLE_CLIENT_SECRET', default='')
GOOGLE_REDIRECT_URI = env('GOOGLE_REDIRECT_URI', default='http://localhost:8000/accounts/google/callback/')

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'fr'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

CLOUDINARY_CLOUD_NAME = env('CLOUDINARY_CLOUD_NAME', default='')
if CLOUDINARY_CLOUD_NAME and CLOUDINARY_CLOUD_NAME != 'your-cloud-name':
    DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
    CLOUDINARY_STORAGE = {
        'CLOUD_NAME': CLOUDINARY_CLOUD_NAME,
        'API_KEY': env('CLOUDINARY_API_KEY', default=''),
        'API_SECRET': env('CLOUDINARY_API_SECRET', default=''),
    }

LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'home'

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST', default='localhost')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@sidequest.app')
SITE_URL = env('SITE_URL', default='http://localhost:8000')

REDIS_URL = env('REDIS_URL', default='redis://localhost:6379/0')

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': REDIS_URL,
    }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

MESSAGE_TAGS = {
    'debug': 'info',
    'info': 'info',
    'success': 'success',
    'warning': 'warning',
    'error': 'error',
}

CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[])
