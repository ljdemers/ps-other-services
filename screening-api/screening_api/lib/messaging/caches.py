from datetime import datetime


class TimestampCache(object):

    def __init__(self, cache, key, timeout=None):
        self.cache = cache
        self.key = key
        self.timeout = timeout

    def get(self):
        return self.cache.get(self.key)

    def update(self):
        data = self._get_data()
        self.cache.set(self.key, data, self.timeout)

    def _get_data(self):
        utcnow = datetime.utcnow()
        return {
            'timestamp': utcnow,
        }
