"""Screening API ship inspections repositories module"""
from datetime import date
from typing import List

from screening_api.lib.alchemy.queries import ExtendedQuery
from screening_api.lib.alchemy.repositories import AlchemyRepository
from screening_api.ship_inspections.models import ShipInspection


class ShipInspectionsRepository(AlchemyRepository):

    model = ShipInspection

    def create(
            self, ship_id: int, inspection_id: str, inspection_date: date,
            authority: str, detained_days: float, defects_count: int,
            detained: bool = False,
            **kwargs) -> ShipInspection:
        kwargs.update({
            'ship_id': ship_id,
            'inspection_id': inspection_id,
            'inspection_date': inspection_date,
            'authority': authority,
            'detained': detained,
            'detained_days': detained_days,
            'defects_count': defects_count,
        })

        return super(ShipInspectionsRepository, self).create(**kwargs)

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

    def _find_query(
            self,
            detained: bool = None,
            detained_days__gt: int = None,
            defects_count__gt: int = None,
            **kwargs
    ) -> ExtendedQuery:
        query = super(ShipInspectionsRepository, self)._find_query(**kwargs)

        if detained is not None:
            query = query.filter(
                self.model.detained.is_(detained),
            )

        if detained_days__gt is not None:
            query = query.filter(
                self.model.detained_days > detained_days__gt,
            )

        if defects_count__gt is not None:
            query = query.filter(
                self.model.defects_count > defects_count__gt,
            )

        return query
