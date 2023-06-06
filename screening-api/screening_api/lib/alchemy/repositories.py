"""Screening API lib alchemy repositories module"""
from typing import List, Tuple

from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql.elements import UnaryExpression
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.orm.scoping import scoped_session
from sqlalchemy.orm.session import Session

from screening_api.lib.alchemy.paginators import AlchemyPaginator
from screening_api.models import BaseModel


class AlchemyRepository:

    model = NotImplemented

    def __init__(self, session_factory: scoped_session):
        self.session_factory = session_factory

    def get_session(self) -> Session:
        return self.session_factory()

    def get_attr(
            self, name: str, model: BaseModel = None) -> InstrumentedAttribute:
        if model is None:
            model = self.model

        try:
            return getattr(model, name)
        except AttributeError:
            raise TypeError(
                "'{0}' is an invalid attribute name".format(name))

    def get_rel_model(self, name: str, model: BaseModel = None) -> BaseModel:
        attr = self.get_attr(name, model=model)

        return attr.mapper.class_

    def get_sort_expression(self, sort: str) -> UnaryExpression:
        desc = sort.startswith('-')
        sort_field_name = sort[1:] if desc else sort

        sort_path_fields = sort_field_name.split('__')
        sort_model = self.model
        for sort_path_field in sort_path_fields[:-1]:
            sort_model = self.get_rel_model(sort_path_field, sort_model)

        sort_attr = self.get_attr(sort_path_fields[-1], model=sort_model)

        return sort_attr.desc() if desc else sort_attr.asc()

    def get(self, **kwargs):
        query = self._filter_query(**kwargs)

        return query.one()

    def get_or_none(self, **kwargs):
        query = self._filter_query(**kwargs)

        return query.one_or_none()

    def get_or_create(self, **kwargs):
        session = kwargs.pop('session', None)
        if session is None:
            session = self.get_session()

        create_kwargs = kwargs.pop('create_kwargs', None)
        if create_kwargs is None:
            create_kwargs = {}

        try:
            return self.create(
                **kwargs, **create_kwargs, session=session), True
        except IntegrityError:
            return self.get(**kwargs, session=session), False

    def find(self, limit: int = None, **kwargs):
        query = self._find_query(**kwargs)

        if limit is not None:
            query = query.limit(limit)

        return query.all()

    def find_paginated(
            self, limit: int = None, offset: int = 0, **kwargs
            ) -> AlchemyPaginator:
        query = self._find_query(**kwargs)

        return query.paginate(limit, offset)

    def create(self, **kwargs):
        data, options = self._split_data(**kwargs)
        session = options.pop('session', None)
        refresh = options.pop('refresh', True)

        if session is None:
            session = self.get_session()

        instance = self.model(**data)

        session.add(instance)
        session.flush()

        if refresh:
            session.refresh(instance)

        return instance

    def update(self, instance_or_id: int, **kwargs):
        data, options = self._split_data(**kwargs)
        session = options.pop('session', None)
        refresh = options.pop('refresh', True)

        if session is None:
            session = self.get_session()

        if isinstance(instance_or_id, (int, )):
            instance = session.query(self.model).filter(
                self.model.id == instance_or_id,
            ).with_for_update().one()
        else:
            instance = instance_or_id

        for key, value in data.items():
            setattr(instance, key, value)

        session.add(instance)
        session.flush()

        if refresh:
            session.refresh(instance)

        return instance

    def delete(self, **kwargs):
        query = self._filter_query(**kwargs)

        return query.delete(synchronize_session=False)

    def _split_data(self, **options) -> Tuple[dict, dict]:
        data = {
            field_name: options.pop(field_name)
            for field_name in inspect(self.model).all_orm_descriptors.keys()
            if field_name in options and not field_name.startswith('__')
        }

        return data, options

    def _find_query(self, sort: List[str] = ['-id'], **kwargs):
        query = self._filter_query(**kwargs)

        sort_exps = list(map(self.get_sort_expression, sort))

        return query.order_by(*sort_exps)

    def _filter_query(self, **kwargs):
        session = kwargs.pop('session', None)
        if session is None:
            session = self.get_session()

        query = session.query(self.model)

        ids = kwargs.pop('id__in', None)
        if ids is not None:
            query = query.filter(self.model.id.in_(ids))

        joinedload_related = kwargs.pop('joinedload_related', None)
        subqueryload = kwargs.pop('subqueryload', None)
        innerjoin = kwargs.pop('innerjoin', False)
        if joinedload_related is not None:
            joinload_query = joinedload(
                *joinedload_related, innerjoin=innerjoin)
            if subqueryload is not None:
                joinload_query = joinload_query.subqueryload(*subqueryload)
            query = query.options(joinload_query)

        return query.filter_by(**kwargs)
