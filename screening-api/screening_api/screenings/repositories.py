"""Screening API screenings repositories module"""
import logging
from datetime import datetime
from typing import List

from sqlalchemy.sql.expression import or_

from screening_api.lib.alchemy.paginators import AlchemyPaginator
from screening_api.lib.alchemy.queries import ExtendedQuery
from screening_api.lib.alchemy.repositories import AlchemyRepository
from screening_api.screenings.enums import Severity, SeverityChange, Status
from screening_api.screenings.models import Screening
from screening_api.screenings.signals import bulk_screen_screenings

log = logging.getLogger(__name__)


class ScreeningsRepository(AlchemyRepository):

    model = Screening

    def create(
            self, account_id: int, ship_id: int,
            **kwargs) -> Screening:

        kwargs.update({
            'account_id': account_id,
            'ship_id': ship_id,
        })

        return super(ScreeningsRepository, self).create(**kwargs)

    def update(self, id: int, **kwargs):
        session = kwargs.pop('session', None)
        if session is None:
            session = self.get_session()

        session.begin()
        try:
            instance = session.query(self.model).filter(
                self.model.id == id,
            ).with_for_update().one()

            old_instance_status = instance.status
            old_instance_severity = instance.severity
            old_instance_severity_date = instance.updated

            for key, value in kwargs.items():
                setattr(instance, key, value)

            instance.status = instance.calculated_status

            if old_instance_status != instance.status == Status.DONE:
                log.info('Finished screening %s', id)
                instance.previous_severity = old_instance_severity
                instance.previous_severity_date = old_instance_severity_date
                instance.ship_sanctions_severity =\
                    instance.calculated_ship_sanctions_severity
                instance.company_sanctions_severity =\
                    instance.calculated_company_sanctions_severity
                instance.country_sanctions_severity =\
                    instance.calculated_country_sanctions_severity
                instance.ship_movements_severity =\
                    instance.calculated_ship_movements_severity
                instance.severity = instance.calculated_severity
                instance.severity_change = instance.calculated_severity_change

            session.add(instance)
            session.flush()
        except Exception as e:
            log.error('Unable to update screening %s: %s', id, e)
            session.rollback()
            raise
        else:
            session.commit()
            session.refresh(instance)
            return instance

    def screen_many(self, **kwargs) -> None:
        query = self._filter_query(**kwargs)

        objects = query.all()

        bulk_screen_screenings.send(self.__class__, instances=objects)

    def find_paginated(
            self,
            severities: List[Severity] = None,
            company_sanctions_severities: List[Severity] = None,
            ship_sanctions_severities: List[Severity] = None,
            country_sanctions_severities: List[Severity] = None,
            ship_inspections_severities: List[Severity] = None,
            ship_movements_severities: List[Severity] = None,
            severity_change: SeverityChange = None,
            created__lte: datetime = None,
            ship__country_ids: List[str] = None,
            ship__types: List[str] = None,
            search: str = None,
            sort: List[str] = ['-updated'],
            limit: int = None,
            **kwargs
    ) -> AlchemyPaginator:
        query = self._find_query(
            severities=severities,
            company_sanctions_severities=company_sanctions_severities,
            ship_sanctions_severities=ship_sanctions_severities,
            country_sanctions_severities=country_sanctions_severities,
            ship_inspections_severities=ship_inspections_severities,
            ship_movements_severities=ship_movements_severities,
            severity_change=severity_change,
            created__lte=created__lte,
            ship__country_ids=ship__country_ids,
            ship__types=ship__types,
            search=search,
            sort=sort,
            **kwargs
        )

        return query.paginate(limit)

    def _find_query(self, sort: List[str] = ['-updated'], **kwargs):
        query = super(ScreeningsRepository, self)._find_query(
            sort=sort, **kwargs)

        ship_model = self.get_rel_model('ship')
        query = query.join(ship_model)

        return query

    def _filter_query(
            self,
            severities: List[Severity] = None,
            company_sanctions_severities: List[Severity] = None,
            ship_sanctions_severities: List[Severity] = None,
            country_sanctions_severities: List[Severity] = None,
            ship_inspections_severities: List[Severity] = None,
            ship_movements_severities: List[Severity] = None,
            severity_change: SeverityChange = None,
            created__lte: datetime = None,
            ship__country_ids: List[str] = None,
            ship__types: List[str] = None,
            search: str = None,
            **kwargs
    ) -> ExtendedQuery:
        query = super(ScreeningsRepository, self)._filter_query(**kwargs)

        ship_model = self.get_rel_model('ship')

        if severities is not None:
            query = query.filter(
                self.model.severity.in_(severities),
            )

        if company_sanctions_severities is not None:
            query = query.filter(
                self.model.company_sanctions_severity.in_(
                    company_sanctions_severities),
            )

        if ship_sanctions_severities is not None:
            query = query.filter(
                self.model.ship_sanctions_severity.in_(
                    ship_sanctions_severities),
            )

        if country_sanctions_severities is not None:
            query = query.filter(
                self.model.country_sanctions_severity.in_(
                    country_sanctions_severities),
            )

        if ship_inspections_severities is not None:
            query = query.filter(
                self.model.ship_inspections_severity.in_(
                    ship_inspections_severities),
            )

        if ship_movements_severities is not None:
            query = query.filter(
                self.model.ship_movements_severity.in_(
                    ship_movements_severities),
            )

        if severity_change is not None:
            query = query.filter(
                self.model.severity_change == severity_change,
            )

        if created__lte is not None:
            query = query.filter(
                self.model.created <= created__lte,
            )

        if ship__country_ids is not None:
            query = query.filter(
                self.model.ship_id == ship_model.id,
                ship_model.country_id.in_(ship__country_ids),
            )

        if ship__types is not None:
            query = query.filter(
                self.model.ship_id == ship_model.id,
                ship_model.type.in_(ship__types),
            )

        if search:
            search_wildcard = "%{0}%".format(search)
            query = query.filter(
                self.model.ship_id == ship_model.id,
                or_(
                    ship_model.imo.contains(search),
                    ship_model.name.ilike(search_wildcard),
                )
            )

        return query

    def delete_orphans(self, **kwargs):
        session = kwargs.pop('session', None)
        if session is None:
            session = self.get_session()

        ship_model = self.get_rel_model('ship')

        subquery = session.query(self.model).filter(
            ship_model.id == self.model.ship_id)
        session.query(ship_model).filter(~subquery.exists()).delete(
            synchronize_session=False,
        )
