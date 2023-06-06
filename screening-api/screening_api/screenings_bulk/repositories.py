"""Screening API screenings bulk repositories module"""
from typing import List

from screening_api.lib.alchemy.queries import ExtendedQuery
from screening_api.lib.alchemy.repositories import AlchemyRepository
from screening_api.screenings_bulk.enums import BulkScreeningStatus
from screening_api.screenings_bulk.models import BulkScreening
from screening_api.screenings_bulk.singnals import bulk_save_screenings


class BulkScreeningsRepository(AlchemyRepository):

    model = BulkScreening

    def create(
            self, account_id: int, imo_id: int,
            **kwargs) -> BulkScreening:
        kwargs.update({
            'account_id': account_id,
            'imo_id': imo_id,
        })

        return super(BulkScreeningsRepository, self).create(**kwargs)

    def create_many(self, account_id: int, *imo_ids: int) -> None:
        session = self.get_session()

        objects = [
            self.model(
                account_id=account_id,
                imo_id=imo_id,
            ) for imo_id in set(imo_ids)
        ]

        session.bulk_save_objects(objects, return_defaults=True)
        session.flush()
        bulk_save_screenings.send(self.__class__, instances=objects)

    def update(
            self, id: int, status: BulkScreeningStatus = None,
            result: bool = None, **options):
        session = options.pop('session', None)
        if session is None:
            session = self.get_session()

        instance = session.query(self.model).filter(
            self.model.id == id,
        ).with_for_update().one()

        if status is not None:
            instance.status = status

        if result is not None:
            instance.result = result

        session.add(instance)
        session.flush()
        return instance

    def _find_query(
            self,
            statuses: List[BulkScreeningStatus] = None,
            results: List[bool] = None,
            **kwargs
    ) -> ExtendedQuery:
        query = super(BulkScreeningsRepository, self)._find_query(**kwargs)

        if statuses is not None:
            query = query.filter(self.model.status.in_(statuses))

        if results is not None:
            query = query.filter(self.model.result.in_(results))

        return query
