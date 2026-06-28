from .base import *  # noqa: F401,F403

DEBUG = False

ALLOWED_HOSTS = ['KaynBricool.pythonanywhere.com', 'www.kaynbricool.com', 'kaynbricool.com']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.db'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

SECURE_SSL_REDIRECT = False

CSRF_TRUSTED_ORIGINS = [
    'https://KaynBricool.pythonanywhere.com',
    'https://www.kaynbricool.com',
    'https://kaynbricool.com',
]
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
}
