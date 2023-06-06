from datetime import datetime, timedelta
from socket import socket, AF_INET, SOCK_DGRAM

from screening_api.lib.health.enums import HealthStatus
from screening_api.lib.health.models import Health
from screening_api.lib.messaging.caches import TimestampCache


class Healths(list):

    unhealthy_statuses = [HealthStatus.FAILING, ]

    def __json__(self) -> dict:
        return list(map(lambda x: x.__json__(), self))

    def is_healthy(self) -> bool:
        return all(
            health.status not in self.unhealthy_statuses
            for health in self
        )


class BaseIndicator:

    def health(self) -> Health:
        raise NotImplementedError


class Indicators(list):

    def __init__(self, *indicators):
        super(Indicators, self).__init__(indicators)

    def get_healths(self) -> Healths:
        return Healths(map(lambda x: x.health(), self))


class AlchemyIndicator(BaseIndicator):

    service_type = 'database'

    def __init__(self, database):
        self.database = database

    def health(self) -> Health:
        notes = {
            'drivername': self.database.engine.url.drivername,
        }

        status = HealthStatus.FAILING
        if self._is_connected():
            status = HealthStatus.PASSING

        return Health(
            service_type=self.service_type,
            status=status, notes=notes, errors=[],
        )

    def _is_connected(self):
        connection = self.database.engine.connect()
        try:
            result = connection.execute("SELECT 1 AS is_alive").fetchone()
            return result['is_alive'] == 1
        except:
            return False


class KombuIndicator(BaseIndicator):

    service_type = 'broker'

    def __init__(self, broker):
        self.broker = broker

    def health(self) -> Health:
        notes = {
            'transport': self.broker.transport_cls,
        }

        status = HealthStatus.FAILING
        if self._is_connected():
            status = HealthStatus.PASSING

        return Health(
            service_type=self.service_type,
            status=status, notes=notes, errors=[],
        )

    def _is_connected(self):
        self.broker.connect()
        result = self.broker.connected
        self.broker.release()
        return result


class HeartbeatIndicator(BaseIndicator):

    service_type = 'beat'
    heartbeat_due = timedelta(minutes=3)

    def __init__(self, cache: TimestampCache):
        self.cache = cache

    def health(self) -> Health:
        errors = []

        heartbeat = self._get_heartbeat()

        heartbeat_timestamp = heartbeat.get('timestamp')

        status = HealthStatus.FAILING
        if heartbeat_timestamp is not None:
            overdue = self._is_heartbeat_overdue(heartbeat_timestamp)
            status = HealthStatus.WARNING if overdue else HealthStatus.PASSING
        else:
            errors.append('No heartbeat timestamp')

        return Health(
            service_type=self.service_type,
            status=status, notes=heartbeat, errors=errors,
        )

    def _get_heartbeat(self):
        try:
            return self.cache.get()
        except KeyError:
            return {}

    def _is_heartbeat_overdue(self, heartbeat_timestamp: datetime):
        utcnow = datetime.utcnow()
        return heartbeat_timestamp + self.heartbeat_due < utcnow


class XRayIndicator(BaseIndicator):

    service_type = 'xray'

    def __init__(self, recorder):
        self.recorder = recorder

    def health(self) -> Health:
        notes = {
            'service': self.service,
            'context_missing': self.context_missing,
            'daemon_address': self.daemon_address,
        }

        status = HealthStatus.FAILING
        if self.service is None:
            status = HealthStatus.DISABLED
        elif self._is_connected():
            status = HealthStatus.PASSING

        return Health(
            service_type=self.service_type,
            status=status, notes=notes, errors=[],
        )

    @property
    def service(self):
        return self.recorder._service

    @property
    def context_missing(self):
        return self.recorder.context.context_missing

    @property
    def ip(self):
        return self.recorder.emitter._ip

    @property
    def port(self):
        return self.recorder.emitter._port

    @property
    def daemon_address(self):
        return ':'.join([self.ip, str(self.port)])

    def _is_connected(self):
        if not self.service:
            return False

        sock = socket(AF_INET, SOCK_DGRAM)
        code = sock.connect_ex((self.ip, self.port))
        sock.close()
        return code == 0
