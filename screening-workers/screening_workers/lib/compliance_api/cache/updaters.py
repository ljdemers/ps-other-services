"""Screening Workers ship sanctions cache updaters module"""
from collections import deque
from functools import partial
import logging

from beaker.cache import Cache
from redlock.lock import RedLockFactory
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.session import Session

from screening_api.ships.models import Ship
from screening_api.ships.repositories import ShipsRepository
from screening_api.ship_sanctions.repositories import (
    ShipSanctionsRepository,
)
from screening_api.companies.models import SISCompany
from screening_api.companies.repositories import SISCompaniesRepository
from screening_api.company_associations.repositories import (
    CompanyAssociationsRepository,
)
from screening_api.entities.enums import EntityType
from screening_api.entities.repositories import (
    ComplianceEntitiesRepository,
)
from screening_api.sanctions.repositories import (
    ComplianceSanctionsRepository, ComplianceEntitySanctionsRepository,
)
from screening_api.screenings.enums import Severity

from screening_workers.lib.screening.cache.updaters import (
    BaseShipCacheUpdater, BaseCompanyCacheUpdater,
)
from screening_workers.lib.compliance_api.collections import (
    ShipsCollection, OrganisationNamesCollection,
)
from screening_workers.lib.compliance_api.models import (
    Entity, EntitySanction, EntityAssociation,
)

log = logging.getLogger(__name__)


class ShipSanctionsUpdater(BaseShipCacheUpdater):

    UPDATE_INTERVAL = 3600  # seconds
    HISTORY_SIZE = 720  # days

    lock_name_prefix = 'ship_sanctions_update'

    def __init__(
            self,
            ships_repository: ShipsRepository,
            update_cache: Cache,
            locker: RedLockFactory,
            ships_collection: ShipsCollection,
            ship_sanctions_repository: ShipSanctionsRepository,
    ):
        super(ShipSanctionsUpdater, self).__init__(
            ships_repository, update_cache, locker)
        self.ships_collection = ships_collection
        self.ship_sanctions_repository = ship_sanctions_repository

    def process_ship(self, ship: Ship) -> None:
        # @todo: add greater than date filter support in sis
        # last_inspection_date = self._get_last_inspection_date(ship_id)
        ships = self.ships_collection.query(imo_number=ship.imo_id, limit=1)

        if not ships:
            return

        compliance_ship = ships[0]

        create_func = partial(self._create_sanction, ship.id)
        deque(map(create_func, compliance_ship.ship_sanctions))

    def _create_sanction(
            self, ship_id: int, entity_sanction: EntitySanction) -> None:
        # we don't use optimistic pattern coz of used lock
        sanction_list_name = entity_sanction.sanction.name
        sanction = self.ship_sanctions_repository.get_or_none(
            ship_id=ship_id, sanction_list_name=sanction_list_name)

        is_active = entity_sanction.status.lower() == 'active'
        data = {
            'code': entity_sanction.sanction.code,
            'sanction_list_name': sanction_list_name,
            'start_date': entity_sanction.since_date,
            'end_date': entity_sanction.to_date,
            'is_active': is_active,
        }

        if sanction is not None:
            self.ship_sanctions_repository.update(sanction, **data)
            return

        try:
            self.ship_sanctions_repository.create(ship_id, **data)
        # inspection already exists
        except IntegrityError:
            pass


