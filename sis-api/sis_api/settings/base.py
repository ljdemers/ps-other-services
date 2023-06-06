from __future__ import unicode_literals

import os
import sys

from sis_api.conf import load_ini_settings
from sis_api import __version__


PRODUCT = "SIS API"
VERSION = __version__

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../../')
)


# Specify 'FTP' as a default value to use old IHS settings
CONNECTOR_TYPE = os.getenv('CONNECTOR_TYPE', 'SFTP')
IHS_CACHE_DIR = '/opt/data'

# Old IHS settings (deprecated and not secure because FTP isn't encrypted)
OLD_IHS_HOST = 'ftp.lrfairplay.com'
OLD_IHS_USER = 'polestar'
OLD_IHS_PASSWORD = '23AdEPev'
OLD_IHS_PASSIVE_MODE = True
OLD_IHS_REMOTE_DIR = ''

OLD_IHS_REMOTE_HISTORICAL_DATA_DIR = '/historical data/'
OLD_IHS_REMOTE_MOVEMENTS_DIR = '/movements/aps/46223'

# New IHS settings (secure)
IHS_HOST = 'mft.ihsmarkit.com'
IHS_USER = 'srv_maruk_polestar'
IHS_PASSWORD = 'u76HX^cTuNGRqR9Mjmi'

IHS_REMOTE_MOVEMENTS_DIR = '/Movements/APS/46223'

REDIS_HOST = 'localhost'
REDIS_PORT = '6379'
REDIS_DB = '0'

DEBUG = False

ADMINS = (
    ('Admin & Devs', 'sis-dev+test@polestarglobal.com'),
)
MANAGERS = ADMINS

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

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'

TIME_ZONE = 'Etc/UTC'
LANGUAGE_CODE = 'en-gb'
SITE_ID = 1
USE_I18N = True
USE_L10N = True
USE_TZ = True
MEDIA_ROOT = ''
MEDIA_URL = ''

SYSTEM_STATUS = {
    "NginX": "system.checks.NginxProcessCheck",
    "Database Check": "system.checks.DatabaseCheck",
    "uWsgi": "system.checks.UwsgiProcessCheck",
    "celerybeat": "system.checks.CeleryBeatCheck",
    "celeryd": "system.checks.CelerydProcessCheck",
    "failed load": "system.checks.FailedLoadHistoryCheck",
    "broker": "system.checks.CeleryBrokerConnectionCheck",
}

SYSTEM_STATUS_CACHE_TIMEOUT = 10

# in seconds
FAILED_LOADS_CHECK_TIME_RANGE = 48 * 60 * 60

STATIC_ROOT = os.path.join(PROJECT_ROOT, 'static')
STATIC_URL = '/static/'
STATICFILES_DIRS = []
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

SECRET_KEY = ')-qni9+6-oc9s&amp;h*2ogx&amp;mng!+5^ypp(*4=b3nf5dii5wk+mt@'

MIDDLEWARE = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'easyaudit.middleware.easyaudit.EasyAuditMiddleware',
)

ROOT_URLCONF = 'sis_api.urls'
WSGI_APPLICATION = 'sis_api.wsgi.application'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(PROJECT_ROOT, 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
            ],
            'debug': DEBUG,
        },
    }
]

INSTALLED_APPS = (
    # Django.
    'django.contrib.auth',
    'django.contrib.admin',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admindocs',
    'django.contrib.sites',
    'django_celery_beat',

    # 3rd party apps and libraries.
    'raven.contrib.django.raven_compat',
    'tastypie',
    'easyaudit',

    # Project apps.
    'ships',
    'ports',
    'system',
    'sis_api',
)

# Apps that will be registered in the django admin
ADMIN_APPS = (
    'django.contrib.auth',
    'ships',
    'ports',
    'tastypie',
)

# TASTYPIE_SWAGGER_API_MODULE = 'sis_api.urls.api'

CELERY_TIMEZONE = 'UTC'
CELERY_HIJACK_ROOT_LOGGER = False
IMPORT_TIME_LIMIT = 40 * 60 * 60  # 40h

