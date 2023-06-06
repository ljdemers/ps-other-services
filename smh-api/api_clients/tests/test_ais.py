import datetime
from freezegun import freeze_time
from unittest.mock import patch

from api_clients.base_client import ResponseDict
from api_clients.ais import AISClient


class TestAISClient:
    ais_client = AISClient(
            host='test',
            username='test',
            key='key'
    )

    @patch('api_clients.ais.ApiClient.get')
    def test_get_ship_by_imo(self, mock_base_client):
        """ Test ``get_ship_by_imo`` method in a successful call. """
        mock_response = ResponseDict(
            count=1,
            data=[
                {
                    'call_sign': 'T8ZA',
                    'imo_number': 7011149,
                    'loa': 85,
                    'mmsi': 511012010,
                    'name': 'M/T SEA CZAR',
                    'ship_type': 'Tanker - all ships of this type',
                    'voyage_destination': 'SHARJAH HAMRIYAH',
                    'voyage_eta': '2019-07-05T15:00:00Z',
                    'voyage_timestamp': '2018-08-07T09:55:56Z'
                },
            ]
        )
        mock_base_client.return_value = mock_response

        # The method must return the response from AIS.
        response = self.ais_client.get_ship_by_imo('7011149')
        assert response == mock_response

    @patch('api_clients.ais.ApiClient.get')
    def test_get_ship_by_imo_two_ships(self, mock_base_client):
        """If there are two ships with the same IMO"""
        mock_response = ResponseDict(
            count=2,
            data=[
                {
                    "call_sign": "5IM314",
                    "imo_number": 7011149,
                    "loa": 89,
                    "mmsi": 677021400,
                    "name": "JULIA L.S.",
                    "position": "43.0,28.756",
                    "position_course": 2.6,
                    "position_speed": 8.7,
                    "position_timestamp": "2018-10-31T04:21:17Z",
                    "ship_type": "Cargo - all ships of this type",
                    "voyage_destination": "HAIFA",
                    "voyage_eta": "2018-10-22T20:00:00Z",
                    "voyage_timestamp": "2033-12-13T15:40:19Z"
                },
                {
                    "call_sign": "5IM314",
                    "imo_number": 7011149,
                    "loa": 89,
                    "mmsi": 675620952,
                    "name": "JULIA L.S.",
                    "ship_type": "Cargo - all ships of this type",
                    "voyage_destination": "SINES",
                    "voyage_eta": "2018-05-01T06:00:00Z",
                    "voyage_timestamp": "2018-04-26T16:19:10Z"
                }
            ])

        mock_base_client.return_value = mock_response

        # The method must return the response from AIS.
        response = self.ais_client.get_ship_by_imo('7901693')
        assert response.count == 1
        assert response.data[0]['position_timestamp'] == "2018-10-31T04:21:17Z"

    @patch('api_clients.ais.ApiClient.get')
    def test_get_ship_by_imo_latest(self, mock_base_client):
        """
        If AIS Service returns multiple entries for the same IMO, the one with
        the latest position must be selected.
        """
        # Mock up an unordered list of similar items. The differences are the
        # `position` and the `position_timestamp`. Our system will order them
        # by this `position_timestamp` to get the LATEST known position for the
        # ship. If there is NO `position_timestamp` in the response, the system
        # will gracefully handle it.
        response_data = [
            # 26th April 2019, 10:16:08 UTC. This must be the SECOND.
            {
                "call_sign": "OUJI2",
                "imo_number": 9359026,
                "loa": 367,
                "mmsi": 220595000,
                "name": "GUNHILDE MAERSK",
                "position": "6.905,-81.236",
                "position_course": 91.1,
                "position_speed": 14.7,
                "position_timestamp": "2019-04-26T10:16:08Z",
                "ship_type": "Cargo - No additional information",
                "voyage_destination": "KR BUS > PA PTY",
                "voyage_eta": "2019-04-27T03:00:00Z",
                "voyage_timestamp": "2033-12-24T13:06:46Z"
            },
            # 23rd April 2019, 10:12:05 UTC. This must be the THIRD.
            {
                "call_sign": "OUJI2",
                "imo_number": 9359026,
                "loa": 367,
                "mmsi": 220595000,
                "name": "GUNHILDE MAERSK",
                "position": "7.905,-80.236",
                "position_course": 91.1,
                "position_speed": 14.7,
                "position_timestamp": "2019-04-23T10:12:05Z",
                "ship_type": "Cargo - No additional information",
                "voyage_destination": "KR BUS > PA PTY",
                "voyage_eta": "2019-04-27T03:00:00Z",
                "voyage_timestamp": "2033-12-24T13:06:46Z"
            },
            # 12th March 2019, 03:01:19 UTC. This must be the FOURTH.
            {
                "call_sign": "OUJI2",
                "imo_number": 9359026,
                "loa": 367,
                "mmsi": 220595000,
                "name": "GUNHILDE MAERSK",
                "position": "2.132,-79.234",
                "position_course": 91.1,
                "position_speed": 14.7,
                "position_timestamp": "2019-03-12T03:01:19Z",
                "ship_type": "Cargo - No additional information",
                "voyage_destination": "KR BUS > PA PTY",
                "voyage_eta": "2019-04-27T03:00:00Z",
                "voyage_timestamp": "2033-12-24T13:06:46Z"
            },
            # 26th April 2019, 10:20:58 UTC. This must be the FIRST, the one
            # that gets actually returned as a result.
            {
                "call_sign": "OUJI2",
                "imo_number": 9359026,
                "loa": 367,
                "mmsi": 220595000,
                "name": "GUNHILDE MAERSK",
                "position": "6.905,-81.236",
                "position_course": 91.1,
                "position_speed": 14.7,
                "position_timestamp": "2019-04-26T10:20:58Z",
                "ship_type": "Cargo - No additional information",
                "voyage_destination": "KR BUS > PA PTY",
                "voyage_eta": "2019-04-27T03:00:00Z",
                "voyage_timestamp": "2033-12-24T13:06:46Z"
            },
            # NO `position_timestamp` in response! This must be the last.
            {
                "call_sign": "OUJI2",
                "imo_number": 9359026,
                "loa": 367,
                "mmsi": 220595000,
                "name": "GUNHILDE MAERSK",
                "position": "6.905,-81.236",
                "position_course": 91.1,
                "position_speed": 14.7,
                "ship_type": "Cargo - No additional information",
                "voyage_destination": "KR BUS > PA PTY",
                "voyage_eta": "2019-04-27T03:00:00Z",
                "voyage_timestamp": "2033-12-24T13:06:46Z"
            },
        ]
        mock_response = ResponseDict(count=5, data=response_data)

        mock_base_client.return_value = mock_response

        response = self.ais_client.get_ship_by_imo('9359026')
        assert response.count == 1
        assert response.data[0] == response_data[3]

    @patch('api_clients.ais.ApiClient.get')
    def test_get_ship_by_imo_not_found(self, mock_base_client):
        """
        Test ``get_ship_by_imo`` method in a 'not found' response from AIS.
        """
        # Mock the error response from 'Ship Information Service'.
        mock_response = ResponseDict(
            _error={
                'message': "AISClient request failed with status 404 "
                           "headers: {'Content-Type': 'application/json', "
                           "'Server': 'TornadoServer/5.1', 'Content-Length': "
                           "'69', 'Connection': 'keep-alive'}",
                'details': {
                    'full_url':
                        'http://commaisservice.polestarglobal-test.com'
                        '/api/v2/ship',
                    'kwr': {
                        'url':
                            'http://commaisservice.polestarglobal-test.com'
                            '/api/v2/ship',
                        'headers': {
                            'Content-Type': 'application/json',
                            'Accept': 'application/json'
                        },
                        'params': {'q': 'imo_number:6930661'}
                    }
                }
            }
        )
        mock_base_client.return_value = mock_response

        # The method must return the response from AIS.
        response = self.ais_client.get_ship_by_imo('7011149')
        assert response == mock_response

    @patch('api_clients.ais.ApiClient.get')
    def test_get_track(self, mock_base_client):
        mmsi = '220595000'
        self.ais_client.get_track(mmsi)
        mock_base_client.assert_called_once_with(
            url=f'/track/{mmsi}',
            params={'position_count': 500}
        )

    @patch('api_clients.ais.ApiClient.get')
    def test_get_track_frequency(self, mock_base_client):
        mmsi = '220595000'
        self.ais_client.get_track(mmsi, downsample_frequency_seconds=3600)
        mock_base_client.assert_called_once_with(
            url=f'/track/{mmsi}',
            params={'position_count': 500, 'downsample_frequency_seconds': 3600}
        )

    @patch('api_clients.ais.ApiClient.get')
    def test_get_track_frequency_not_used(self, mock_base_client):
        mmsi = '220595000'
        self.ais_client.get_track(mmsi, downsample_frequency_seconds=0)
        mock_base_client.assert_called_once_with(
            url=f'/track/{mmsi}',
            params={'position_count': 500}
        )

    @patch('api_clients.ais.ApiClient.get')
    def test_get_track_with_limit(self, mock_base_client):
        mmsi = '220595077'
        response = self.ais_client.get_track(mmsi, 100)

        assert response == mock_base_client.return_value
        mock_base_client.assert_called_once_with(
            url=f'/track/{mmsi}',
            params={'position_count': 100}
        )

    @patch('api_clients.ais.ApiClient.get')
    def test_get_track_with_end_date(self, mock_base_client):
        mmsi = '220595077'
        response = self.ais_client.get_track(
            mmsi,
            end_date=datetime.datetime(2121, 4, 1)
        )

        assert response == mock_base_client.return_value
        mock_base_client.assert_called_once_with(
            url=f'/track/{mmsi}',
            params={'position_count': 500, 'end_date': '2121-04-01T00:00:00'}
        )

    @patch('api_clients.ais.ApiClient.get')
    def test_get_track_latest(self, mock_base_client):
        mmsi = '220595123'
        response = self.ais_client.get_track_latest(mmsi)

        assert response == mock_base_client.return_value
        mock_base_client.assert_called_once_with(
            url=f'/track/{mmsi}',
            params={'position_count': 1}
        )

    @patch('api_clients.ais.AISClient.get_ship_by_imo')
    def test_get_mmsi_from_imo_error_getting_ship(self, mock_get_ship_by_imo):
        imo = '9359026'
        mock_get_ship_by_imo.return_value.error = 'error'
        response = self.ais_client.get_mmsi_from_imo(imo)

        assert response is None

    @patch('api_clients.ais.AISClient.get_ship_by_imo')
    def test_get_mmsi_from_imo_invalid_response(self, mock_get_ship_by_imo):
        imo = '9359026'
        mock_get_ship_by_imo.return_value = ResponseDict({})
        response = self.ais_client.get_mmsi_from_imo(imo)

        assert response is None

    @patch('api_clients.ais.AISClient.get_ship_by_imo')
    def test_get_mmsi_from_imo(self, mock_get_ship_by_imo):
        imo = '9359026'
        mmsi = '220595123'
        mock_get_ship_by_imo.return_value = ResponseDict(
            {'data': [{'mmsi': mmsi}]}
        )
        response = self.ais_client.get_mmsi_from_imo(imo)

        assert mmsi == response

    @patch('api_clients.ais.ApiClient.get')
    def test_get_status(self, mock_base_client):
        mmsi = '220595123'
        response = self.ais_client.get_status(mmsi)

        assert response == mock_base_client.return_value
        mock_base_client.assert_called_once_with(f'/ship/{mmsi}')

    @patch('api_clients.ais.ApiClient.get')
    def test_system_status(self, mock_base_client):
        response = self.ais_client.system_status()

        assert response == mock_base_client.return_value
        mock_base_client.assert_called_once_with('/system/status')

    @patch('api_clients.ais.ApiClient.get')
    def test_list_ships_no_limit(self, mock_base_client):
        params = {'p': 1}
        response = self.ais_client.list_ships(params)

        assert response == mock_base_client.return_value
        params['limit'] = 20
        mock_base_client.assert_called_once_with('/ship', params=params)

    @patch('api_clients.ais.ApiClient.get')
    def test_list_ships_with_limit(self, mock_base_client):
        params = {'p': 1, 'limit': 4}
        response = self.ais_client.list_ships(params)

        assert response == mock_base_client.return_value
        mock_base_client.assert_called_once_with('/ship', params=params)

    @patch('api_clients.ais.ApiClient.get')
    def test_list_ships_with_limit_over_maximum(self, mock_base_client):
        params = {'p': 1, 'limit': 21}
        response = self.ais_client.list_ships(params)

        assert response == mock_base_client.return_value
        params['limit'] = 20
        mock_base_client.assert_called_once_with('/ship', params=params)
