# pylint: disable=wildcard-import,unused-wildcard-import
from .base import *


DEBUG = True

ALLOWED_HOSTS.append('localhost')

# Development local default databases. Set up local PostgreSQL for it if needed.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'sis_api',
        'USER': 'postgres',
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': '5432',
    },
}


# Local memory cache.
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}


# Dummy email backend.
EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'


# Development logging. Only stdout. No hard-disk file writing.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] "
                      "%(message)s",
            'datefmt': "%d/%b/%Y %H:%M:%S"
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'standard'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'propagate': True,
            'level': 'INFO',
        },
        'celery': {
            'handlers': ['console'],
            'propagate': True,
            'level': 'DEBUG',
        },
        'sis_api': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'ships': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'ports': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'management': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'system': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    }
}

# Override settings with local box settings for dev environment customization.
try:
    from .local_settings import *
except ImportError as e:
    print('No custom local settings imported: ', e)
