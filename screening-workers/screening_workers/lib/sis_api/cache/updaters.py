"""Screening Workers ship inspections cache updaters module"""
from collections import deque
from datetime import datetime, timedelta
from functools import partial

from beaker.cache import Cache
from redlock.lock import RedLockFactory
from sqlalchemy.exc import IntegrityError

from screening_api.ships.models import Ship
from screening_api.ships.repositories import ShipsRepository
from screening_api.ship_inspections.repositories import (
    ShipInspectionsRepository,
)

from screening_workers.lib.screening.cache.updaters import BaseShipCacheUpdater
from screening_workers.lib.sis_api.collections import (
    ShipsCollection, ShipInspectionsCollection,
)
from screening_workers.lib.sis_api.models import ShipInspection

from screening_workers.ships.upserters import ShipsUpserter


class ShipUpdater(BaseShipCacheUpdater):

    UPDATE_INTERVAL = 86400  # seconds

    lock_name_prefix = 'ship_update'

    def __init__(
            self,
            ships_repository: ShipsRepository,
            ship_update_cache: Cache,
            locker: RedLockFactory,
            ships_collection: ShipsCollection,
            ships_upserter: ShipsUpserter,
    ):
        super(ShipUpdater, self).__init__(
            ships_repository, ship_update_cache, locker)
        self.ships_collection = ships_collection
        self.ships_upserter = ships_upserter

    def process_ship(self, ship: Ship) -> None:
        ships = self.ships_collection.query(imo_id=ship.imo_id)

        if not ships:
            return

        self._update_ship(ship.id, ships[0])

    def _update_ship(self, ship_id: int, ship_data):
        self.ships_upserter.upsert(ship_data)


class ShipInspectionsUpdater(BaseShipCacheUpdater):

    UPDATE_INTERVAL = 3600  # seconds
    HISTORY_SIZE = 720  # days

    lock_name_prefix = 'ship_inspections_update'

    def __init__(
            self,
            ships_repository: ShipsRepository,
            ship_inspections_update_cache: Cache,
            locker: RedLockFactory,
            ship_inspections_collection: ShipInspectionsCollection,
            ship_inspections_repository: ShipInspectionsRepository,
    ):
        super(ShipInspectionsUpdater, self).__init__(
            ships_repository, ship_inspections_update_cache, locker)
        self.ship_inspections_collection = ship_inspections_collection
        self.ship_inspections_repository = ship_inspections_repository

    def process_ship(self, ship: Ship) -> None:
        # @todo: add greater than date filter support in sis
        # last_inspection_date = self._get_last_inspection_date(ship_id)
        inspections = self.ship_inspections_collection.query(
            imo_id=ship.imo_id)

        if not inspections:
            return

        create_func = partial(self._create_inspection, ship.id)
        deque(map(create_func, inspections))

    def _get_last_inspection_date(self, ship_id: int) -> datetime:
        last_inspection = self.ship_inspections_repository.find(
            ship_id=ship_id, limit=1)

        if not last_inspection:
            return datetime.utcnow() - timedelta(days=self.HISTORY_SIZE)

        return last_inspection[0].inspection_date

    def _create_inspection(
            self, ship_id: int, inspection: ShipInspection) -> None:
        detained_days = inspection.number_part_days_detained
        if detained_days is None:
            detained_days = 0.0

        defects_count = inspection.no_defects
        if defects_count is None:
            defects_count = 0

        data = {
            'inspection_id': inspection.inspection_id,
            'inspection_date': inspection.inspection_date,
            'authority': inspection.authorisation,
            'defects_count': defects_count,
            'detained': inspection.detained,
            'detained_days': detained_days,
            'port_name': inspection.port_name,
            'country_name': inspection.country_name,
        }

        # we don't use optimistic pattern coz of used lock
        inspection = self.ship_inspections_repository.get_or_none(
            inspection_id=inspection.inspection_id)

        if inspection is not None:
            return

        try:
            self.ship_inspections_repository.create(ship_id, **data)
        # inspection already exists
        except IntegrityError:
            pass
