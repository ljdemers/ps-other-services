"""Screening Workers main module"""
from configparser import ConfigParser
import json
import logging
from logging.config import fileConfig
from urllib.parse import urlunparse

from beaker.cache import CacheManager
from beaker.util import parse_cache_config_options
from celery import Celery
from celery import signals
from celery.registry import tasks
from kombu.serialization import register
from redlock import RedLockFactory
from sqlalchemy.orm import sessionmaker

from screening_api.lib.alchemy.encoders import AlchemyEncoder
from screening_api.lib.alchemy.queries import ExtendedQuery
from screening_api.lib.health.indicators import AlchemyIndicator
from screening_api.main import (
    get_engine, get_json_content, get_resource_fullpath,
)
from screening_api.blacklisted_countries.repositories import (
    BlacklistedCountriesRepository,
)
from screening_api.companies.repositories import (
    SISCompaniesRepository,
)
from screening_api.company_associations.repositories import (
    CompanyAssociationsRepository,
)
from screening_api.sanctions.repositories import (
    ComplianceSanctionsRepository, ComplianceEntitySanctionsRepository,
)
from screening_api.entities.repositories import ComplianceEntitiesRepository
from screening_api.screenings.repositories import ScreeningsRepository
from screening_api.screenings_bulk.repositories import BulkScreeningsRepository
from screening_api.screenings_history.repositories import (
    ScreeningsHistoryRepository,
)
from screening_api.screenings_reports.repositories import (
    ScreeningsReportsRepository,
)
from screening_api.screenings_reports.validators import (
    ReportSchemaValidator,
)
from screening_api.ships.repositories import ShipsRepository
from screening_api.ship_inspections.repositories import (
    ShipInspectionsRepository,
)
from screening_api.ship_sanctions.repositories import ShipSanctionsRepository
from screening_api.ship_movements.repositories import ShipPortVisitsRepository

from screening_workers.lib.smh_api.smh_client import SMHClient
from screening_workers.lib.ais_api.ais_client import AISClient
from screening_workers.lib.ports_api.portservice_client import (
    PortServiceClient, )
from screening_workers.lib.api.clients import TastyPieClient
from screening_workers.lib.compliance_api.cache.collections import (
    ShipSanctionsCollection, CompanyAssociationsCollection,
    CompanySanctionsCollection,
)
from screening_workers.lib.compliance_api.cache.updaters import (
    ShipSanctionsUpdater, CompanySanctionsUpdater,
)
from screening_workers.lib.compliance_api.collections import (
    ShipsCollection as ComplianceShipsCollection,
    OrganisationNamesCollection as ComplianceOrganisationNamesCollection,
)
from screening_workers.lib.health.caches import HeartbeatCache
from screening_workers.lib.health.indicators import PortsIndicator
from screening_workers.lib.health.tasks import HeartbeatTask
from screening_workers.lib.health.schedules import HeartbeatSchedule
from screening_workers.lib.metrics.connectors import CeleryMetricsConnector
from screening_workers.lib.metrics.publishers import StatsDMetricsPublisher
from screening_workers.lib.screening.registries import CheckTasksRegistry
from screening_workers.lib.sis_api.cache.collections import (
    ShipsCollection, ShipInspectionsCollection,
)
from screening_workers.lib.sis_api.cache.updaters import (
    ShipUpdater, ShipInspectionsUpdater,
)
from screening_workers.lib.sis_api.collections import (
    ShipsCollection as SisShipsCollection, InspectionsCollection,
)
from screening_workers.lib.blacklist import default_blacklisted_ports

