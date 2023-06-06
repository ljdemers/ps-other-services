import grpc

from screening_api.lib.health.enums import HealthStatus
from screening_api.lib.health.models import Health


class BaseIndicator:

    def health(self):
        raise NotImplementedError


class PortsIndicator(BaseIndicator):

    service_type = 'ports'

    def __init__(self, client):
        self.client = client

    def health(self) -> Health:
        errors = []

        notes = {
            'server_url': self.client.server_url
        }

        status = HealthStatus.FAILING
        try:
            resp = self.check_health()
        except grpc.RpcError as exc:
            errors.append(str(exc))
        else:
            if resp.status == resp.ServingStatus.SERVING:
                status = HealthStatus.PASSING

        return Health(
            service_type=self.service_type,
            status=status, notes=notes, errors=[],
        )

    def check_health(self):
        return self.client.health_check()
