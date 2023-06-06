"""Screening API main module"""
from configparser import ConfigParser
import logging
from logging.config import fileConfig
import os
from urllib.parse import urlunparse

from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.ext.flask.middleware import XRayMiddleware
from beaker.cache import CacheManager
from beaker.util import parse_cache_config_options
from flask.app import Flask
from flask.blueprints import Blueprint
from flask_compress import Compress
from flask_cors import CORS
from kombu.connection import Connection
from openapi_core import create_spec
from pkg_resources import resource_filename
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from ujson import loads, dumps
from yaml import safe_load

from screening_api.lib.alchemy.encoders import AlchemyEncoder
from screening_api.lib.alchemy.queries import ExtendedQuery
from screening_api.lib.auth.webtoken import JWTAuthentication
from screening_api.lib.flask.handlers import LogExceptionsHandler
from screening_api.lib.health.indicators import (
    AlchemyIndicator, KombuIndicator, XRayIndicator, HeartbeatIndicator,
    Indicators,
)
from screening_api.lib.messaging.caches import TimestampCache
from screening_api.lib.messaging.publishers import CeleryTaskPublisher
from screening_api.blacklisted_countries.repositories import (
    BlacklistedCountriesRepository,
)
from screening_api.companies.repositories import (
    SISCompaniesRepository,
)
from screening_api.sanctions.repositories import (
    ComplianceSanctionsRepository,
)
from screening_api.countries.views import CountriesView
from screening_api.entities.repositories import ComplianceEntitiesRepository
from screening_api.health.views import LivenessView, ReadinessView
from screening_api.ships.repositories import ShipsRepository
from screening_api.ships.views import ShipTypesView
from screening_api.screenings.repositories import ScreeningsRepository
from screening_api.screenings.signals import bulk_screen_screenings
from screening_api.screenings.subscribers import ScreeningsScreenSubscriber
from screening_api.screenings.views import (
    ScreeningsView, ScreeningView, ScreenView,
)
from screening_api.screenings_bulk.repositories import BulkScreeningsRepository
from screening_api.screenings_bulk.singnals import bulk_save_screenings
from screening_api.screenings_bulk.subscribers import (
    BulkScreeningsValidationSubscriber,
)
from screening_api.screenings_bulk.views import (
    BulkScreeningsView, BulkScreeningView,
)
from screening_api.screenings_history.repositories import (
    ScreeningsHistoryRepository,
)
from screening_api.screenings_history.views import ScreeningsHistoryView
from screening_api.ship_inspections.repositories import (
    ShipInspectionsRepository,
)
from screening_api.screenings_reports.views import (
    ScreeningShipInfoReportView,
    ScreeningShipInspectionsReportView, ScreeningShipSanctionsReportView,
    ScreeningCountrySanctionsReportView, ScreeningShipMovementsReportView,
    ScreeningCompanySanctionsReportView, ScreeningPdfReportView,
)
from screening_api.ship_sanctions.repositories import ShipSanctionsRepository
from screening_api.ship_movements.repositories import ShipPortVisitsRepository

from screening_api.screenings_reports.repositories import (
    ScreeningsReportsRepository,
)
from screening_api.screenings_reports.validators import (
    ReportSchemaValidator,
)

from screening_api.lib.flask.utils import (
    format_datetime, format_date,
    format_severity, format_title_severity, format_border_severity,
)

log = logging.getLogger(__name__)

CONFIG_ENVIRON_NAME = 'INI_FILE'


def get_resource_fullpath(resource_path):
    path = resource_filename('screening_api', resource_path)
    return os.path.join(os.path.dirname(__file__), path)


def get_json_content(path):
    json_fullpath = get_resource_fullpath(path)

    with open(json_fullpath, encoding='utf-8') as json_file:
        return safe_load(json_file)


def get_url(scheme, user='', password='', hostname='', path='', port=None):
    auth = user
    if user or password:
        auth = '{0}:{1}'.format(user, password)

    host = hostname
    if hostname or port:
        host = '{0}:{1}'.format(hostname, port)

    netloc = '@'.join([auth, host])
    return urlunparse((scheme, netloc, path, None, None, None))