from screening_workers.company_sanctions.checks import (
    ShipRegisteredOwnerCompanyCheck, ShipOperatorCompanyCheck,
    ShipBeneficialOwnerCompanyCheck, ShipManagerCompanyCheck,
    ShipTechnicalManagerCompanyCheck, ShipCompanyAssociatesCheck,
)
from screening_workers.company_sanctions.tasks import (
    ShipRegisteredOwnerCompanyCheckTask, ShipOperatorCompanyCheckTask,
    ShipBeneficialOwnerCompanyCheckTask, ShipManagerCompanyCheckTask,
    ShipTechnicalManagerCompanyCheckTask, ShipCompanyAssociatesCheckTask,
)
from screening_workers.country_sanctions.checks import (
    ShipFlagCheck, ShipRegisteredOwnerCheck, ShipOperatorCheck,
    ShipBeneficialOwnerCheck, ShipManagerCheck, ShipTechnicalManagerCheck,
    DocCompanyCheck,
)
from screening_workers.country_sanctions.tasks import (
    ShipFlagCheckTask, ShipRegisteredOwnerCheckTask, ShipOperatorCheckTask,
    ShipBeneficialOwnerCheckTask, ShipManagerCheckTask,
    ShipTechnicalManagerCheckTask, DocCompanyCheckTask,
)
from screening_workers.screenings.creators import ScreeningsCreator
from screening_workers.screenings.killers import ScreeningKiller
from screening_workers.screenings.schedulers import ScreeningScheduler
from screening_workers.screenings.schedules import (
    ScreeningsBulkScreenSchedule, ScreeningsBulkScreenKillerSchedule,
)
from screening_workers.screenings.signals import post_create_screening
from screening_workers.screenings.tasks import (
    ScreeningScreenTask, ScreeningsBulkScreenTask, ScreeningScreenKillerTask,
    ScreeningsBulkScreenKillerTask,
)
from screening_workers.screenings_bulk.tasks import BulkScreeningValidationTask
from screening_workers.screenings_history.creators import (
    ScreeningsHistoryCreator,
)
from screening_workers.ship_inspections.checks import (
    ShipInspectionsCheck,
)
from screening_workers.ship_inspections.tasks import (
    ShipInspectionsCheckTask,
)
from screening_workers.ship_movements.checks import (
    ShipMovementsCheck, ZoneVisitsCheck,
)
from screening_workers.ship_movements.tasks import (
    ShipMovementsCheckTask, ZoneVisitsCheckTask,
)
from screening_workers.ship_sanctions.checks import (
    ShipAssociationCheck, ShipSanctionCheck,
)
from screening_workers.ship_sanctions.tasks import (
    ShipAssociationCheckTask, ShipSanctionCheckTask,
)
from screening_workers.ships.schedulers import ShipCacheUpdateScheduler
from screening_workers.ships.tasks import (
    ShipCacheUpdateTask, ShipsCacheUpdateTask,
)
from screening_workers.ships.upserters import ShipsUpserter

log = logging.getLogger(__name__)

CONFIG_ENVIRON_NAME = 'INI_FILE'


def get_file_config(config):
    ini_file = config.get(CONFIG_ENVIRON_NAME)

    if ini_file is None:
        raise RuntimeError("INI file not defined")

    config_parser = ConfigParser()
    config_parser.read(ini_file)

    fileConfig(ini_file, disable_existing_loggers=True)
    return config_parser


def get_database(config):
    return get_engine(
        config.get('DBSCHEME', 'postgresql+psycopg2'),
        config.get('DBUSER', 'screening'),
        config.get('DBPASSWORD', ''),
        config.get('DBHOST', 'localhost'),
        config.get('DBNAME', 'screening'),
    )


def get_sis_client(config):
    return TastyPieClient(
        config.get(
            'SIS_BASE_URL',
            'https://sis.polestarglobal.net/api/v1/',
        ),
        config.get('SIS_USERNAME', 'screening'),
        config.get('SIS_API_KEY', ''),
        encoding='utf-8',
    )


def get_compliance_client(config):
    return TastyPieClient(
        config.get(
            'COMPLIANCE_BASE_URL',
            'https://compliance.polestarglobal.net/api/v1/',
        ),
        config.get('COMPLIANCE_USERNAME', 'screening'),
        config.get('COMPLIANCE_API_KEY', ''),
        encoding='utf-8',
    )


