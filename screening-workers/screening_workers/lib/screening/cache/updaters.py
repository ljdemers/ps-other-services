from beaker.cache import Cache
from redlock.lock import RedLockFactory
from sqlalchemy.orm.session import Session

from screening_api.companies.models import SISCompany
from screening_api.companies.repositories import SISCompaniesRepository
from screening_api.ships.models import Ship
from screening_api.ships.repositories import ShipsRepository

from screening_workers.lib.api.cache.updaters import BaseCacheUpdater


class BaseShipCacheUpdater(BaseCacheUpdater):

    lock_name_prefix = 'ship'

    def __init__(
            self,
            ships_repository: ShipsRepository,
            update_cache: Cache,
            locker: RedLockFactory,
    ):
        super().__init__(update_cache, locker)
        self.ships_repository = ships_repository

    def process(self, item_id: int) -> None:
        ship = self._get_ship(item_id)

        self.process_ship(ship)

    def process_ship(self, ship: Ship) -> None:
        raise NotImplementedError

    def _get_ship(self, ship_id: int) -> Ship:
        return self.ships_repository.get(id=ship_id)


class BaseCompanyCacheUpdater(BaseCacheUpdater):

    lock_name_prefix = 'company'

    def __init__(
            self,
            update_cache: Cache,
            locker: RedLockFactory,
            companies_repository: SISCompaniesRepository,
    ):
        super().__init__(update_cache, locker)
        self.companies_repository = companies_repository

    def get_session(self):
        return self.companies_repository.get_session()

    def process(self, item_id: int) -> None:
        session = self.get_session()
        company = self._get_company(item_id, session=session)

        self.process_company(company, session=session)

    def process_company(
            self, company: SISCompany, session: Session = None) -> None:
        raise NotImplementedError

    def _get_company(
            self, company_id: int, session: Session = None) -> SISCompany:
        return self.companies_repository.get(id=company_id, session=session)
