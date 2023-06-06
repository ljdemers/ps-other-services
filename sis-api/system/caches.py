from datetime import datetime


class HeartbeatCache(object):
    """
    Heartbeat cache class.
    """

    cache_key = 'heartbeat'

    def __init__(self, cache):
        self.cache = cache

    def get(self):
        """
        Returns latest cached heartbeat.
        """
        return self.cache.get(self.cache_key)

    def update(self):
        """
        Updates heartbeat cache.
        """
        value = self._get()
        self.cache.set(self.cache_key, value)

    def _get(self):
        return datetime.utcnow()
