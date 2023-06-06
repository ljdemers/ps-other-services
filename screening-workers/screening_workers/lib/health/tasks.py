from screening_workers.lib.messaging.tasks import CacheUpdateTask


class HeartbeatTask(CacheUpdateTask):

    name = 'heartbeat'
