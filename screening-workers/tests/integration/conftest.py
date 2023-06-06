
import os
from unittest import mock

import pytest

from screening_api.models import BaseModel
from screening_api.testing.factories import Factory

from screening_workers.main import (
    get_file_config, get_database, setup_app,
    get_sis_client, get_compliance_client, get_ais_client, get_smh_client,
    get_portservice_client, get_cache_manager, get_locker, CONFIG_ENVIRON_NAME,
)
from screening_workers.screenings.signals import post_create_screening
from screening_workers.company_sanctions.tasks import (
    ShipRegisteredOwnerCompanyCheckTask, ShipOperatorCompanyCheckTask,
    ShipBeneficialOwnerCompanyCheckTask, ShipManagerCompanyCheckTask,
    ShipTechnicalManagerCompanyCheckTask, ShipCompanyAssociatesCheckTask,
)
from screening_workers.country_sanctions.tasks import (
    ShipFlagCheckTask, ShipRegisteredOwnerCheckTask, ShipOperatorCheckTask,
    ShipBeneficialOwnerCheckTask, ShipManagerCheckTask,
    ShipTechnicalManagerCheckTask, DocCompanyCheckTask,
)
from screening_workers.ship_inspections.tasks import (
    ShipInspectionsCheckTask,
)
from screening_workers.ship_movements.tasks import (
    ShipMovementsCheckTask, ZoneVisitsCheckTask,
)
from screening_workers.ship_sanctions.tasks import (
    ShipAssociationCheckTask, ShipSanctionCheckTask,
)


class CheckTasksMock:

    ship_reg_owner_company_patch = mock.patch.object(
        ShipRegisteredOwnerCompanyCheckTask, 'apply_async')
    ship_operator_company_patch = mock.patch.object(
        ShipOperatorCompanyCheckTask, 'apply_async')
    ship_beneficial_owner_company_patch = mock.patch.object(
        ShipBeneficialOwnerCompanyCheckTask, 'apply_async')
    ship_manager_company_patch = mock.patch.object(
        ShipManagerCompanyCheckTask, 'apply_async')
    ship_technical_manager_company_patch = mock.patch.object(
        ShipTechnicalManagerCompanyCheckTask, 'apply_async')
    ship_company_associates_patch = mock.patch.object(
        ShipCompanyAssociatesCheckTask, 'apply_async')
    ship_association_patch = mock.patch.object(
        ShipAssociationCheckTask, 'apply_async')
    ship_sanction_patch = mock.patch.object(
        ShipSanctionCheckTask, 'apply_async')
    port_visits_patch = mock.patch.object(
        ShipMovementsCheckTask, 'apply_async')
    zone_visits_patch = mock.patch.object(
        ZoneVisitsCheckTask, 'apply_async')
    ship_inspections_patch = mock.patch.object(
        ShipInspectionsCheckTask, 'apply_async')
    ship_flag_patch = mock.patch.object(
        ShipFlagCheckTask, 'apply_async')
    ship_registered_owner_patch = mock.patch.object(
        ShipRegisteredOwnerCheckTask, 'apply_async')
    ship_operator_patch = mock.patch.object(
        ShipOperatorCheckTask, 'apply_async')
    ship_beneficial_owner_patch = mock.patch.object(
        ShipBeneficialOwnerCheckTask, 'apply_async')
    ship_manager_patch = mock.patch.object(
        ShipManagerCheckTask, 'apply_async')
    ship_technical_manager_patch = mock.patch.object(
        ShipTechnicalManagerCheckTask, 'apply_async')
    doc_company_patch = mock.patch.object(
        DocCompanyCheckTask, 'apply_async')

    def start(self):
        self.ship_reg_owner_company_task =\
            self.ship_reg_owner_company_patch.start()
        self.ship_operator_company_task =\
            self.ship_operator_company_patch.start()
        self.ship_beneficial_owner_company_task =\
            self.ship_beneficial_owner_company_patch.start()
        self.ship_manager_company_task =\
            self.ship_manager_company_patch.start()
        self.ship_technical_manager_company_task =\
            self.ship_technical_manager_company_patch.start()
        self.ship_company_associates_task =\
            self.ship_company_associates_patch.start()
        self.ship_association_task = self.ship_association_patch.start()
        self.ship_sanction_task = self.ship_sanction_patch.start()
        self.port_visits_task = self.port_visits_patch.start()
        self.zone_visits_task = self.zone_visits_patch.start()
        self.ship_inspections_task = self.ship_inspections_patch.start()
        self.ship_flag_task = self.ship_flag_patch.start()
        self.ship_registered_owner_task = \
            self.ship_registered_owner_patch.start()
        self.ship_operator_task = self.ship_operator_patch.start()
        self.ship_beneficial_owner_task = \
            self.ship_beneficial_owner_patch.start()
        self.ship_manager_task = self.ship_manager_patch.start()
        self.ship_technical_manager_task = \
            self.ship_technical_manager_patch.start()
        self.doc_company_task = self.doc_company_patch.start()

    def stop(self):
        self.ship_reg_owner_company_patch.stop()
        self.ship_operator_company_patch.stop()
        self.ship_beneficial_owner_company_patch.stop()
        self.ship_manager_company_patch.stop()
        self.ship_technical_manager_company_patch.stop()
        self.ship_company_associates_patch.stop()
        self.ship_association_patch.stop()
        self.ship_sanction_patch.stop()
        self.port_visits_patch.stop()
        self.zone_visits_patch.stop()
        self.ship_inspections_task.stop()
        self.ship_flag_patch.stop()
        self.ship_registered_owner_patch.stop()
        self.ship_operator_patch.stop()
        self.ship_beneficial_owner_patch.stop()
        self.ship_manager_patch.stop()
        self.ship_technical_manager_patch.stop()
        self.doc_company_patch.stop()


