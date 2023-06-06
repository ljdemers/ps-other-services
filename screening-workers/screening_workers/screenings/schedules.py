"""Screening workers screenings schedules module"""
from celery.schedules import crontab

from screening_workers.screenings.tasks import (
    ScreeningsBulkScreenTask, ScreeningsBulkScreenKillerTask,
)


class ScreeningsBulkScreenSchedule:

    # Expires after 60 seconds
    expires = 60

    def __init__(self, task: ScreeningsBulkScreenTask, time: str):
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


class ScreeningsBulkScreenKillerSchedule:

    # Expires after 60 seconds
    expires = 60

    def __init__(self, task: ScreeningsBulkScreenKillerTask, time: str):
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
