from celery.schedules import crontab

from screening_workers.lib.health.tasks import HeartbeatTask


class HeartbeatSchedule:

    # Calls task every minute
    time = crontab()
    expires = 120

    def __init__(self, task: HeartbeatTask):
        self.task = task

    def setup(self, sender, **kwargs):
        sender.add_periodic_task(
            self.time, self.task.s(), expires=self.expires)
