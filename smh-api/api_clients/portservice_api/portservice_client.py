"""The Python implementation of the GRPC portservice client."""
import time
from datetime import datetime

import grpc

from ps_env_config import config
from api_clients.utils import str2date, json_logger
from api_clients.portservice_api import portservice_pb2 as service_pb2


class PortServiceClient(object):
    def __init__(self, server_url, log_level='INFO'):
        self.server_url = server_url
        self.logger = json_logger(__name__, level=log_level)
        self.channel = grpc.insecure_channel(self.server_url)

        try:
            if config.get('PORT_SERVICE_MESSAGE_VERSION') < '2.3':
                from api_clients.portservice_api import service_pb2
                from api_clients.portservice_api import service_pb2_grpc
            else:

                from api_clients.portservice_api import \
                    portservice_pb2_grpc as service_pb2_grpc
        except:
            from api_clients.portservice_api import \
                portservice_pb2_grpc as service_pb2_grpc

        self.stub = service_pb2_grpc.FindPortStub(self.channel)

    def check_port(self):
        pos = {'latitude': 0, 'longitude': 0}
        self.get_port(pos)

    def get_port(self, position) -> dict:

        ts = int(str2date(position.get('timestamp', '2000-01-01')).
                 timestamp())
        response = self.stub.FindNearestPort(
            service_pb2.Position(timestamp=ts,
                                 latitude=position['latitude'],
                                 longitude=position['longitude']))

        resp_dict = {'port_name': response.name, 'port_code': response.code,
                     'port_country_name': response.country_name}

        return resp_dict

    def get_port_data(self, field, value):

        response = self.stub.GetPort(
            service_pb2.Data(field=field, value=value))

        if response.code == '0':
            return None

        resp_dict = \
            {
                'port_name': response.name,
                'port_code': response.code,
                'port_country_name': response.country_name
            }

        return resp_dict

    def get_ports(self, positions) -> list:

        position_request = []
        for pos in positions:
            ts = int(str2date(pos['timestamp']).timestamp())
            position_request.append(
                service_pb2.Position(timestamp=ts,
                                     latitude=float(pos['latitude'] or 90),
                                     longitude=float(pos['longitude'] or 180)))

        responses = self.stub.FindClosestPorts(iter(position_request))
        for response in responses:
            visit = \
                {
                    'port_name': response.name,
                    'port_country_name': response.country_name,
                    'port_code': response.code,
                    'port_latitude': response.latitude,
                    'port_longitude': response.longitude
                }
            yield visit

    def get_port_history(self, positions) -> list:

        position_request = []
        for pos in positions:
            ts = int(str2date(pos['timestamp']).timestamp())
            position_request.append(
                service_pb2.Position(timestamp=ts, latitude=pos['latitude'],
                                     longitude=pos['longitude']))

        visits = self.stub.GetPortHistory(iter(position_request))

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
            self.logger.debug("PortService client received: %s %s %s" % (
                visit, datetime.fromtimestamp(response.timestamp_enter),
                datetime.fromtimestamp(response.timestamp_exit)
            ))
            port_visits.append(visit)

        return port_visits
