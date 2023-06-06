import os

import pytest
from flask.testing import FlaskClient
from sqlalchemy.orm import sessionmaker

from screening_api.main import (
    get_database, get_broker, get_cache_manager, get_file_config, app_factory,
    CONFIG_ENVIRON_NAME,
)
from screening_api.lib.auth.factories import UserTokenFactory, UserFactory
from screening_api.lib.flask.responses import HTTPResponse
from screening_api.screenings_bulk.singnals import bulk_save_screenings
from screening_api.screenings.signals import bulk_screen_screenings
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


@pytest.yield_fixture(scope='session')
def broker():
    return get_broker(os.environ)


@pytest.yield_fixture(scope='session')
def cache_manager():
    return get_cache_manager(os.environ)


@pytest.fixture
def session_factory(connection):
    return sessionmaker(bind=connection, autocommit=True)


@pytest.yield_fixture(scope='function')
def application(pytestconfig, monkeypatch, connection, broker, cache_manager):
    # clear signal receivers (evil globals)
    bulk_save_screenings._clear_state()
    bulk_screen_screenings._clear_state()

    monkeypatch.setenv(CONFIG_ENVIRON_NAME, pytestconfig.option.ini_file)
    get_file_config(os.environ)
    transaction = connection.begin()
    yield app_factory(os.environ, connection, broker, cache_manager)
    transaction.rollback()


@pytest.fixture
def test_client(application):
    # @tod: move to test conf
    application.config['SERVER_NAME'] = 'api'
    return FlaskClient(application, HTTPResponse, use_cookies=True)


@pytest.fixture
def user_factory():
    return UserFactory


@pytest.fixture
def token_factory(application):
    factory = UserTokenFactory(application.authentication.secret_key)
    return factory.create


@pytest.fixture
def user(user_factory):
    return user_factory(account_id=54321)


@pytest.fixture
def token(token_factory, user):
    token_bytes = token_factory(user=user)
    return token_bytes.decode()


@pytest.fixture
def auth_headers(token, test_client):
    return {
        'Authorization': 'Bearer {0}'.format(token),
    }


@pytest.yield_fixture
def authenticated(test_client, token):
    test_client.environ_base['HTTP_AUTHORIZATION'] = 'Bearer {0}'.format(token)
    yield test_client
    del test_client.environ_base['HTTP_AUTHORIZATION']


@pytest.fixture
def factory(session_factory):
    session = session_factory()
    return Factory.create(session)


@pytest.yield_fixture(autouse=True)
def heartbeat_cache_region(application):
    application.heartbeat_cache_region.clear()
    yield application.heartbeat_cache_region
    application.heartbeat_cache_region.clear()
