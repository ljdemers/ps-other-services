from django.core.cache import cache

from sis_api.celery import app
from system.caches import HeartbeatCache


@app.task(ignore_result=True, queue='heartbeat')
def heartbeat():
    """
    Celery heartbeat task.
    """
    return HeartbeatCache(cache).update()
