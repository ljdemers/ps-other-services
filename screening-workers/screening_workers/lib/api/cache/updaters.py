from datetime import datetime, timedelta

from beaker.cache import Cache
from redlock.lock import RedLockFactory, RedLock


class BaseCacheUpdater:

    UPDATE_INTERVAL = 3600  # seconds

    lock_name_prefix = NotImplemented

    def __init__(
            self,
            update_cache: Cache,
            locker: RedLockFactory,
    ):
        self.update_cache = update_cache
        self.locker = locker

    def update(self, item_id: int):
        lock = self._get_lock(item_id)
        lock.acquire()

        now = datetime.utcnow()
        if not self._is_interval_passed(item_id, now):
            return

        self.process(item_id)

        self._set_last_update_date(item_id, now)

        lock.release()

    def process(self, item_id: int) -> None:
        raise NotImplementedError

    def _get_lock_name(self, item_id: int) -> str:
        return '{0}_{1}'.format(self.lock_name_prefix, item_id)

    def _get_lock(self, item_id: int) -> RedLock:
        lock_name = self._get_lock_name(item_id)
        return self.locker.create_lock(lock_name)

    def _get_cache_key(self, item_id: int) -> str:
        return str(item_id)

    def _get_last_update_date(self, item_id: int) -> datetime:
        cache_key = self._get_cache_key(item_id)
        return self.update_cache.get_value(
            cache_key, createfunc=lambda: datetime(1890, 1, 1))

    def _set_last_update_date(self, item_id: int, last_update_date: datetime):
        cache_key = self._get_cache_key(item_id)
        return self.update_cache.put(cache_key, last_update_date)

    def _get_next_update_date(self, last_update_date: datetime) -> datetime:
        if last_update_date is None:
            return datetime.utcnow()

        return last_update_date + timedelta(seconds=self.UPDATE_INTERVAL)

    def _is_interval_passed(
            self, item_id: int, current_date: datetime) -> bool:
        last_update_date = self._get_last_update_date(item_id)
        if last_update_date is None:
            return True

        next_update_date = self._get_next_update_date(last_update_date)
        return current_date > next_update_date