@pytest.yield_fixture(scope='session')
def database():
    return get_database(os.environ)


@pytest.fixture(scope='session')
def sis_client():
    return get_sis_client(os.environ)


@pytest.fixture(scope='session')
def compliance_client():
    return get_compliance_client(os.environ)


@pytest.fixture(scope='session')
def smh_client():
    return get_smh_client(os.environ)


@pytest.fixture(scope='session')
def ais_client():
    return get_ais_client(os.environ)


@pytest.fixture(scope='session')
def portservice_client():
    return get_portservice_client(os.environ)


@pytest.fixture(scope='session')
def locker():
    return get_locker(os.environ)


@pytest.fixture(scope='session')
def cache_manager():
    return get_cache_manager(os.environ)


@pytest.yield_fixture(scope='session')
def connection(database):
    conn = database.connect()
    BaseModel.metadata.create_all(conn)
    yield conn
    BaseModel.metadata.drop_all(conn)
    conn.close()


@pytest.yield_fixture(scope='function')
def transaction(connection):
    transaction = connection.begin()
    yield connection
    transaction.rollback()


@pytest.fixture(scope='function')
def application(
        pytestconfig, monkeypatch, transaction, sis_client, compliance_client,
        smh_client, ais_client, portservice_client, cache_manager,
        locker, celery_app,
):
    # clear signal receivers (evil globals)
    post_create_screening._clear_state()

    monkeypatch.setenv(CONFIG_ENVIRON_NAME, pytestconfig.option.ini_file)
    get_file_config(os.environ)

    setup_app(
        celery_app, os.environ, transaction, sis_client, compliance_client,
        smh_client, ais_client, portservice_client, cache_manager, locker,
    )
    return celery_app


@pytest.yield_fixture(autouse=True)
def company_sanctions_update_cache(application):
    application.company_sanctions_update_cache.clear()
    yield application.company_sanctions_update_cache
    application.company_sanctions_update_cache.clear()


@pytest.yield_fixture(autouse=True)
def ship_inspections_update_cache(application):
    application.ship_inspections_update_cache.clear()
    yield application.ship_inspections_update_cache
    application.ship_inspections_update_cache.clear()


@pytest.yield_fixture(autouse=True)
def ship_sanctions_update_cache(application):
    application.ship_sanctions_update_cache.clear()
    yield application.ship_sanctions_update_cache
    application.ship_sanctions_update_cache.clear()


@pytest.yield_fixture(autouse=True)
def heartbeat_cache(application):
    application.heartbeat_cache_region.clear()
    yield application.heartbeat_cache_region
    application.heartbeat_cache_region.clear()


@pytest.yield_fixture(autouse=True)
def ship_update_cache(application):
    application.ship_update_cache.clear()
    yield application.ship_update_cache
    application.ship_update_cache.clear()


@pytest.fixture
def session_factory(application):
    return application.session_factory


@pytest.fixture
def factory(session_factory):
    session = session_factory()
    return Factory.create(session)


@pytest.yield_fixture
def check_tasks_mock():
    check_task_mock = CheckTasksMock()
    check_task_mock.start()
    yield check_task_mock
    check_task_mock.stop()


@pytest.yield_fixture
def mock_task_run(task):
    with mock.patch.object(task, 'run') as m:
        yield m
