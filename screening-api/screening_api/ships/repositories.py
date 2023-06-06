"""Screening API ships repositories module"""
from typing import List, Tuple

from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql import distinct
from sqlalchemy.sql.expression import or_

from screening_api.lib.alchemy.repositories import AlchemyRepository
from screening_api.ships.models import Ship


class ShipsRepository(AlchemyRepository):

    model = Ship

    def create(self, imo_id: int, **kwargs) -> Ship:
        kwargs.update({
            'imo_id': imo_id,
            'imo': str(imo_id),
        })

        return super(ShipsRepository, self).create(**kwargs)

    def update_by_imo_id(self, imo_id: int, **kwargs):
        data, options = self._split_data(**kwargs)
        session = options.pop('session', None)
        refresh = options.pop('refresh', True)

        if session is None:
            session = self.get_session()

        instance = session.query(self.model).filter(
            self.model.imo_id == imo_id,
        ).with_for_update().one()

        for key, value in data.items():
            setattr(instance, key, value)

        session.add(instance)
        session.flush()

        if refresh:
            session.refresh(instance)

        return instance

    def update_or_create(self, imo_id: int, **kwargs) -> Tuple[Ship, bool]:
        data, options = self._split_data(**kwargs)
        session = options.pop('session', None)

        if session is None:
            session = self.get_session()

        create_kwargs = options.pop('create_kwargs', None)
        if create_kwargs is None:
            create_kwargs = {}

        try:
            return self.update_by_imo_id(
                imo_id, **data, session=session), False
        except NoResultFound:
            return self.create(
                **data, **create_kwargs, imo_id=imo_id, session=session), True

    def find_countries(self, search: str = None) -> List[str]:
        session = self.get_session()

        query = session.query(
            distinct(self.model.country_id), self.model.country_name)

        if search:
            search_ilike = "%{0}%".format(search)
            query = query.filter(
                or_(
                    self.model.country_id.ilike(search_ilike),
                    self.model.country_name.ilike(search_ilike),
                )
            )

        return query.order_by(
            self.model.country_id.asc(), self.model.country_name.asc()).all()

    def find_types(self, search: str = None) -> List[str]:
        session = self.get_session()

        query = session.query(distinct(self.model.type))

        if search:
            search_ilike = "%{0}%".format(search)
            query = query.filter(self.model.type.ilike(search_ilike))

        instances = query.order_by(self.model.type.asc()).all()

        if not instances:
            return []

        return list(zip(*instances))[0]
