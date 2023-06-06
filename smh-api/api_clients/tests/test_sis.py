import datetime
from unittest.mock import patch

from api_clients.base_client import ResponseDict
from api_clients.sis import SisClient


class TestSISClient:
    sis_client = SisClient(
            host='test',
            username='test',
            key='key'
    )

    @patch('api_clients.sis.SisClient.get')
    def test_list_ship_movement_history_by_imo(self, mock_base_client):
        """ Test ``list_ship_movement_history_by_imo``
        method in a successful call. """
        mock_response = ResponseDict(
            count=2,
            objects=[{"arrival_date": "2018-02-14",
                         "country_name": "Cote d'Ivoire",
                         "creation_date": "2018-02-18T08:47:17.425859",
                         "destination_port": "Abidjan",
                         "estimated_time_of_arrival": "2018-02-18T06:00:00",
                         "hours_in_port": 73, "id": 43335772,
                         "ihs_creation_date": "2018-02-17T18:15:58.473000",
                         "ihs_id": "97736771", "ihs_port_geo_id": "5557",
                         "ihs_port_id": "18346", "imo_id": "9467873",
                         "last_port_of_call_arrival_date":
                             "2018-02-14T15:59:29",
                         "last_port_of_call_code": "7982",
                         "last_port_of_call_country": "Cote d'Ivoire",
                         "last_port_of_call_country_code": "CI",
                         "last_port_of_call_name": "San Pedro "
                                                   "(Cote d'Ivoire) Anchorage",
                         "last_port_of_call_sail_date": "2018-02-14T16:43:49",
                         "latitude": "4.734900", "longitude": "-6.611617",
                         "movement_type": "",
                         "port_name": "San Pedro (Cote d'Ivoire)",
                         "resource_uri": "/api/v1/ship_movement/43335772",
                         "sail_date": "2018-02-17",
                         "sail_date_full": "2018-02-17T17:59:25",
                         "ship_name": "BLUE CAT",
                         "ship_type": "Bulk Carrier",
                         "timestamp": "2018-02-14T16:43:49"},
                        {"arrival_date": "2017-12-26", "country_name": "Japan",
                         "creation_date": "2018-01-07T08:45:16.700541",
                         "destination_port": "Singapore",
                         "estimated_time_of_arrival": "2018-01-15T22:00:00",
                         "hours_in_port": 254, "id": 41814938,
                         "ihs_creation_date": "2018-01-06T12:11:58.857000",
                         "ihs_id": "96197720", "ihs_port_geo_id": "1473",
                         "ihs_port_id": "15680", "imo_id": "9467873",
                         "last_port_of_call_arrival_date":
                             "2017-12-24T11:48:56",
                         "last_port_of_call_code": "6815",
                         "last_port_of_call_country": "Japan",
                         "last_port_of_call_country_code": "JAP",
                         "last_port_of_call_name": "Yokkaichi and Nagoya "
                                                   "Outer Anchorage",
                         "last_port_of_call_sail_date": "2017-12-26T21:50:49",
                         "latitude": "35.029917", "longitude": "136.850783",
                         "movement_type": "", "port_name": "Nagoya",
                         "resource_uri": "/api/v1/ship_movement/41814938",
                         "sail_date": "2018-01-06",
                         "sail_date_full": "2018-01-06T11:56:12",
                         "ship_name": "BLUE CAT", "ship_type": "Bulk Carrier",
                         "timestamp": "2017-12-26T21:50:49"}
                        ]
        )
        mock_base_client.return_value = mock_response

        # The method must return the response from SIS.
        response = self.sis_client.list_ship_movement_history_by_imo('9467873')
        assert response == mock_response
