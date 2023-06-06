import logging
from statsd import StatsClient

from api_clients.utils import memoized
from api_clients.ais import AISClient
from api_clients.sis import SisClient
from api_clients.portservice_api.portservice_client import \
    PortServiceClient

from ps_env_config import config


logger = logging.getLogger(__name__)


@memoized
def ais_client():
    """ Connect to AIS.

    Returns:
        api_clients.ais.AISClient: AIS REST client.
    """
    return AISClient(
        host=config.get('AIS_REST_BASE_URL'),
        username=config.get('AIS_USERNAME'),
        key=config.get('AIS_PASSWORD')
    )


@memoized
def sis_client():
    """ Connect to the Polestar Ship Information Service.

    Returns:
        api_clients.sis.SisClient: A SIS REST client.
    """
    return SisClient(
        host=config.get('SIS_BASE_URL'),
        username=config.get('SIS_USERNAME'),
        key=config.get('SIS_API_KEY'),
    )


@memoized
def port_service_client():
    return PortServiceClient(
        config.get('PORT_SERVICE_BASE_URL'),
        config.get('LOG_LEVEL')
        )


def port_service_client_detect():
    return PortServiceClient(
        config.get('PORT_SERVICE_BASE_URL'),
        config.get('LOG_LEVEL')
        )


@memoized
def statsd_client():
    return StatsClient(
        host=config.get('STATSD_HOST'),
        port=int(config.get('STATSD_PORT')),
        prefix=f"{config.get('ENVIRONMENT')}.{config.get('STATSD_PREFIX')}"
    )
