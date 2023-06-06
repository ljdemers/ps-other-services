from screening_api.ships.repositories import ShipsRepository
from screening_api.ship_inspections.repositories import (
    ShipInspectionsRepository,
)

from screening_workers.lib.api.cache.collections import BaseCachedCollection
from screening_workers.lib.sis_api.cache.updaters import (
    ShipUpdater, ShipInspectionsUpdater,
)


class ShipsCollection(BaseCachedCollection):

    def __init__(
            self,
            ships_repository: ShipsRepository,
            ship_updater: ShipUpdater,
    ):
        self.ships_repository = ships_repository
        self.ship_updater = ship_updater

    def invalidate(self, ship_id):
        raise NotImplementedError

    def refresh(self, ship_id):
        return self.ship_updater.update(ship_id)

    def get(self, ship_id, **kwargs):
        self.refresh(ship_id)
        # always use cache
        return self.ships_repository.get(id=ship_id, **kwargs)


class ShipInspectionsCollection(BaseCachedCollection):

    def __init__(
            self,
            ship_inspections_repository: ShipInspectionsRepository,
            ship_inspections_updater: ShipInspectionsUpdater,
    ):
        self.ship_inspections_repository = ship_inspections_repository
        self.ship_inspections_updater = ship_inspections_updater

    def invalidate(self, ship_id):
        return self.ship_inspections_repository.delete(ship_id=ship_id)

    def refresh(self, ship_id):
        return self.ship_inspections_updater.update(ship_id)

    def query(self, ship_id):
        self.refresh(ship_id)
        # always use cache
        return self.ship_inspections_repository.find(
            ship_id=ship_id, sort=['-inspection_date'])
