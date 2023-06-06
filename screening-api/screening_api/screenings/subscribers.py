"""Screening API screenings subscribers module"""
import logging
from typing import List

from screening_api.lib.messaging.publishers import CeleryTaskPublisher
from screening_api.screenings.models import Screening
from screening_api.screenings.repositories import ScreeningsRepository

log = logging.getLogger(__name__)


class ScreeningsScreenSubscriber(object):

    name = 'screening.screenings.screen'

    def __init__(self, publisher: CeleryTaskPublisher):
        self.publisher = publisher

    def __call__(
            self,
            sender: ScreeningsRepository,
            instances: List[Screening],
    ):
        for instance in instances:
            self.publisher.publish(self.name, instance.id)
