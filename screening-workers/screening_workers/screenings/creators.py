"""Screening workers screenings creators module"""
import logging

from sqlalchemy.orm.scoping import scoped_session
from sqlalchemy.orm.session import Session

from screening_api.screenings.models import Screening
from screening_api.screenings.repositories import ScreeningsRepository
from screening_api.screenings_bulk.enums import BulkScreeningStatus
from screening_api.screenings_bulk.models import BulkScreening
from screening_api.screenings_bulk.repositories import BulkScreeningsRepository
from screening_api.ships.models import Ship
from screening_api.ships.repositories import ShipsRepository

from screening_workers.lib.sis_api.models import Ship as SISShip
from screening_workers.lib.sis_api.collections import ShipsCollection
from screening_workers.screenings.signals import post_create_screening
from screening_workers.ships.upserters import ShipsUpserter

log = logging.getLogger(__name__)


class ScreeningsCreator:

    def __init__(
            self, ships_collection: ShipsCollection,
            bulk_screenings_repository: BulkScreeningsRepository,
            screenings_repository: ScreeningsRepository,
            ships_repository: ShipsRepository,
            ships_upserter: ShipsUpserter,
            session_factory: scoped_session):
        self.ships_collection = ships_collection
        self.screenings_repository = screenings_repository
        self.bulk_screenings_repository = bulk_screenings_repository
        self.ships_repository = ships_repository
        self.ships_upserter = ships_upserter
        self.session_factory = session_factory

    def get_session(self) -> Session:
        return self.session_factory()

    def create(self, bulk_screening_id):
        bulk_screening = self._get_bulk_screening(bulk_screening_id)
        self._set_bulk_screening_pending(bulk_screening_id)

        ship = self._get_ship_or_none(bulk_screening.imo_id)
        ship_data = None
        if ship is None:
            ship_data = self._get_ship_data_or_none(bulk_screening.imo_id)

        if ship is None and ship_data is None:
            # no ship data found for screening
            log.warning(
                'No ship data found for screening: %s',
                bulk_screening.id
            )
            self._set_bulk_screening_invalid(bulk_screening.id)
            return

        screening = None
        if ship is not None:
            screening = self._get_screening_or_none(
                bulk_screening.account_id, ship.id)

        if ship is not None and screening is not None:
            # screening for user already exist
            log.warning(
                'Screening <%s> for user already exist',
                bulk_screening.id
            )
            self._set_bulk_screening_ok(bulk_screening.id)
            post_create_screening.send(self.__class__, instance=screening)
            log.info(
                'Started screening: %s',
                screening.id
            )
            return

        session = self.get_session()
        session.begin()
        try:
            if ship is None:
                ship = self._create_ship(ship_data, session=session)

            screening = self._create_screening(
                bulk_screening.account_id, ship.id, session=session)
            self._set_bulk_screening_ok(
                bulk_screening.id, session=session)
            log.info(
                'Created bulk screening: %s',
                bulk_screening.id
            )
        # @todo: narrow exceptions
        except:
            session.rollback()
            self._set_bulk_screening_invalid(bulk_screening.id)
            log.warning(
                'Could not complete bulk screening: %s',
                bulk_screening.id
            )
        else:
            session.commit()
            post_create_screening.send(self.__class__, instance=screening)
            log.info(
                'Started screening: %s',
                screening.id
            )

    def _get_bulk_screening(self, bulk_screening_id: int) -> BulkScreening:
        return self.bulk_screenings_repository.get(id=bulk_screening_id)

    def _get_screening_or_none(self, account_id, ship_id) -> Screening:
        return self.screenings_repository.get_or_none(
            account_id=account_id, ship_id=ship_id)

    def _get_ship_or_none(self, imo_id) -> Ship:
        return self.ships_repository.get_or_none(imo_id=imo_id)

    def _get_ship_data_or_none(self, imo_id) -> SISShip:
        try:
            ships = self.ships_collection.query(imo_id=imo_id)
        # @todo: narrow exceptions
        except:
            return None

        try:
            return ships[0]
        # empty list
        except IndexError:
            return None

    def _create_ship(self, ship_data: SISShip, session: Session) -> Ship:
        ship, _ = self.ships_upserter.upsert(ship_data, session)
        return ship

    def _create_screening(
            self, account_id, ship_id, session: Session) -> Screening:
        return self.screenings_repository.create(
            account_id=account_id, ship_id=ship_id, session=session)

    def _set_bulk_screening_pending(self, bulk_screening_id):
        return self.bulk_screenings_repository.update(
            bulk_screening_id, status=BulkScreeningStatus.PENDING)

    def _set_bulk_screening_ok(
            self, bulk_screening_id, session: Session = None):
        return self.bulk_screenings_repository.update(
            bulk_screening_id,
            status=BulkScreeningStatus.DONE, result=True, session=session,
        )

    def _set_bulk_screening_invalid(self, bulk_screening_id):
        return self.bulk_screenings_repository.update(
            bulk_screening_id, status=BulkScreeningStatus.DONE, result=False)
