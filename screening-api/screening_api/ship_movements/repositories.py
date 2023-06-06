"""Screening API ship inspections repositories module"""
from datetime import date
from typing import List

from screening_api.lib.alchemy.repositories import AlchemyRepository
from screening_api.ship_movements.models import ShipPortVisit


class ShipPortVisitsRepository(AlchemyRepository):

    model = ShipPortVisit

    def create(
            self, ship_id: int, movement_id: int,
            entered: date, departed: date,
            **kwargs) -> ShipPortVisit:
        kwargs.update({
            'ship_id': ship_id,
            'movement_id': movement_id,
            'entered': entered,
            'departed': departed,
        })

        return super(ShipPortVisitsRepository, self).create(**kwargs)

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
