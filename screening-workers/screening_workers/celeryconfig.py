from distutils.util import strtobool
import os
from urllib.parse import urlunparse

from kombu import Queue


def get_url(scheme, host='localhost', path='', user='', password='', port=''):
    netloc = host
    if port:
        netloc = '{0}:{1}'.format(host, port)
    if user and password:
        netloc = '{0}:{1}@{2}'.format(user, password, netloc)

    return urlunparse((scheme, netloc, path, None, None, None))


def get_redis_url(dbhost, dbname, dbuser='', dbpassword='', port='6379'):
    return get_url('redis', dbhost, dbname, dbuser, dbpassword, port='6379')

accept_content = ['json', 'extended-json']
task_serializer = 'extended-json'
result_serializer = 'extended-json'

beat_max_loop_interval = os.environ.get('BEAT_MAX_LOOP_INTERVAL', '0')
if beat_max_loop_interval is not None:
    beat_max_loop_interval = int(beat_max_loop_interval)
broker_url = get_url(
    os.environ.get('BROKERBACKEND', 'redis'),
    os.environ['BROKERHOST'], os.environ.get('BROKERNAME', '0'),
    os.environ.get('BROKERUSER', ''), os.environ.get('BROKERPASSWORD', ''),
    os.environ.get('BROKERPORT', '6379'),
)
result_backend = get_redis_url(
    os.environ['RESULTHOST'], os.environ.get('RESULTNAME', '1'),
)
include = ['screening_workers']

metrics_enable = os.environ.get('METRICS_ENABLE', '0')
if metrics_enable is not None:
    metrics_enable = strtobool(metrics_enable)
metrics_namespace = os.environ.get('METRICS_NAMESPACE', '')

redbeat_redis_url = get_redis_url(
    os.environ['REDBEATHOST'], os.environ.get('REDBEATNAME', '0'),
)
redbeat_key_prefix = os.environ.get('REDBEAT_KEY_PREFIX', 'redbeat')
redbeat_lock_key = os.environ.get(
    'REDBEAT_LOCK_KEY', '{0}:lock'.format(redbeat_key_prefix))
redbeat_lock_timeout = os.environ.get(
    'REDBEAT_LOCK_TIMEOUT', 5*beat_max_loop_interval)
if redbeat_lock_timeout is not None:
    redbeat_lock_timeout = int(redbeat_lock_timeout)

screenings_bulk_screen_time = os.environ.get(
    'SCREENINGS_BULK_SCREEN_TIME', '0 1 * * *')

statsd_host = os.environ.get('STATSD_HOST', '127.0.0.1')
statsd_port = os.environ.get('STATSD_PORT', '8125')
if statsd_port is not None:
    statsd_port = int(statsd_port)
statsd_prefix = os.environ.get('STATSD_PREFIX')

