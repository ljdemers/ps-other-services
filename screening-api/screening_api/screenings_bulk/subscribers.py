"""Screening API screenings bulk subscribers module"""
import logging
from typing import List

from screening_api.lib.messaging.publishers import CeleryTaskPublisher
from screening_api.screenings_bulk.models import BulkScreening
from screening_api.screenings_bulk.repositories import BulkScreeningsRepository

log = logging.getLogger(__name__)


class BulkScreeningsValidationSubscriber(object):

    name = 'screening.bulk_screenings.validation'

    def __init__(self, publisher: CeleryTaskPublisher):
        self.publisher = publisher

    def __call__(
            self,
            sender: BulkScreeningsRepository,
            instances: List[BulkScreening],
    ):
        for instance in instances:
            self.publisher.publish(self.name, instance.id)
