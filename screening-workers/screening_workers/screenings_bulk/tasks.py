"""Screening workers screenings bulk tasks module"""
from celery import Task

from screening_workers.screenings.creators import ScreeningsCreator


class BulkScreeningValidationTask(Task):

    name = 'screening.bulk_screenings.validation'

    def __init__(self, screenings_creator: ScreeningsCreator):
        self.screenings_creator = screenings_creator

    def run(self, bulk_screening_id: int, *args, **kwargs):
        return self.screenings_creator.create(bulk_screening_id)
