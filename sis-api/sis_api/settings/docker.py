# pylint: disable=wildcard-import,unused-wildcard-import
from sis_api.settings.base import *


DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'sis',
        'USER': 'sis',
        'PASSWORD': 'sis',
        'HOST': 'sis-api-postgres',
        'PORT': '5432',
    }
}

REDIS_HOST = 'api-redis'
REDIS_PORT = '6379'
REDIS_DB = '0'
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://{0}:{1}/1'.format(REDIS_HOST, REDIS_PORT),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PASSWORD': ""
        }
    }
}

CELERY_ALWAYS_EAGER = True
BROKER_URL = 'redis://{0}:{1}/2'.format(REDIS_HOST, REDIS_PORT)
CELERY_BROKER_URL = BROKER_URL

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
        },
        'system': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    }
}
