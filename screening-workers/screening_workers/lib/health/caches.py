from datetime import datetime

from redbeat import RedBeatSchedulerEntry
from redbeat.decoder import from_timestamp
from redbeat.schedulers import redis

from screening_api.lib.messaging.caches import TimestampCache

from screening_workers import __version__


class HeartbeatCache(TimestampCache):

    def __init__(self, cache, key, *indicators):
        self.cache = cache
        self.key = key
        self.indicators = indicators

    def update(self, hostname):
        data = self._get_data(hostname)
        self.cache.put(self.key, data)

    def _get_app(self):
        from celery.task.control import inspect

        inspect_obj = inspect()

        return inspect_obj.app

    def _get_data(self, hostname, *indicators):
        app = self._get_app()

        utcnow = datetime.utcnow()
        tasks = list(app.tasks.keys())
        tasks.sort()
        entries = self._get_entries(app)
        schedules = [
            {
                'task': entry.task,
                'total_run_count': entry.total_run_count,
                'last_run_at': entry.last_run_at,
                'due_at': entry.due_at,
            }
            for entry, due in entries
        ]
        healths = list(map(lambda x: x.health(), self.indicators))
        services = list(map(lambda x: x.__json__(), healths))
        return {
            'timestamp': utcnow,
            'hostname': hostname,
            'tasks': tasks,
            'schedules': schedules,
            'version': __version__,
            'services': services,
        }

    def _get_keys(self, app):
        client = redis(app)
        for key, ts in client.zscan_iter(app.redbeat_conf.schedule_key):
            yield key, from_timestamp(ts)

    def _get_entries(self, app):
        for key, due in self._get_keys(app):
            try:
                yield RedBeatSchedulerEntry.from_key(key, app=app), due
            except KeyError:
                continue
