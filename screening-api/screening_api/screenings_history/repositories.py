"""Screening API screenings history repositories module"""
from datetime import datetime
from typing import List

from screening_api.lib.alchemy.queries import ExtendedQuery
from screening_api.lib.alchemy.repositories import AlchemyRepository
from screening_api.screenings_history.models import ScreeningHistory


class ScreeningsHistoryRepository(AlchemyRepository):

    model = ScreeningHistory

    def create(
        self, screening_id: int, severity_date: datetime, **kwargs,
    ) -> ScreeningHistory:
        kwargs.update({
            'screening_id': screening_id,
            'severity_date': severity_date,
        })

        return super(ScreeningsHistoryRepository, self).create(**kwargs)

    def _find_query(
            self,
            screening__account_id: List[str] = None,
            **kwargs
    ) -> ExtendedQuery:
        screening_model = self.get_rel_model('screening')

        query = super(ScreeningsHistoryRepository, self)._find_query(**kwargs)

        query = query.join(screening_model)

        if screening__account_id is not None:
            query = query.filter(
                screening_model.account_id == screening__account_id,
            )

        return query
