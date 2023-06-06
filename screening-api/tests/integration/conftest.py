import os

import pytest
from sqlalchemy.orm import sessionmaker

from screening_api.main import get_database
from screening_api.testing.factories import Factory


@pytest.yield_fixture(scope='session')
def database():
    return get_database(os.environ)


@pytest.yield_fixture(scope='function')
def connection(database):
    conn = database.connect()
    transaction = conn.begin()
    yield conn
    transaction.rollback()


@pytest.fixture
def session_factory(connection):
    return sessionmaker(bind=connection, autocommit=True)


@pytest.fixture
def factory(session_factory):
    session = session_factory()
    return Factory.create(session)