def get_engine(backend, user, password, host, name, port='5432'):
    url = get_url(backend, user, password, host, name, port=port)
    return create_engine(
        url, json_serializer=dumps, json_deserializer=loads,
        connect_args={'connect_timeout': 10},
    )


def get_database(config):
    return get_engine(
        config.get('DBBACKEND', 'postgresql+psycopg2'),
        config.get('DBUSER', 'screening'),
        config.get('DBPASSWORD', ''),
        config.get('DBHOST', 'localhost'),
        config.get('DBNAME', 'screening'),
        config.get('DBPORT', '5432'),
    )


def get_broker(config):
    url = get_url(
        config.get('BROKERBACKEND', 'redis'),
        config.get('BROKERUSER', ''),
        config.get('BROKERPASSWORD', ''),
        config.get('BROKERHOST', 'localhost'),
        config.get('BROKERNAME', '0'),
        config.get('BROKERPORT', '6379'),
    )
    return Connection(
        url,
        transport_options={
            'socket_timeout': 5,
            'socket_connect_timeout': 5,
            'socket_keepalive': True,
            'max_retries': 3,
            'retry_on_connerror': False,
        },
    )


def get_file_config(config):
    ini_file = config.get(CONFIG_ENVIRON_NAME)

    if ini_file is None:
        raise RuntimeError("INI file not defined")

    config_parser = ConfigParser()
    config_parser.read(ini_file)

    fileConfig(ini_file, disable_existing_loggers=True)
    return config_parser


