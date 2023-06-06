import responses
import json
import pytest

from requests.exceptions import HTTPError

from screening_workers.lib.smh_api.smh_client import SMHClient
from screening_workers.lib.exceptions import ClientError


class TestSmhClient:
    @pytest.fixture
    def client(self):
        """Returns an AIS client"""
        return SMHClient("http://test/api/v1", "one", "pass")

    @responses.activate
    def test_get_smh(self, client):
        response = {
            'metadata': {},
            'visits': [
                {
                  "departed": None,
                  "entered": "2020-04-07T12:31:05Z",
                  "heading": 26.0,
                  "ihs_port_name": ", , ",
                  "latitude": 9.444067,
                  "longitude": -79.952805,
                  "port": {
                    "port_code": "PAONX",
                    "port_country_name": "Panama",
                    "port_latitude": 9.366666793823242,
                    "port_longitude": -79.91666412353516,
                    "port_name": "Col\u00f3n"
                  },
                  "sail_date_full": None,
                  "speed": 0.1,
                  "type": "At anchor"
                }
            ],
            "positions": [
                {
                    "timestamp": "2019-09-27T20:59:39Z",
                    "speed": 10.2,
                    "heading": 275,
                    "latitude": 39.224550,
                    "longitude": -76.538167,
                    "status": "Moored"
                }
            ],
            "ihs_movement_data": []
        }

        responses.add(
            responses.GET,
            'http://test/api/v1/shipmovementhistory/9155107',
            status=200, body=json.dumps(response),
        )

        resp = client.get_smh('9155107')
        visits = resp['visits']

        assert len(visits) == 1
        assert 'metadata' in response
        assert visits[0]['entered'] == "2020-04-07T12:31:05Z"
        assert visits[0]["port"]["port_code"] == "PAONX"

    @responses.activate
    def test_get_smh_exception(self, client):
        responses.add(
            responses.GET,
            'http://test/api/v1/shipmovementhistory/9155107',
            status=200, body=Exception)
        with pytest.raises(ClientError):
            client.get_smh('9155107')

    @responses.activate
    def test_get_smh_status_500(self, client):
        responses.add(
            responses.GET,
            'http://test/api/v1/shipmovementhistory/9155107',
            status=500, body='{}')
        with pytest.raises(HTTPError):
            client.get_smh('9155107')

    @responses.activate
    def test_get_port_data(self, client):
        response = {'data': 'Bayonne',
                    'field': 'port_name',
                    'port_code': 'FRBAY',
                    'port_country_name': 'France',
                    'port_name': 'Bayonne',
                    'version': '0.1.3'}
        responses.add(
            responses.GET,
            'http://test/api/v1/portdata/?field=port_name&value=Bayonne',
            status=200, body=json.dumps(response),
        )

        resp = client.get_port_data(field='port_name', value='Bayonne')

        assert 'data' in response
        assert resp['port_code'] == "FRBAY"
        assert resp["port_country_name"] == "France"

    @responses.activate
    def test_get_port_data_exception(self, client):
        responses.add(
            responses.GET,
            'http://test/api/v1/portdata/?field=port_name&value=Bayonne',
            status=200, body=Exception)
        with pytest.raises(ClientError):
            client.get_port_data(field='port_name', value='Bayonne')

    @responses.activate
    def test_get_port_data_500(self, client):
        responses.add(
            responses.GET,
            'http://test/api/v1/portdata/?field=port_name&value=Bayonne',
            status=500, body='{}')
        with pytest.raises(HTTPError):
            client.get_port_data(field='port_name', value='Bayonne')

    @responses.activate
    def test_get_status(self, client):
        response = {
            'client_ip': '10.44.20.225',
            'msg': 'SMH Service',
            'route': '/api/v1/system/status',
            'status_code': 200,
            'version': '0.1.3'
        }
        responses.add(
            responses.GET,
            'http://test/api/v1/system/status',
            status=200, body=json.dumps(response),
        )

        resp = client.system_status()

        assert 'msg' in response
        assert resp['status_code'] == 200
        assert resp["route"] == '/api/v1/system/status'
