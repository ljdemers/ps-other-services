"""Screening API lib alchemy queries module"""
from sqlalchemy.orm import Query

from screening_api.lib.alchemy.paginators import AlchemyPaginator


class ExtendedQuery(Query):

    def paginate(self, per_page, offset=0, allow_empty_first_page=True):
        return AlchemyPaginator(
            self, per_page,
            offset=offset, allow_empty_first_page=allow_empty_first_page,
        )
