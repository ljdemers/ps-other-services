"""Screening API ship sanctions repositories module"""
from typing import List

from screening_api.lib.alchemy.queries import ExtendedQuery
from screening_api.lib.alchemy.repositories import AlchemyRepository
from screening_api.blacklisted_sanctions.models import (
    BlacklistedSanctionListItem,
)
from screening_api.ship_sanctions.models import ShipSanction


class ShipSanctionsRepository(AlchemyRepository):

    model = ShipSanction

    def create(
            self, ship_id: int, sanction_list_name: str, is_active: bool,
            **kwargs) -> ShipSanction:
        kwargs.update({
            'ship_id': ship_id,
            'sanction_list_name': sanction_list_name,
            'is_active': is_active,
        })

        return super(ShipSanctionsRepository, self).create(**kwargs)

    def create_many(self, ship_id: int, *data_list: List[dict]) -> None:
        session = self.get_session()

        objects = [
            self.model(
                ship_id=ship_id,
                **data,
            ) for data in data_list
        ]

        session.bulk_save_objects(objects)
        session.flush()

    def _filter_query(
            self,
            blacklisted_sanction_list_id: int = None,
            **kwargs
    ) -> ExtendedQuery:
        session = kwargs.pop('session', None)
        if session is None:
            session = self.get_session()

        query = super(ShipSanctionsRepository, self)._filter_query(
            session=session, **kwargs)

        if blacklisted_sanction_list_id is not None:
            blacklisted_subquery = session.query(
                BlacklistedSanctionListItem.sanction_code,
            ).filter(
                BlacklistedSanctionListItem.blacklisted_sanction_list_id ==
                blacklisted_sanction_list_id,
            )
            query = query.filter(~self.model.code.in_(blacklisted_subquery))

        return query
