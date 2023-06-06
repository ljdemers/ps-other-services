"""Screening workers ships tasks module"""
from typing import List

from celery import Task

from screening_api.ships.models import Ship
from screening_api.ships.repositories import ShipsRepository

from screening_workers.lib.sis_api.cache.collections import ShipsCollection

from screening_workers.ships.schedulers import ShipCacheUpdateScheduler


class ShipCacheUpdateTask(Task):

    name = 'screening.ships.ship_cache_update'

    def __init__(self, ships_collection: ShipsCollection):
        self.ships_collection = ships_collection

    def run(self, ship_id: int, *args, **kwargs):
        return self.ships_collection.refresh(ship_id)


class ShipsCacheUpdateTask(Task):

    name = 'screening.ships.ships_cache_update'

    def __init__(
            self, ships_repository: ShipsRepository,
            ship_cache_update_scheduler: ShipCacheUpdateScheduler,
    ):
        self.ships_repository = ships_repository
        self.ship_cache_update_scheduler = ship_cache_update_scheduler

    def run(self, *args, **kwargs):
        ships = self._find_ships()

        for ship in ships:
            self.ship_cache_update_scheduler.schedule(ship.id)

    def _find_ships(self) -> List[Ship]:
        return self.ships_repository.find()
