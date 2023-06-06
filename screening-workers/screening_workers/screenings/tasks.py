"""Screening workers screenings bulk tasks module"""
from celery import Task

from screening_api.screenings.repositories import ScreeningsRepository

from screening_workers.screenings.killers import ScreeningKiller
from screening_workers.screenings.schedulers import ScreeningScheduler


class ScreeningScreenTask(Task):

    name = 'screening.screenings.screen'

    def __init__(self, screening_scheduler: ScreeningScheduler):
        self.screening_scheduler = screening_scheduler

    def run(self, screening_id: int, *args, **kwargs):
        return self.screening_scheduler.schedule(screening_id)


class ScreeningScreenKillerTask(Task):

    name = 'screening.screenings.screen_killer'

    def __init__(self, screening_killer: ScreeningKiller):
        self.screening_killer = screening_killer

    def run(self, screening_id: int, *args, **kwargs):
        return self.screening_killer.kill(screening_id)


class ScreeningsBulkScreenTask(Task):

    name = 'screening.screenings.bulk_screen'

    def __init__(
            self,
            screenings_repository: ScreeningsRepository,
            screening_scheduler: ScreeningScheduler,
            task_time_limit=None,
            soft_time_limit=None
    ):
        self.screenings_repository = screenings_repository
        self.screening_scheduler = screening_scheduler
        self.time_limit = task_time_limit
        self.soft_time_limit = soft_time_limit

    def run(self, *args, **kwargs):
        screenings = self._find_screenings()

        for screening in screenings:
            self.screening_scheduler.schedule(screening.id)

    def _find_screenings(self):
        return self.screenings_repository.find()


class ScreeningsBulkScreenKillerTask(Task):

    name = 'screening.screenings.bulk_screen_killer'

    def __init__(
            self,
            screenings_repository: ScreeningsRepository,
            screening_killer: ScreeningKiller):
        self.screenings_repository = screenings_repository
        self.screening_killer = screening_killer

    def run(self, *args, **kwargs):
        screenings = self._find_screenings()

        for screening in screenings:
            self.screening_killer.kill(screening.id)

    def _find_screenings(self):
        return self.screenings_repository.find()
