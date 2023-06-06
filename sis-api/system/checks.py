import logging
from datetime import timedelta, datetime

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from ships.models import LoadHistory
from system.caches import HeartbeatCache
from sis_api import celery
from sis_api.utils import (
    ProcessCheck,
    SystemCheck
)

log = logging.getLogger(__name__)


def handle_exceptions(f):
    def wrapper(*args, **kw):
        try:
            return f(*args, **kw)
        except Exception as exc:
            log.exception('Method %s raised exception %s', f, exc)
            return False
    return wrapper


class NginxProcessCheck(ProcessCheck):
    process_name = 'nginx'


class UwsgiProcessCheck(ProcessCheck):
    process_name = 'uwsgi'


class CelerydProcessCheck(ProcessCheck):
    process_name = 'celeryd'


class DatabaseCheck(SystemCheck):
    """Database Check Class."""
    def run(self):
        database = 'OK'

        try:
            # If that won't throw exception it means that we have connection
            # to the database and we can execute query
            LoadHistory.objects.first()
        except Exception:
            database = 'ERROR'

        return database


class CeleryBeatCheck(SystemCheck):

    treshold = timedelta(minutes=10)

    def run(self):
        heartbeat = HeartbeatCache(cache).get()
        if heartbeat is None:
            return 'ERROR'

        now = datetime.utcnow()
        if now - heartbeat > self.treshold:
            return 'ERROR'

        return 'OK'


class CeleryBrokerConnectionCheck(SystemCheck):

    @property
    def app(self):
        return celery.app

    def run(self):
        """Run the check."""
        try:
            inspector = self.app.control.inspect()
            inspector.ping()
        except Exception:  # pylint: disable=broad-except
            return 'ERROR'
        else:
            return 'OK'


class FailedLoadHistoryCheck(SystemCheck):

    def run(self):
        """Returns ERROR if last load status within 48h
        (FAILED_LOADS_CHECK_TIME_RANGE) failed"""
        seconds = settings.FAILED_LOADS_CHECK_TIME_RANGE
        dt = timezone.now() - timedelta(seconds=seconds)
        result = LoadHistory.objects.order_by('-started_date').first()
        if not result:
            log.warning("there are no LoadHistory objects")
            return 'ERROR'
        elif result.status == LoadHistory.FAILED:
            # The last data load didn't succeed
            return 'WARNING'
        elif result.started_date < dt:
            return 'WARNING'
        else:
            return 'OK'