def get_cache_manager(config):
    url = get_url(
        config.get('CACHEBACKEND', 'redis'),
        config.get('CACHEUSER', ''),
        config.get('CACHEPASSWORD', ''),
        config.get('CACHEHOST', 'localhost'),
        config.get('CACHENAME', '3'),
        config.get('CACHEPORT', '6379'),
    )
    cache_opts = {
        'cache.type': 'ext:redis',
        'cache.data_dir': '/tmp/cache/data',
        'cache.lock_dir': '/tmp/cache/lock',
        'cache.regions': 'short_term',
        'cache.short_term.url': url,
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


def create_app(config):
    file_config = get_file_config(config)

    if file_config.has_section('ptvsd'):
        enable_debugger(file_config['ptvsd'])

    database = get_database(config)
    broker = get_broker(config)
    cache_manager = get_cache_manager(config)

    return app_factory(config, database, broker, cache_manager)


def configure_xray(app, config):
    service = config['AWS_XRAY_TRACING_NAME']
    context_missing = config.get('AWS_XRAY_CONTEXT_MISSING', 'RUNTIME_ERROR')
    daemon_address = config.get('AWS_XRAY_DAEMON_ADDRESS', '127.0.0.1:2000')

    xray_recorder.configure(
        service=service,
        context_missing=context_missing,
        daemon_address=daemon_address,
    )
    XRayMiddleware(app, xray_recorder)


def app_factory(config, database, broker, cache_manager):
    app = Flask(__name__)
    app.json_encoder = AlchemyEncoder
    log_exceptions_handler = LogExceptionsHandler(app, log)
    app.register_error_handler(Exception, log_exceptions_handler)
    CORS(app)
    Compress(app)

    if 'AWS_XRAY_TRACING_NAME' in config:
        configure_xray(app, config)

    authentication = JWTAuthentication(config['JWT_SECRET'])

    liveness_view = LivenessView.as_view('liveness')
    app.add_url_rule('/healthz', view_func=liveness_view)

    heartbeat_cache_region = cache_manager.get_cache_region(
        'heartbeat', 'short_term')
    heartbeat_cache = TimestampCache(heartbeat_cache_region, 'heartbeat')

    database_indicator = AlchemyIndicator(database)
    broker_indicator = KombuIndicator(broker)
    xray_indicator = XRayIndicator(xray_recorder)
    heartbeat_indicator = HeartbeatIndicator(heartbeat_cache)
    indicators = Indicators(
        database_indicator, broker_indicator, xray_indicator,
        heartbeat_indicator,
    )
    readiness_view = ReadinessView.as_view('readiness', indicators)
    app.add_url_rule('/health', view_func=readiness_view)

    spec_path = get_resource_fullpath('spec/')
    openapi_schema = get_json_content('spec/openapi.json')
    openapi_spec = create_spec(openapi_schema)

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

    session_registry = sessionmaker(
        bind=database, autocommit=True, query_cls=ExtendedQuery)
    session_factory = scoped_session(session_registry)

    broker_connections_limit = config.get('BROKER_CONNECTIONS_LIMIT', 100)
    bulk_screenings_validation_task_publisher = CeleryTaskPublisher(
        broker, 'screening.bulk_screenings.validation',
        broker_connections_limit,
    )
    bulk_screenings_validation_sub = BulkScreeningsValidationSubscriber(
        bulk_screenings_validation_task_publisher)

    bulk_save_screenings.connect(
        bulk_screenings_validation_sub,
        sender=BulkScreeningsRepository, weak=False,
    )

    screenings_screen_task_publisher = CeleryTaskPublisher(
        broker, 'screening.screenings.screen',
        broker_connections_limit,
    )
    screenings_screen_sub = ScreeningsScreenSubscriber(
        screenings_screen_task_publisher)

    bulk_screen_screenings.connect(
        screenings_screen_sub,
        sender=ScreeningsRepository, weak=False,
    )

    api_v1 = Blueprint('api_v1', __name__)

    blacklisted_countries_repository = BlacklistedCountriesRepository(
        session_factory)

    sis_companies_repository = SISCompaniesRepository(session_factory)
    compliance_entities_repository = ComplianceEntitiesRepository(
        session_factory)

    compliance_sanctions_repository = ComplianceSanctionsRepository(
        session_factory)

    ships_repository = ShipsRepository(session_factory)

    ship_inspections_repository = ShipInspectionsRepository(session_factory)

    ship_sanctions_repository = ShipSanctionsRepository(session_factory)
    ship_movements_repository = ShipPortVisitsRepository(session_factory)

    countries_view = CountriesView.as_view(
        'countries', ships_repository, openapi_spec, authentication)

    api_v1.add_url_rule('/countries', view_func=countries_view)

    ship_types_view = ShipTypesView.as_view(
        'ship_types', ships_repository, openapi_spec, authentication)

    api_v1.add_url_rule('/ship_types', view_func=ship_types_view)

    screenings_repository = ScreeningsRepository(session_factory)
    screenings_view = ScreeningsView.as_view(
        'screenings', screenings_repository, openapi_spec, authentication)

    api_v1.add_url_rule('/screenings', view_func=screenings_view)

    screening_view = ScreeningView.as_view(
        'screening', screenings_repository, openapi_spec, authentication)

    api_v1.add_url_rule(
        '/screenings/<screening_id>', view_func=screening_view)

    screen_view = ScreenView.as_view(
        'screen', screenings_repository, openapi_spec, authentication)

    api_v1.add_url_rule('/screenings/screen', view_func=screen_view)

    bulk_screenings_repository = BulkScreeningsRepository(session_factory)
    bulk_screenings_view = BulkScreeningsView.as_view(
        'bulk_screenings', openapi_spec, authentication,
        bulk_screenings_repository,
    )

    api_v1.add_url_rule(
        '/screenings/_bulk', view_func=bulk_screenings_view)

    bulk_screening_view = BulkScreeningView.as_view(
        'bulk_screening', openapi_spec, authentication,
        bulk_screenings_repository,
    )

    api_v1.add_url_rule(
        '/screenings/_bulk/<bulk_screening_id>', view_func=bulk_screening_view)

    screenings_history_repository = ScreeningsHistoryRepository(
        session_factory)
    screenings_history_view = ScreeningsHistoryView.as_view(
        'screenings_history', openapi_spec, authentication,
        screenings_history_repository, screenings_repository,
    )

    api_v1.add_url_rule(
        '/screenings/<screening_id>/history',
        view_func=screenings_history_view,
    )

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

    ship_info_report_view = ScreeningShipInfoReportView.as_view(
        'ship_info_report', openapi_spec, authentication,
        screenings_reports_repository,
    )

    api_v1.add_url_rule(
        '/screenings/<screening_id>/reports/ship_info',
        view_func=ship_info_report_view,
    )

    company_sanctions_report_view =\
        ScreeningCompanySanctionsReportView.as_view(
            'company_sanctions_report', openapi_spec, authentication,
            screenings_reports_repository,
        )

    api_v1.add_url_rule(
        '/screenings/<screening_id>/reports/company_sanctions',
        view_func=company_sanctions_report_view,
    )

    ship_inspections_report_view = ScreeningShipInspectionsReportView.as_view(
        'ship_inspections_report', openapi_spec, authentication,
        screenings_reports_repository,
    )

    api_v1.add_url_rule(
        '/screenings/<screening_id>/reports/ship_inspections',
        view_func=ship_inspections_report_view,
    )

    ship_sanctions_report_view = ScreeningShipSanctionsReportView.as_view(
        'ship_sanctions_report', openapi_spec, authentication,
        screenings_reports_repository,
    )

    api_v1.add_url_rule(
        '/screenings/<screening_id>/reports/ship_sanctions',
        view_func=ship_sanctions_report_view,
    )

    ship_country_sanctions_report_view = ScreeningCountrySanctionsReportView.\
        as_view(
            'country_sanctions_report', openapi_spec, authentication,
            screenings_reports_repository,
        )

    api_v1.add_url_rule(
        '/screenings/<screening_id>/reports/country_sanctions',
        view_func=ship_country_sanctions_report_view,
    )

    ship_movements_report_view = ScreeningShipMovementsReportView.as_view(
        'ship_movements_report', openapi_spec, authentication,
        screenings_reports_repository,
    )

    api_v1.add_url_rule(
        '/screenings/<screening_id>/reports/ship_movements',
        view_func=ship_movements_report_view,
    )

    screening_pdf_report_view = ScreeningPdfReportView.as_view(
        'screening_pdf_report', openapi_spec, authentication,
        screenings_repository,
        screenings_reports_repository,
        'screening_report.html',
    )

    api_v1.add_url_rule(
        '/screenings/<screening_id>/report',
        view_func=screening_pdf_report_view,
    )

    screening_history_pdf_report_view = ScreeningPdfReportView.as_view(
        'screening_history_pdf_report', openapi_spec, authentication,
        screenings_repository,
        screenings_history_repository,
        'screening_report.html',
    )

    api_v1.add_url_rule(
        '/screenings/<screening_id>/history/<history_id>/report',
        view_func=screening_history_pdf_report_view,
    )

    app.register_blueprint(api_v1, url_prefix='/v1')

    app.heartbeat_cache_region = heartbeat_cache_region
    app.authentication = authentication
    app.session_factory = session_factory
    app.blacklisted_countries_repository = blacklisted_countries_repository
    app.sis_companies_repository = sis_companies_repository
    app.compliance_entities_repository = compliance_entities_repository
    app.compliance_sanctions_repository = compliance_sanctions_repository
    app.ships_repository = ships_repository
    app.screenings_repository = screenings_repository
    app.screenings_history_repository = screenings_history_repository
    app.bulk_screenings_repository = bulk_screenings_repository
    app.ship_inspections_repository = ship_inspections_repository
    app.ship_sanctions_repository = ship_sanctions_repository
    app.ship_movements_repository = ship_movements_repository
    app.screenings_reports_repository = screenings_reports_repository

    app.jinja_env.filters['datetime'] = format_datetime
    app.jinja_env.filters['date'] = format_date
    app.jinja_env.filters['severity'] = format_severity
    app.jinja_env.filters['title_severity'] = format_title_severity
    app.jinja_env.filters['border_severity'] = format_border_severity

    return app
