import responses
import json
import pytest

from requests.exceptions import HTTPError

from screening_workers.lib.utils import str2date
from screening_workers.lib.ais_api.ais_client import AISClient
from screening_workers.lib.exceptions import ClientError


class TestAisClient:
    @pytest.fixture
    def client(self):
        """Returns an AIS client"""
        return AISClient("http://test", "one", "pass")

    @responses.activate
    def test_get_track(self, client):
        response = {
            "next_link": "/api/v2/track/355443000?"
                         "end_date=2017-10-31T00:20:37Z",
            'count': 2,
            'data': [
                {'latitude': 25.164644, 'channel': 'A', 'source': 'T',
                 'status': 'At anchor', 'heading': 354.0,
                 'longitude': 54.814522, 'timestamp': '2018-01-11T19:24:37Z',
                 'course': 37.7,
                 'extdata': {'msgtype': 3}, 'mmsi': 355443000, 'speed': 0.0},
                {'latitude': 36.241699, 'channel': None, 'source': 'T',
                 'status': None, 'heading': 258.0,
                 'longitude': -3.79616, 'timestamp': '2017-12-12T19:36:45Z',
                 'course': 260.0,
                 'extdata': {'msgtype': 1}, 'mmsi': 355443000, 'speed': 14.7}
            ],
        }
        responses.add(
            responses.GET,
            'http://test/api/v2/track/355443000?position_count=10',
            status=200, body=json.dumps(response),
        )

        resp, code = client.get_track('355443000', position_count=10)
        data = resp['data']

        assert code == 200
        assert resp['count'] == 2
        assert len(data) == 2
        assert data[0]['status'] == 'At anchor'
        assert data[0]['mmsi'] == 355443000
        assert data[1]['status'] is None

    @responses.activate
    def test_get_track_exception(self, client):
        responses.add(
            responses.GET,
            'http://test/api/v2/track/355443000',
            status=200, body=Exception)
        with pytest.raises(ClientError):
            client.get_track('355443000')

    @responses.activate
    def test_get_track_status_500(self, client):
        responses.add(
            responses.GET,
            'http://test/api/v2/track/355443000',
            status=500, body='{}')
        with pytest.raises(HTTPError):
            client.get_track('355443000')

    @responses.activate
    def test_get_all_track(self, client):
        response1 = {
            "next_link": "/api/v2/track/355443000?"
                         "end_date=2017-11-30T00:20:37Z",
            'count': 1,
            'data': [
                {'latitude': 25.164644, 'channel': 'A', 'source': 'T',
                 'status': 'At anchor', 'heading': 354.0,
                 'longitude': 54.814522, 'timestamp': '2018-01-11T19:24:37Z',
                 'course': 37.7,
                 'extdata': {'msgtype': 3}, 'mmsi': 355443000, 'speed': 0.0}
            ],
        }
        response2 = {
            "next_link": "/api/v2/track/355443000?"
                         "end_date=2017-10-31T00:20:37Z",
            'count': 1,
            'data': [
                {'latitude': 36.241699, 'channel': None, 'source': 'T',
                 'status': None, 'heading': 258.0,
                 'longitude': -3.79616, 'timestamp': '2017-12-12T19:36:45Z',
                 'course': 260.0,
                 'extdata': {'msgtype': 1}, 'mmsi': 355443000, 'speed': 14.7}
            ],
        }
        responses.add(
            responses.GET,
            'http://test/api/v2/track/355443000',
            status=200, body=json.dumps(response1),
        )
        responses.add(
            responses.GET,
            'http://test/api/v2/track/355443000?'
            'end_date=2017-11-30T00:20:37Z',
            status=200, body=json.dumps(response2),
        )
        # No more data
        responses.add(
            responses.GET,
            'http://test/api/v2/track/355443000?'
            'end_date=2017-10-31T00:20:37Z',
            status=404, body=json.dumps({}),
        )

        data = client.get_all_track('355443000')

        assert len(data) == 2
        assert data[0]['status'] == 'At anchor'
        assert data[0]['mmsi'] == 355443000
        assert data[1]['status'] is None

    @responses.activate
    def test_get_all_track_with_stop_date(self, client):
        response1 = {
            "next_link": "/api/v2/track/355443000?"
                         "end_date=2017-12-30T00:20:37Z",
            'count': 1,
            'data': [
                {'latitude': 25.164644, 'channel': 'A', 'source': 'T',
                 'status': 'At anchor', 'heading': 354.0,
                 'longitude': 54.814522, 'timestamp': '2018-01-11T19:24:37Z',
                 'course': 37.7,
                 'extdata': {'msgtype': 3}, 'mmsi': 355443000, 'speed': 0.0}
            ],
        }
        response2 = {
            "next_link": "/api/v2/track/355443000?"
                         "end_date=2017-10-31T00:20:37Z",
            'count': 1,
            'data': [
                {'latitude': 36.241699, 'channel': None, 'source': 'T',
                 'status': None, 'heading': 258.0,
                 'longitude': -3.79616, 'timestamp': '2017-12-12T19:36:45Z',
                 'course': 260.0,
                 'extdata': {'msgtype': 1}, 'mmsi': 355443000, 'speed': 14.7}
            ],
        }
        responses.add(
            responses.GET,
            'http://test/api/v2/track/355443000',
            status=200, body=json.dumps(response1),
        )
        responses.add(
            responses.GET,
            'http://test/api/v2/track/355443000?end_date=2017-12-30T00:20:37Z',
            status=200, body=json.dumps(response2),
        )
        responses.add(
            responses.GET,
            'http://test/api/v2/track/355443000?end_date=2017-10-31T00:20:37Z',
            status=404, body=json.dumps({}),
        )

        # get just track with timestamp > 2018-01-01
        data = client.get_all_track('355443000',
                                    stop_date=str2date('2018-01-01'))

        assert len(data) == 1
        assert data[0]['status'] == 'At anchor'
        assert data[0]['mmsi'] == 355443000
