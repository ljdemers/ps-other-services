import pytest
from unittest import mock

from screening_workers.lib.ports_api.grpc_portservice_v1 import (
    portservice_pb2 as service_pb2,
)
from screening_workers.lib.ports_api.portservice_client \
    import PortServiceClient


class TestPortServiceClient:

    @pytest.fixture
    def client(self):
        """Returns a Port service client"""
        return PortServiceClient("test")

    @pytest.yield_fixture
    def mock_find_port(self, client):
        with mock.patch.object(client.find_ports_stub, 'FindNearestPort') as m:
            yield m

    def test_get_port(self, mock_find_port, client):

        port = service_pb2.Port()
        port.code = 'AOLAD'
        port.name = 'Luanda'
        port.country_code = 'Angola'

        mock_find_port.return_value = port
        position = {'latitude': -8.85, 'longitude': 13.25}

        result = client.get_port(position)

        assert 'port_code' in result
        assert 'port_name' in result