task_default_queue = os.environ.get('TASK_DEFAULT_QUEUE', 'screening')
task_queues = [
    Queue('heartbeat', routing_key='heartbeat'),
    Queue(task_default_queue, routing_key='screening'),
    Queue(
        'screening.bulk_screenings.validation',
        routing_key='screening.bulk_screenings.validation',
    ),
    Queue(
        'screening.company_sanctions.ship_beneficial_owner_check',
        routing_key='screening.company_sanctions.ship_beneficial_owner_check',
    ),
    Queue(
        'screening.company_sanctions.ship_company_associates_check',
        routing_key=(
            'screening.company_sanctions.ship_company_associates_check'
        ),
    ),
    Queue(
        'screening.company_sanctions.ship_manager_check',
        routing_key='screening.company_sanctions.ship_manager_check',
    ),
    Queue(
        'screening.company_sanctions.ship_operator_check',
        routing_key='screening.company_sanctions.ship_operator_check',
    ),
    Queue(
        'screening.company_sanctions.ship_registered_owner_check',
        routing_key='screening.company_sanctions.ship_registered_owner_check',
    ),
    Queue(
        'screening.company_sanctions.ship_technical_manager_check',
        routing_key='screening.company_sanctions.ship_technical_manager_check',
    ),
    Queue(
        'screening.country_sanctions.doc_company_check',
        routing_key='screening.country_sanctions.doc_company_check',
    ),
    Queue(
        'screening.country_sanctions.ship_beneficial_owner_check',
        routing_key='screening.country_sanctions.ship_beneficial_owner_check',
    ),
    Queue(
        'screening.country_sanctions.ship_flag_check',
        routing_key='screening.country_sanctions.ship_flag_check',
    ),
    Queue(
        'screening.country_sanctions.ship_manager_check',
        routing_key='screening.country_sanctions.ship_manager_check',
    ),
    Queue(
        'screening.country_sanctions.ship_operator_check',
        routing_key='screening.country_sanctions.ship_operator_check',
    ),
    Queue(
        'screening.country_sanctions.ship_registered_owner_check',
        routing_key='screening.country_sanctions.ship_registered_owner_check',
    ),
    Queue(
        'screening.country_sanctions.ship_technical_manager_check',
        routing_key='screening.country_sanctions.ship_technical_manager_check',
    ),
    Queue(
        'screening.screenings.bulk_screen',
        routing_key='screening.screenings.bulk_screen',
    ),
    Queue(
        'screening.screenings.screen',
        routing_key='screening.screenings.screen',
    ),
    Queue(
        'screening.screenings.screen_killer',
        routing_key='screening.screenings.screen_killer',
    ),
    Queue(
        'screening.screenings.bulk_screen_killer',
        routing_key='screening.screenings.bulk_screen_killer',
    ),
    Queue(
        'screening.ship_inspections.ship_inspections_check',
        routing_key='screening.ship_inspections.ship_inspections_check',
    ),
    Queue(
        'screening.ship_movements.port_visits_check',
        routing_key='screening.ship_movements.port_visits_check',
    ),
    Queue(
        'screening.ship_movements.zone_visits_check',
        routing_key='screening.ship_movements.zone_visits_check',
    ),
    Queue(
        'screening.ship_sanctions.ship_association_check',
        routing_key='screening.ship_sanctions.ship_association_check',
    ),
    Queue(
        'screening.ship_sanctions.ship_sanction_check',
        routing_key='screening.ship_sanctions.ship_sanction_check',
    ),
    Queue(
        'screening.ships.ship_cache_update',
        routing_key='screening.ships.ship_cache_update',
    ),
    Queue(
        'screening.ships.ships_cache_update',
        routing_key='screening.ships.ships_cache_update',
    ),
]
task_routes = {
    'heartbeat': {'queue': 'heartbeat'},
    'screening.bulk_screenings.validation': {
        'queue': 'screening.bulk_screenings.validation',
    },
    'screening.company_sanctions.ship_beneficial_owner_check': {
        'queue': 'screening.company_sanctions.ship_beneficial_owner_check',
    },
    'screening.company_sanctions.ship_company_associates_check': {
        'queue': 'screening.company_sanctions.ship_company_associates_check',
    },
    'screening.company_sanctions.ship_manager_check': {
        'queue': 'screening.company_sanctions.ship_manager_check',
    },
    'screening.company_sanctions.ship_operator_check': {
        'queue': 'screening.company_sanctions.ship_operator_check',
    },
    'screening.company_sanctions.ship_registered_owner_check': {
        'queue': 'screening.company_sanctions.ship_registered_owner_check',
    },
    'screening.company_sanctions.ship_technical_manager_check': {
        'queue': 'screening.company_sanctions.ship_technical_manager_check',
    },
    'screening.country_sanctions.doc_company_check': {
        'queue': 'screening.country_sanctions.doc_company_check',
    },
    'screening.country_sanctions.ship_beneficial_owner_check': {
        'queue': 'screening.country_sanctions.ship_beneficial_owner_check',
    },
    'screening.country_sanctions.ship_flag_check': {
        'queue': 'screening.country_sanctions.ship_flag_check',
    },
    'screening.country_sanctions.ship_manager_check': {
        'queue': 'screening.country_sanctions.ship_manager_check',
    },
    'screening.country_sanctions.ship_operator_check': {
        'queue': 'screening.country_sanctions.ship_operator_check',
    },
    'screening.country_sanctions.ship_registered_owner_check': {
        'queue': 'screening.country_sanctions.ship_registered_owner_check',
    },
    'screening.country_sanctions.ship_technical_manager_check': {
        'queue': 'screening.country_sanctions.ship_technical_manager_check',
    },
    'screening.screenings.bulk_screen': {
        'queue': 'screening.screenings.bulk_screen',
    },
    'screening.screenings.screen': {
        'queue': 'screening.screenings.screen',
    },
    'screening.screenings.screen_killer': {
        'queue': 'screening.screenings.screen_killer',
    },
    'screening.screenings.bulk_screen_killer': {
        'queue': 'screening.screenings.bulk_screen_killer',
    },
    'screening.ship_inspections.ship_inspections_check': {
        'queue': 'screening.ship_inspections.ship_inspections_check',
    },
    'screening.ship_movements.port_visits_check': {
        'queue': 'screening.ship_movements.port_visits_check',
    },
    'screening.ship_movements.zone_visits_check': {
        'queue': 'screening.ship_movements.zone_visits_check',
    },
    'screening.ship_sanctions.ship_association_check': {
        'queue': 'screening.ship_sanctions.ship_association_check',
    },
    'screening.ship_sanctions.ship_sanction_check': {
        'queue': 'screening.ship_sanctions.ship_sanction_check',
    },
    'screening.ships.ship_cache_update': {
        'queue': 'screening.ships.ship_cache_update',
    },
    'screening.ships.ships_cache_update': {
        'queue': 'screening.ships.ships_cache_update',
    },
    'screening.*': {'queue': task_default_queue},
}
task_time_limit = os.environ.get('TASK_TIME_LIMIT', None)
if task_time_limit is not None:
    task_time_limit = int(task_time_limit)
task_soft_time_limit = os.environ.get('TASK_SOFT_TIME_LIMIT', None)
if task_soft_time_limit is not None:
    task_soft_time_limit = int(task_soft_time_limit)
task_smc_soft_time_limit = os.environ.get('TASK_SMC_SOFT_TIME_LIMIT', None)
if task_smc_soft_time_limit is not None:
    task_smc_soft_time_limit = int(task_smc_soft_time_limit)
worker_hijack_root_logger = os.environ.get('WORKER_HIJACK_ROOT_LOGGER', None)
if worker_hijack_root_logger is not None:
    worker_hijack_root_logger = bool(worker_hijack_root_logger)
worker_pool = os.environ.get('WORKER_POOL', 'prefork')
worker_concurrency = os.environ.get('WORKER_CONCURRENCY', None)
if worker_concurrency is not None:
    worker_concurrency = int(worker_concurrency)