TASTYPIE_ALLOW_MISSING_SLASH = True
APPEND_SLASH = True
TASTYPIE_DEFAULT_FORMATS = ['json']


LOG_FILE_PATH = '/var/log/sis-api/'

# Sentry Service configuration (this must be BEFORE `load_ini_settings`).
RAVEN_DSN = ''


ALLOWED_HOSTS = ['*']

load_ini_settings(
    "/etc/polestar/sis.ini",
    settings_object=sys.modules[__name__],
)

# Sentry connection (this must be AFTER `load_ini_settings`).
if RAVEN_DSN:
    RAVEN_CONFIG = {
        'dsn': RAVEN_DSN,
        'release': VERSION,
    }

BROKER_URL = 'redis://{0}:{1}/2'.format(REDIS_HOST, REDIS_PORT)
CELERY_BROKER_URL = 'amqp://guest:guest@localhost:5672/'
CELERY_RESULT_BACKEND = 'amqp://guest:guest@localhost:5672/'

CACHE_TTL = 60 * 10

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://{0}:{1}/1'.format(REDIS_HOST, REDIS_PORT),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

LOG_FILE_NAME = os.path.join(LOG_FILE_PATH, 'django.log')
LOG_FILE_NAME_DB = os.path.join(LOG_FILE_PATH, 'django.db.log')
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': "%(asctime)s %(levelname)s [%(name)s:%(lineno)s] "
                      "%(message)s",
            'datefmt': "%Y-%m-%d %H:%M:%S"
        },
        'celery': {
            'format': "[%(asctime)s %(levelname)s/%(processName)s] %(message)s",
            'datefmt': "%Y-%m-%d %H:%M:%S"
        }
    },
    'handlers': {
        'logfile': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_FILE_NAME,
            'maxBytes': 50000,
            'backupCount': 5,
            'formatter': 'standard',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'standard'
        },
        'celery_console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'celery'
        },
        'logfile_db': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_FILE_NAME_DB,
            'maxBytes': 1000000,
            'backupCount': 5,
            'formatter': 'standard',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['logfile'],
            'propagate': True,
            'level': 'WARN',
        },
        'celery': {
            'handlers': ['celery_console'],
            'propagate': True,
            'level': 'INFO',
        },
        'sis_api': {
            'handlers': ['logfile'],
            'level': 'INFO',
        },
        'ships': {
            'handlers': ['logfile'],
            'level': 'INFO',
            'propagate': False,
        },
        'ports': {
            'handlers': ['logfile'],
            'level': 'INFO',
            'propagate': False,
        },
        'management': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.db.backends': {
            'level': 'INFO',
            'propagate': True,
            'handlers': ['logfile_db', 'console'],
        },
        'system': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    }
}

# EasyAudit configuration, we want to watch only changes in models.
DJANGO_EASY_AUDIT_WATCH_AUTH_EVENTS = False
DJANGO_EASY_AUDIT_WATCH_REQUEST_EVENTS = False
DJANGO_EASY_AUDIT_REGISTERED_CLASSES = [
    'ships.MMSIHistory', 'ships.ShipMovement']


# Globavista export settings
GLOBAVISTA_EXPORT_ENABLED = bool(
    os.environ.get('GLOBAVISTA_EXPORT_ENABLED', False)
)
GLOBAVISTA_EXPORT_FILE_PATTERN = str(
    os.environ.get(
        'GLOBAVISTA_EXPORT_FILE_PATTERN',
        '/tmp/IHS_ShipData_%Y-%m-%d.csv'
    )
)
GLOBAVISTA_EXPORT_S3_BUCKET = str(
    os.environ.get('GLOBAVISTA_EXPORT_S3_BUCKET', '')
)
GLOBAVISTA_EXPORT_S3_KEY_PREFIX = str(
    os.environ.get('GLOBAVISTA_EXPORT_S3_KEY_PREFIX', '')
)
