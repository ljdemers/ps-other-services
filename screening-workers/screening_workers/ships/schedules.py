"""Screening workers ships schedules module"""
from celery.schedules import crontab

from screening_workers.ships.tasks import ShipsCacheUpdateTask


class ShipsCacheUpdateSchedule:

    # Expires after 60 seconds
    expires = 60

    def __init__(self, task: ShipsCacheUpdateTask, time: str):
        self.task = task
        self.time = time

    @property
    def time_tuple(self):
        return self.time.split()

    @property
    def frequency(self):
        return crontab(*self.time_tuple)

    def setup(self, sender, **kwargs):
        sender.add_periodic_task(
            self.frequency, self.task.s(),
            name=self.task.name, expires=self.expires,
        )
