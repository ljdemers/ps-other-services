"""The Python implementation of the GRPC portservice client."""

import grpc
import time
from datetime import datetime
from screening_workers.lib.utils import str2date, json_logger
from screening_workers.lib.ports_api.grpc_health_v1 import (
    health_pb2, health_pb2_grpc,
)
from screening_workers.lib.ports_api.grpc_portservice_v1 import (
    portservice_pb2 as service_pb2, portservice_pb2_grpc as service_pb2_grpc,
)


class PortServiceClient(object):
    def __init__(self, server_url, log_level='INFO'):
        self.server_url = server_url
        self.logger = json_logger(__name__, level=log_level)
        self.channel = grpc.insecure_channel(self.server_url)
        self.health_stub = health_pb2_grpc.HealthStub(self.channel)
        self.find_ports_stub = service_pb2_grpc.FindPortStub(self.channel)

    def health_check(self, service=''):
        request = health_pb2.HealthCheckRequest(service=service)
        return self.health_stub.Check(request)

    def get_port(self, position) -> dict:
        ts = int(str2date(position.get('timestamp', '2000-01-01')).
                 timestamp())
        response = self.find_ports_stub.FindNearestPort(
            service_pb2.Position(timestamp=ts,
                                 latitude=position['latitude'],
                                 longitude=position['longitude']))

        resp_dict = {'port_name': response.name, 'port_code': response.code,
                     'port_country_name': response.country_name}

        return resp_dict

    def get_port_data(self, field, value):
        response = self.find_ports_stub.GetPort(
            service_pb2.Data(field=field, value=value))

        if response.code == '0':
            return None
        else:
            resp_dict = \
                {
                    'port_name': response.name,
                    'port_code': response.code,
                    'port_country_name': response.country_name
                }

            return resp_dict

    def get_ports(self, positions) -> (list, float):
        st = time.time()
        position_request = []
        for pos in positions:
            ts = int(str2date(pos['timestamp']).timestamp())
            position_request.append(
                service_pb2.Position(timestamp=ts, latitude=pos['latitude'],
                                     longitude=pos['longitude']))

        ports = []
        responses = self.find_ports_stub.FindClosestPorts(
            iter(position_request))
        for response in responses:
            visit = \
                {
                    'port_name': response.name,
                    'port_country_name': response.country_name,
                    'port_code': response.code,
                    'port_latitude': response.latitude,
                    'port_longitude': response.longitude
                }
            ports.append(visit)

        et = time.time()

        self.logger.info(
            "Port history done successfully in " + str(et - st) + " sec.")
        return ports, et - st

    def get_port_history(self, positions) -> list:
        position_request = []
        for pos in positions:
            ts = int(str2date(pos['timestamp']).timestamp())
            position_request.append(
                service_pb2.Position(timestamp=ts, latitude=pos['latitude'],
                                     longitude=pos['longitude']))

        visits = self.find_ports_stub.GetPortHistory(iter(position_request))

        port_visits = []
        for response in visits:
            depart = response.timestamp_exit
            port = {
                 'port_name': response.port.name,
                 'port_country_name': response.port.country_name,
                 'port_code': response.port.code,
                 'port_latitude': response.port.latitude,
                 'port_longitude': response.port.longitude
            }
            visit = {
                        'entered': response.timestamp_enter,
                        'departed': None if depart == 0 else depart,
                        'port': port
                    }
            self.logger.info("PortService client received: %s %s %s" % (
                visit, datetime.fromtimestamp(response.timestamp_enter),
                datetime.fromtimestamp(response.timestamp_exit)
            ))
            port_visits.append(visit)

        return port_visits