class CompanySanctionsUpdater(BaseCompanyCacheUpdater):

    UPDATE_INTERVAL = 3600  # seconds
    HISTORY_SIZE = 720  # days

    lock_name_prefix = 'company_sanctions_update'

    def __init__(
            self,
            companies_repository: SISCompaniesRepository,
            company_sanctions_update_cache: Cache,
            locker: RedLockFactory,
            organisation_names_collection: OrganisationNamesCollection,
            compliance_sanctions_repository: ComplianceSanctionsRepository,
            compliance_entities_repository: ComplianceEntitiesRepository,
            company_associations_repository: CompanyAssociationsRepository,
            entity_sanctions_repository: ComplianceEntitySanctionsRepository,
    ):
        super(CompanySanctionsUpdater, self).__init__(
            companies_repository, company_sanctions_update_cache, locker)
        self.organisation_names_collection = organisation_names_collection
        self.compliance_sanctions_repository = compliance_sanctions_repository
        self.compliance_entities_repository = compliance_entities_repository
        self.company_associations_repository = company_associations_repository
        self.entity_sanctions_repository = entity_sanctions_repository

    def process_company(
            self, company: SISCompany, session: Session = None) -> None:
        # filter out unknown company
        if company is None or company.name.lower() == 'unknown':
            return

        organisation_names = self.organisation_names_collection.query(
            sis_company_name=company.name,
            sis_company_code=company.sis_code,
        )

        compliance_companies = map(
            lambda x: x.organisation, organisation_names)

        self._clear_related_companies(company.id, session=session)
        create_related_company_func = partial(
            self._create_entity, entity_type=EntityType.ORGANISATION,
            sis_company_id=company.id, session=session,
        )
        deque(map(create_related_company_func, compliance_companies))

    def _clear_related_companies(
            self, sis_company_id: int, session: Session = None):
        company = self.companies_repository.get(
            id=sis_company_id, session=session)
        company.compliance.clear()
        session.flush()

    def _create_entity(
            self, entity_data: Entity, entity_type: EntityType,
            sis_company_id: int = None, session: Session = None,
    ):
        data = {
            'compliance_id': entity_data.id,
            'name': entity_data.name,
            'entity_type': entity_type,
        }

        if sis_company_id is not None:
            data['sis_company_ids'] = [sis_company_id, ]

        # we don't use optimistic pattern coz of used lock
        entity = self.compliance_entities_repository.get_or_none(
            compliance_id=entity_data.id,
            joinedload_related=['associations', ],
            session=session,
        )

        if entity is None:
            try:
                entity = self.compliance_entities_repository.create(
                    **data, session=session)
            # entity already exists
            except IntegrityError:
                return
        else:
            if sis_company_id and sis_company_id not in entity.sis_company_ids:
                entity.sis_company_ids.append(sis_company_id)

        if hasattr(entity_data, 'associations'):
            self.company_associations_repository.delete(
                src_id=entity.id, session=session)
            create_association_func = partial(
                self._create_association, entity.id, session=session)
            deque(map(create_association_func, entity_data.associations))

        if hasattr(entity_data, 'sanctions'):
            self.entity_sanctions_repository.delete(
                compliance_entity_id=entity.id, session=session)
            create_sanction_func = partial(
                self._create_sanction, entity.id, session=session)
            deque(map(create_sanction_func, entity_data.sanctions))

        return entity

    def _create_association(
            self, compliance_entity_id: int,
            association_data: EntityAssociation,
            session: Session = None,
    ) -> None:
        # backward compatibility
        # skip associations without sanctions
        if not association_data.entity.sanctions:
            return
        entity_type = EntityType(association_data.entity_type)
        entity = self._create_entity(
            association_data.entity, entity_type,
            session=session,
        )

        association = self.company_associations_repository.get_or_none(
            src_id=compliance_entity_id,
            dst_id=entity.id,
            session=session,
        )

        data = {
            'src_id': compliance_entity_id,
            'dst_id': entity.id,
            'relationship': association_data.relationship,
        }

        if association is not None:
            return

        try:
            self.company_associations_repository.create(
                **data, session=session)
        # association already exists
        except IntegrityError:
            pass

    def _create_sanction(
        self, compliance_entity_id: int, sanction_data: EntitySanction,
        session: Session = None,
    ) -> None:
        sanction = self.compliance_sanctions_repository.get_or_none(
            code=sanction_data.sanction.code,
            session=session,
        )

        data = {
            'code': sanction_data.sanction.code,
            'sanction_list_name': sanction_data.sanction.name,
        }

        entity_sanction_data = {
            'compliance_id': sanction_data.id,
            'start_date': sanction_data.since_date,
            'end_date': sanction_data.to_date,
            # backward compatibility
            'severity': Severity.WARNING,
        }

        if sanction is not None:
            self.compliance_sanctions_repository.update(
                sanction, **data, session=session)
            entity_sanction = self.entity_sanctions_repository.get_or_none(
                **entity_sanction_data,
                compliance_sanction_id=sanction.id,
                compliance_entity_id=compliance_entity_id,
                session=session,
            )
            if entity_sanction is None:
                try:
                    self.entity_sanctions_repository.create(
                        **entity_sanction_data,
                        compliance_sanction_id=sanction.id,
                        compliance_entity_id=compliance_entity_id,
                        session=session,
                        refresh=False,
                    )
                # entity sanction already exists
                except IntegrityError:
                    pass

            return

        data['compliance_entity_ids'] = {
            compliance_entity_id: entity_sanction_data,
        }

        try:
            self.compliance_sanctions_repository.create(
                **data, session=session)
        # sanction already exists
        except IntegrityError:
            pass