def get_smh_client(config):
    return SMHClient(
        config.get(
            'SMH_REST_BASE_URL',
            'http://smh.polestar-testing.local/api/v1',
        ),
        config.get('SMH_USERNAME', 'screening'),
        config.get('SMH_PASSWORD', ''),
    )


def get_ais_client(config):
    return AISClient(
        config.get(
            'AIS_BASE_URL',
            'https://commaisservice.polestarglobal-test.com/api/v2',
        ),
        config.get('AIS_USERNAME', 'screening'),
        config.get('AIS_PASSWORD', ''),
    )


def get_portservice_client(config):
    return PortServiceClient(
        config.get(
            'PORTSERVICE_BASE_URL',
            'http://test-use1b-port-app-01.polestar-test.local/api/v2',
        )
    )


def get_redis_url(dbhost, dbname, dbuser='', dbpassword='', port='6379'):
    netloc = '{0}:{1}'.format(dbhost, port)
    if dbuser and dbpassword:
        netloc = '{0}:{1}@{2}'.format(dbuser, dbpassword, netloc)

    return urlunparse(('redis', netloc, dbname, None, None, None))


def get_locker(config):
    locker_url = get_redis_url(
        config.get('LOCKERHOST', 'localhost'),
        config.get('LOCKERNAME', '2'),
    )
    return RedLockFactory(
        [
            {
                'url': locker_url,
            },
        ]
    )


def get_cache_manager(config):
    cache_url = get_redis_url(
        config.get('LOCKERHOST', 'localhost'),
        config.get('LOCKERNAME', '3'),
    )
    cache_opts = {
        'cache.type': 'ext:redis',
        'cache.data_dir': '/tmp/cache/data',
        'cache.lock_dir': '/tmp/cache/lock',
        'cache.regions': 'short_term',
        'cache.short_term.url': cache_url,
        'cache.short_term.expire': '3600',
    }

    return CacheManager(**parse_cache_config_options(cache_opts))


def enable_debugger(config):
    import ptvsd
    ptvsd_host = config.get('HOST', '0.0.0.0')
    ptvsd_port = config.get('PORT', '5678')
    ptvsd_wait = config.get('wait_for_attach', False)
    try:
        ptvsd.enable_attach(address=(ptvsd_host, int(ptvsd_port)))
        log.debug("* PTVSd enabled on %s:%s", ptvsd_host, ptvsd_port)
        if ptvsd_wait:
            log.debug("* PTVSd is waiting for you to attach")
            ptvsd.wait_for_attach()
    except OSError:
        log.debug("* PTVSd already active")


def setup_metrics(config):
    metrics_enable = config.get('metrics_enable', False)
    metrics_namespace = config.get('metrics_namespace', '')
    if not metrics_enable:
        log.warning("Metrics disabled")
        return

    statsd_host = config.get('statsd_host', '127.0.0.1')
    statsd_port = config.get('statsd_port', 8125)
    statsd_prefix = config.get('statsd_prefix')
    metrics_publisher = StatsDMetricsPublisher(
        statsd_host, statsd_port, statsd_prefix)
    metrics_connector = CeleryMetricsConnector(
        metrics_publisher, metrics_namespace)
    metrics_connector.connect(signals)


def setup_app(
        app, config, database, sis_client, compliance_client, smh_client,
        ais_client, portservice_client, cache_manager, locker,
):
    def extended_dumps(o):
        return json.dumps(o, cls=AlchemyEncoder)

    register(
        'extended-json', extended_dumps, json.loads,
        content_type='application/x-extended-json', content_encoding='utf-8',
    )

    setup_metrics(app.conf)
    log.info("app.conf", app.conf)

    session_factory = sessionmaker(
        bind=database, autocommit=True, query_cls=ExtendedQuery)

    sis_ships_collection = SisShipsCollection(sis_client)

    compliance_ships_collection = ComplianceShipsCollection(compliance_client)

    blacklisted_countries_repository = BlacklistedCountriesRepository(
        session_factory)

    sis_companies_repository = SISCompaniesRepository(session_factory)
    compliance_entities_repository = ComplianceEntitiesRepository(
        session_factory)

    entity_sanctions_repository = ComplianceEntitySanctionsRepository(
        session_factory)

    company_associations_repository = CompanyAssociationsRepository(
        session_factory)

    ship_update_cache = cache_manager.get_cache_region(
        'ship_update', 'short_term')
    ships_repository = ShipsRepository(session_factory)
    ships_upserter = ShipsUpserter(
        ships_repository, sis_companies_repository, session_factory)

    ship_updater = ShipUpdater(
        ships_repository, ship_update_cache, locker, sis_ships_collection,
        ships_upserter,
    )
    ships_collection = ShipsCollection(ships_repository, ship_updater)

    company_sanctions_update_cache = cache_manager.get_cache_region(
        'company_sanctions_update', 'short_term')
    compliance_organisation_names_collection = \
        ComplianceOrganisationNamesCollection(compliance_client)
    compliance_sanctions_repository = ComplianceSanctionsRepository(
        session_factory)
    company_sanctions_updater = CompanySanctionsUpdater(
        company_sanctions_update_cache, locker, sis_companies_repository,
        compliance_organisation_names_collection,
        compliance_sanctions_repository, compliance_entities_repository,
        company_associations_repository, entity_sanctions_repository,
    )
    company_sanctions_collection = CompanySanctionsCollection(
        entity_sanctions_repository, company_sanctions_updater,
    )
    company_associations_collection = CompanyAssociationsCollection(
        company_associations_repository, company_sanctions_updater,
    )

    ship_inspections_update_cache = cache_manager.get_cache_region(
        'ship_inspections_update', 'short_term')
    inspections_collection = InspectionsCollection(sis_client)
    ship_inspections_repository = ShipInspectionsRepository(session_factory)
    ship_inspections_updater = ShipInspectionsUpdater(
        ships_repository, ship_inspections_update_cache, locker,
        inspections_collection, ship_inspections_repository,
    )
    ship_inspections_collection = ShipInspectionsCollection(
        ship_inspections_repository, ship_inspections_updater,
    )

    ship_sanctions_update_cache = cache_manager.get_cache_region(
        'ship_sanctions_update', 'short_term')
    ship_sanctions_repository = ShipSanctionsRepository(session_factory)
    ship_sanctions_updater = ShipSanctionsUpdater(
        ships_repository, ship_sanctions_update_cache, locker,
        compliance_ships_collection, ship_sanctions_repository,
    )
    ship_sanctions_collection = ShipSanctionsCollection(
        ship_sanctions_repository, ship_sanctions_updater,
    )

    ship_movements_repository = ShipPortVisitsRepository(session_factory)

    bulk_screenings_repository = BulkScreeningsRepository(session_factory)

    screenings_repository = ScreeningsRepository(session_factory)

    screenings_creator = ScreeningsCreator(
        sis_ships_collection, bulk_screenings_repository,
        screenings_repository, ships_repository, ships_upserter,
        session_factory,
    )

    spec_path = get_resource_fullpath('spec/')
    ship_info_report_schema = get_json_content(
        'spec/ship_info_report.json')
    ship_inspections_report_schema = get_json_content(
        'spec/ship_inspections_report.json')
    ship_sanction_report_schema = get_json_content(
        'spec/ship_sanction_report.json')
    ship_flag_report_schema = get_json_content(
        'spec/ship_flag_report.json')
    ship_associated_country_report_schema = get_json_content(
        'spec/ship_associated_country_report.json')
    ship_movement_report_schema = get_json_content(
        'spec/ship_movement_report.json')

    screenings_reports_repository = ScreeningsReportsRepository(
        session_factory,
        ReportSchemaValidator(
            ship_info_report_schema, spec_path,
        ),
        ReportSchemaValidator(
            ship_inspections_report_schema, spec_path,
        ),
        ReportSchemaValidator(
            ship_sanction_report_schema, spec_path,
        ),
        ReportSchemaValidator(
            ship_flag_report_schema, spec_path,
        ),
        ReportSchemaValidator(
            ship_associated_country_report_schema, spec_path,
        ),
        ReportSchemaValidator(
            ship_movement_report_schema, spec_path,
        ),
    )

    screenings_history_repository = ScreeningsHistoryRepository(
        session_factory)

    ship_registered_owner_company_check = ShipRegisteredOwnerCompanyCheck(
        screenings_repository, screenings_reports_repository, ships_collection,
        company_sanctions_collection,
    )
    ship_operatior_company_check = ShipOperatorCompanyCheck(
        screenings_repository, screenings_reports_repository, ships_collection,
        company_sanctions_collection,
    )
    ship_beneficial_owner_company_check = ShipBeneficialOwnerCompanyCheck(
        screenings_repository, screenings_reports_repository, ships_collection,
        company_sanctions_collection,
    )
    ship_manager_company_check = ShipManagerCompanyCheck(
        screenings_repository, screenings_reports_repository, ships_collection,
        company_sanctions_collection,
    )
    ship_technical_manager_company_check = ShipTechnicalManagerCompanyCheck(
        screenings_repository, screenings_reports_repository, ships_collection,
        company_sanctions_collection,
    )
    ship_company_associates_check = ShipCompanyAssociatesCheck(
        screenings_repository, screenings_reports_repository, ships_collection,
        company_associations_collection,
    )
    ship_flag_check = ShipFlagCheck(
        screenings_repository, screenings_reports_repository, ships_collection,
        blacklisted_countries_repository,
    )
    ship_registered_owner_check = ShipRegisteredOwnerCheck(
        screenings_repository, screenings_reports_repository, ships_collection,
        blacklisted_countries_repository,
    )
    ship_operator_check = ShipOperatorCheck(
        screenings_repository, screenings_reports_repository, ships_collection,
        blacklisted_countries_repository,
    )
    ship_beneficial_owner_check = ShipBeneficialOwnerCheck(
        screenings_repository, screenings_reports_repository, ships_collection,
        blacklisted_countries_repository,
    )
    ship_manager_check = ShipManagerCheck(
        screenings_repository, screenings_reports_repository, ships_collection,
        blacklisted_countries_repository,
    )
    ship_technical_manager_check = ShipTechnicalManagerCheck(
        screenings_repository, screenings_reports_repository, ships_collection,
        blacklisted_countries_repository,
    )
    doc_company_check = DocCompanyCheck(screenings_repository)
    ship_association_check = ShipAssociationCheck(screenings_repository)
    ship_sanction_check = ShipSanctionCheck(
        screenings_repository, screenings_reports_repository,
        ship_sanctions_collection,
    )
    ship_inspections_check = ShipInspectionsCheck(
        screenings_repository, screenings_reports_repository,
        ship_inspections_collection,
    )

    ship_movements_check = ShipMovementsCheck(screenings_repository,
                                              screenings_reports_repository,
                                              ship_movements_repository,
                                              ships_repository,
                                              default_blacklisted_ports,
                                              sis_client, config,
                                              smh_client, ais_client,
                                              portservice_client)

    zone_visits_check = ZoneVisitsCheck(screenings_repository)

    bulk_screening_validation_task = BulkScreeningValidationTask(
        screenings_creator)

    ship_reg_owner_company_check_task = ShipRegisteredOwnerCompanyCheckTask(
        ship_registered_owner_company_check)
    ship_operator_company_check_task = ShipOperatorCompanyCheckTask(
        ship_operatior_company_check)
    ship_beneficial_owner_company_check_task =\
        ShipBeneficialOwnerCompanyCheckTask(
            ship_beneficial_owner_company_check)
    ship_manager_company_check_task = ShipManagerCompanyCheckTask(
        ship_manager_company_check)
    ship_technical_manager_company_check_task =\
        ShipTechnicalManagerCompanyCheckTask(
            ship_technical_manager_company_check)
    ship_company_associates_check_task = ShipCompanyAssociatesCheckTask(
        ship_company_associates_check)

    ship_flag_check_task = ShipFlagCheckTask(ship_flag_check)
    ship_registered_owner_check_task = ShipRegisteredOwnerCheckTask(
        ship_registered_owner_check)
    ship_operator_check_task = ShipOperatorCheckTask(ship_operator_check)
    ship_beneficial_owner_check_task = ShipBeneficialOwnerCheckTask(
        ship_beneficial_owner_check)
    ship_manager_check_task = ShipManagerCheckTask(ship_manager_check)
    ship_technical_manager_check_task = ShipTechnicalManagerCheckTask(
        ship_technical_manager_check)
    doc_company_check_task = DocCompanyCheckTask(doc_company_check)

    ship_association_check_task = ShipAssociationCheckTask(
        ship_association_check)
    ship_sanction_check_task = ShipSanctionCheckTask(ship_sanction_check)
    ship_inspections_check_task = ShipInspectionsCheckTask(
        ship_inspections_check)
    ship_movements_check_task = ShipMovementsCheckTask(
        ship_movements_check,
        soft_time_limit=app.conf.get('task_smc_soft_time_limit', 600),
    )
    zone_visits_check_task = ZoneVisitsCheckTask(zone_visits_check)

    screenings_history_creator = ScreeningsHistoryCreator(
        screenings_repository, screenings_history_repository,
        screenings_reports_repository,
    )

    check_tasks_registry = CheckTasksRegistry.create(
        ship_reg_owner_company_check_task, ship_operator_company_check_task,
        ship_beneficial_owner_company_check_task,
        ship_manager_company_check_task,
        ship_technical_manager_company_check_task,
        ship_company_associates_check_task,
        ship_flag_check_task, ship_registered_owner_check_task,
        ship_operator_check_task, ship_beneficial_owner_check_task,
        ship_manager_check_task, ship_technical_manager_check_task,
        doc_company_check_task,
        ship_association_check_task, ship_sanction_check_task,
        ship_inspections_check_task,
        ship_movements_check_task, zone_visits_check_task,
    )

    screening_killer = ScreeningKiller(screenings_repository)

    screening_screen_killer_task = ScreeningScreenKillerTask(screening_killer)

    screenings_bulk_screen_killer_task = ScreeningsBulkScreenKillerTask(
        screenings_repository, screening_killer)

    screenings_bulk_screen_killer_time = app.conf.get(
        'screenings_bulk_screen_killer_time', '0 0 * * *')
    screenings_bulk_screen_killer_schedule =\
        ScreeningsBulkScreenKillerSchedule(
            screenings_bulk_screen_killer_task,
            screenings_bulk_screen_killer_time,
        )

    screening_scheduler = ScreeningScheduler(
        screenings_repository, screenings_history_creator,
        check_tasks_registry,
    )

    screening_screen_task = ScreeningScreenTask(screening_scheduler)

    screenings_bulk_screen_task = ScreeningsBulkScreenTask(
        screenings_repository, screening_scheduler,
        # default four hours
        task_time_limit=app.conf.get('task_time_limit', 4 * 60 * 60),
        soft_time_limit=app.conf.get('task_soft_time_limit')
    )

    screenings_bulk_screen_time = app.conf.get(
        'screenings_bulk_screen_time', '0 1 * * *')
    screenings_bulk_screen_schedule = ScreeningsBulkScreenSchedule(
        screenings_bulk_screen_task, screenings_bulk_screen_time)

    post_create_screening.connect(
        screening_scheduler.schedule_on_signal,
        sender=ScreeningsCreator, weak=False,
    )

    ship_cache_update_task = ShipCacheUpdateTask(ships_collection)
    ship_cache_update_scheduler = ShipCacheUpdateScheduler(
        ship_cache_update_task)
    ships_cache_update_task = ShipsCacheUpdateTask(
        ships_repository, ship_cache_update_scheduler)

    database_indicator = AlchemyIndicator(database)
    ports_indicator = PortsIndicator(portservice_client)

    heartbeat_cache_region = cache_manager.get_cache_region(
        'heartbeat', 'short_term')
    heartbeat_cache = HeartbeatCache(
        heartbeat_cache_region, 'heartbeat',
        database_indicator, ports_indicator,
    )
    heartbeat_task = HeartbeatTask(heartbeat_cache)
    heartbeat_schedule = HeartbeatSchedule(heartbeat_task)

    check_tasks_registry.register(app, tasks)

    tasks.register(bulk_screening_validation_task)
    tasks.register(screening_screen_task)
    tasks.register(screening_screen_killer_task)
    tasks.register(screenings_bulk_screen_task)
    tasks.register(screenings_bulk_screen_killer_task)
    tasks.register(ship_cache_update_task)
    tasks.register(ships_cache_update_task)
    tasks.register(heartbeat_task)
    app.register_task(bulk_screening_validation_task)
    app.register_task(screening_screen_task)
    app.register_task(screening_screen_killer_task)
    app.register_task(screenings_bulk_screen_task)
    app.register_task(screenings_bulk_screen_killer_task)
    app.register_task(ship_cache_update_task)
    app.register_task(ships_cache_update_task)
    app.register_task(heartbeat_task)

    screenings_bulk_screen_schedule.setup(sender=app)
    screenings_bulk_screen_killer_schedule.setup(sender=app)
    # Don't setup. Let's try update locker for now.
    # ships_cache_update_time = app.conf.get(
    #     'ships_cache_update_time', '0 16 * * *')
    # ships_cache_update_schedule = ShipsCacheUpdateSchedule(
    #     ships_cache_update_task, ships_cache_update_time)
    # ships_cache_update_schedule.setup(sender=app)
    heartbeat_schedule.setup(sender=app)

    app.session_factory = session_factory
    app.ships_repository = ships_repository
    app.ship_inspections_repository = ship_inspections_repository
    app.bulk_screenings_repository = bulk_screenings_repository
    app.screenings_repository = screenings_repository
    app.screenings_reports_repository = screenings_reports_repository
    app.screenings_history_repository = screenings_history_repository
    app.ship_inspections_updater = ship_inspections_updater
    app.ship_update_cache = ship_update_cache
    app.company_sanctions_update_cache = company_sanctions_update_cache
    app.ship_inspections_update_cache = ship_inspections_update_cache
    app.ship_sanctions_update_cache = ship_sanctions_update_cache
    app.screenings_bulk_screen_schedule = screenings_bulk_screen_schedule
    app.heartbeat_cache_region = heartbeat_cache_region
    app.portservice_client = portservice_client


def app_factory(
        config, database, sis_client, compliance_client, smh_client,
        ais_client, portservice_client, locker, cache_manager,
):
    app = Celery('__name__')
    app.config_from_envvar('CELERY_CONFIG_MODULE', force=True)
    log.info("app.conf:", app.conf)
    setup_app(
        app, config, database, sis_client, compliance_client, smh_client,
        ais_client, portservice_client, locker, cache_manager,
    )

    return app


def create_app(config):
    file_config = get_file_config(config)

    if file_config.has_section('ptvsd'):
        enable_debugger(file_config['ptvsd'])

    database = get_database(config)
    sis_client = get_sis_client(config)
    compliance_client = get_compliance_client(config)
    smh_client = get_smh_client(config)
    ais_client = get_ais_client(config)
    portservice_client = get_portservice_client(config)
    cache_manager = get_cache_manager(config)
    locker = get_locker(config)

    return app_factory(
        config, database, sis_client, compliance_client, smh_client,
        ais_client, portservice_client, cache_manager, locker,
    )
