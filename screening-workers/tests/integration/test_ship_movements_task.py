import json
from socket import timeout
from unittest import mock
from freezegun import freeze_time
import pytest
import responses
from screening_api.screenings.enums import Severity, Status
from screening_workers.lib.blacklist import default_blacklisted_ports
from screening_workers.ship_movements.ihs_position import IHSPositionLogic
from screening_workers.ship_movements.checks import ShipMovementsCheck
from screening_workers.ship_movements.tasks import ShipMovementsCheckTask


class TestShipMovementsTask:
    @pytest.fixture
    def check(self, application, sis_client, smh_client,
              ais_client, portservice_client):
        return ShipMovementsCheck(
            application.screenings_repository,
            application.screenings_reports_repository,
            None,
            application.ships_repository,
            default_blacklisted_ports, smh_client,
            sis_client, {}, ais_client, portservice_client
        )

    @pytest.fixture
    def task(self, application):
        return application.tasks[ShipMovementsCheckTask.name]

    def test_registered(self, application):
        assert ShipMovementsCheckTask.name in application.tasks

    def test_screening_not_found(self, application, factory, task):
        screening_id = 1234567
        task_args = (screening_id, )

        result = task.apply(task_args)

        result_value = result.get()
        assert result_value is None

        screening = application.screenings_repository.get_or_none(
            id=screening_id)
        assert screening is None

        report = application.screenings_reports_repository.get_or_none(
            screening_id=screening_id)
        assert report is None

    @pytest.mark.usefixtures('mock_task_run')
    def test_timeout(
            self, mock_task_run, application, factory, task, ):
        mock_task_run.side_effect = timeout
        imo_id = 12345
        account_id = 123456
        ship = factory.create_ship(
            imo_id=imo_id, country_id='PL',
            type='Bulk Carrier', mmsi='355443000')
        screening = factory.create_screening(
            ship=ship, account_id=account_id,
            severity=Severity.UNKNOWN, status=Status.SCHEDULED,
        )

        task_args = (screening.id,)

        result = task.apply(task_args)

        with pytest.raises(timeout):
            result.get()

        screening = application.screenings_repository.get_or_none(
            id=screening.id)
        assert screening is not None
        assert screening.account_id == account_id
        assert screening.port_visits_status == Status.DONE
        assert screening.port_visits_severity == Severity.UNKNOWN

        report = application.screenings_reports_repository.get_or_none(
            screening_id=screening.id)
        assert report is None

    @responses.activate
    def test_no_ais_ihs_data(self, application, factory, task,
                             sis_client):
        imo_id = 12345
        account_id = 123456
        mmsi = '355443000'
        ship = factory.create_ship(
            imo_id=imo_id, country_id='PL',
            type='Bulk Carrier', mmsi='355443000', length=123.4,
            breadth=234.5, displacement=345.6, draught=456.7,
        )
        screening = factory.create_screening(
            ship=ship, account_id=account_id,
            severity=Severity.UNKNOWN, status=Status.SCHEDULED,
        )

        # IHS movement data
        response = {
            'objects': [],
        }
        responses.add(
            responses.GET,
            '{0}ship_movement/?imo_id={1}'.format(sis_client.base_uri, imo_id),
            status=200, body=json.dumps(response),
        )

        # AIS data
        response = {
            "next_link": "/api/v2/track/{0}?"
                         "end_date=2016-10-31T00:20:37Z".format(mmsi),
            'count': 0,
            'data': [],
        }

        responses.add(
            responses.GET,
            'https://commaisservice.polestarglobal-test.com/api/v2/track/'
            '{0}?position_count=10'.format(mmsi),
            status=200, body=json.dumps(response),
        )
        task_args = (screening.id,)

        result = task.apply(task_args)

        result_value = result.get()
        assert result_value is None

        screening = application.screenings_repository.get_or_none(
            id=screening.id)
        assert screening is not None
        assert screening.account_id == account_id
        assert screening.port_visits_status == Status.DONE
        assert screening.port_visits_severity == Severity.OK

        report = application.screenings_reports_repository.get_or_none(
            screening_id=screening.id)
        assert report is not None
        assert report.port_visits == {
            'ihs_movement_data': [],
            'port_visits': [],
        }

    @responses.activate
    @freeze_time("2018-09-11 07:59:00")
    def test_with_ais_ihs_data(self, application, factory, task,
                               sis_client):
        imo_id = 12345
        account_id = 123456
        mmsi = '636016500'
        ship = factory.create_ship(
            imo_id=imo_id, country_id='PL',
            type='Bulk Carrier', mmsi='636016500')
        screening = factory.create_screening(
            ship=ship, account_id=account_id,
            severity=Severity.UNKNOWN, status=Status.SCHEDULED,
        )
        port = {"port_code": "CIPBT",
                "port_country_name": "C\u00f4te d'Ivoire",
                "port_latitude": 5.233333110809326,
                "port_longitude": -3.9666666984558105,
                "port_name": "Abidjan SBM/MBM"}
        port2 = {"port_code": "JPNGO", "port_name": "Nagoya",
                 "port_country_name": "Japan",
                 "port_latitude": 35.03333282470703,
                 "port_longitude": 136.85000610351562}

        ShipMovementsCheck._get_ports = \
            mock.Mock(return_value=[port, port, port, port])
        IHSPositionLogic._get_port_data = \
            mock.Mock(return_value=port2)

        # IHS movement data
        response = {
            'objects': [{"arrival_date": "2018-02-14",
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
                         "timestamp": "2017-12-26T21:50:49"},
                        ],
        }
        responses.add(
            responses.GET,
            '{0}ship_movement/?imo_id={1}'.format(sis_client.base_uri, imo_id),
            status=200, body=json.dumps(response),
        )

        # AIS data
        response = {
            "next_link": "/api/v2/track/{0}?"
                         "end_date=2016-10-31T00:20:37Z".format(mmsi),
            'count': 2,
            'data':
                [
                    {
                        'timestamp': '2018-04-10T23:46:00Z', 'course': 209.0,
                        'latitude': 5.192033, 'longitude': -4.026866,
                        'source': 'T', 'channel': 'A', 'heading': 135.0,
                        'status': 'At anchor', 'extdata': {'msgtype': 3},
                        'mmsi': 636016500, 'speed': 0.0
                    },
                    {
                        'timestamp': '2018-04-10T22:34:02Z', 'course': 236.0,
                        'latitude': 5.192067, 'longitude': -4.026917,
                        'source': 'T', 'channel': 'A', 'heading': 136.0,
                        'status': 'At anchor', 'extdata': {'msgtype': 3},
                        'mmsi': 636016500, 'speed': 0.1
                    }]
        }

        responses.add(
            responses.GET,
            'https://commaisservice.polestarglobal-test.com/api/v2/track/'
            '{0}?position_count=10'.format(mmsi),
            status=200, body=json.dumps(response),
        )
        task_args = (screening.id,)

        result = task.apply(task_args)

        result_value = result.get()
        assert result_value is None

        screening = application.screenings_repository.get_or_none(
            id=screening.id)
        assert screening is not None
        assert screening.account_id == account_id
        assert screening.port_visits_status == Status.DONE
        assert screening.port_visits_severity == Severity.OK

        report = application.screenings_reports_repository.get_or_none(
            screening_id=screening.id)
        assert report is not None
        assert len(report.port_visits['ihs_movement_data']) == 2
        assert len(report.port_visits['port_visits']) == 1

    @responses.activate
    @freeze_time("2018-09-11 07:59:00")
    def test_with_ais_ihs_data_blacklisted_port_country(
            self, application, factory, task, sis_client):
        imo_id = 12345
        account_id = 123456
        mmsi = '636016500'
        ship = factory.create_ship(
            imo_id=imo_id, country_id='KP',
            type='Bulk Carrier', mmsi='636016500')
        screening = factory.create_screening(
            ship=ship, account_id=account_id,
            severity=Severity.UNKNOWN, status=Status.SCHEDULED,
        )
        port = {"port_code": "KPNAM",
                "port_country_name": "Korea, North",
                "port_latitude": 38.7163200378418,
                "port_longitude": 125.40026092529297,
                "port_name": "Nampo"}

        ShipMovementsCheck._get_ports = \
            mock.Mock(return_value=[port, port, port, port])
        IHSPositionLogic._get_port_data = \
            mock.Mock(return_value=port)

        # IHS movement data
        response = {
            'objects': [{"arrival_date": "2018-02-14",
                         "country_name": "Cote d'Ivoire",
                         "creation_date": "2018-02-18T08:47:17.425859",
                         "destination_port": "Nampo",
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
                         "timestamp": "2018-02-14T16:43:49"}
                        ],
        }
        responses.add(
            responses.GET,
            '{0}ship_movement/?imo_id={1}'.format(sis_client.base_uri, imo_id),
            status=200, body=json.dumps(response),
        )

        # AIS data
        response = {
            "next_link": "/api/v2/track/{0}?"
                         "end_date=2016-10-31T00:20:37Z".format(mmsi),
            'count': 2,
            'data':
                [
                    {
                        'timestamp': '2018-04-10T23:46:00Z', 'course': 209.0,
                        'latitude': 38.71632, 'longitude': 125.40026,
                        'source': 'T', 'channel': 'A', 'heading': 135.0,
                        'status': 'At anchor', 'extdata': {'msgtype': 3},
                        'mmsi': 636016500, 'speed': 0.0
                    },
                    {
                        'timestamp': '2018-04-10T22:34:02Z', 'course': 236.0,
                        'latitude': 5.192067, 'longitude': -4.026917,
                        'source': 'T', 'channel': 'A', 'heading': 136.0,
                        'status': 'At anchor', 'extdata': {'msgtype': 3},
                        'mmsi': 636016500, 'speed': 0.1
                    }]
        }

        responses.add(
            responses.GET,
            'https://commaisservice.polestarglobal-test.com/api/v2/track/'
            '{0}?position_count=10'.format(mmsi),
            status=200, body=json.dumps(response),
        )
        task_args = (screening.id,)

        result = task.apply(task_args)

        result_value = result.get()
        assert result_value is None

        screening = application.screenings_repository.get_or_none(
            id=screening.id)
        assert screening is not None
        assert screening.account_id == account_id
        assert screening.port_visits_status == Status.DONE
        assert screening.port_visits_severity == Severity.CRITICAL

        report = application.screenings_reports_repository.get_or_none(
            screening_id=screening.id)
        assert report is not None
        assert len(report.port_visits['ihs_movement_data']) == 1
        assert len(report.port_visits['port_visits']) == 1

    @responses.activate
    @freeze_time("2018-09-11 07:59:00")
    def test_with_ais_ihs_data_no_port(self, application, factory, task,
                                       sis_client):
        imo_id = 12345
        account_id = 123456
        mmsi = '636016500'
        ship = factory.create_ship(
            imo_id=imo_id, country_id='KP',
            type='Bulk Carrier', mmsi='636016500')
        screening = factory.create_screening(
            ship=ship, account_id=account_id,
            severity=Severity.UNKNOWN, status=Status.SCHEDULED,
        )
        port = {
            "port_code": "JPNGO", "port_name": "Nagoya",
            "port_country_name": "Japan",
            "port_latitude": 35.03333282470703,
            "port_longitude": 136.85000610351562
        }

        ShipMovementsCheck._get_ports = \
            mock.Mock(return_value=[port, port, port, port])
        IHSPositionLogic._get_port_data = \
            mock.Mock(return_value=port)

        canal = "In the Canal"
        # IHS movement data
        response = {
            'objects': [{"arrival_date": "2018-02-14",
                         "country_name": "",
                         "creation_date": "2018-02-18T08:47:17.425859",
                         "destination_port": "",
                         "estimated_time_of_arrival": "2018-02-18T06:00:00",
                         "hours_in_port": 73, "id": 43335772,
                         "ihs_creation_date": "2018-02-17T18:15:58.473000",
                         "ihs_id": "97736771", "ihs_port_geo_id": "5557",
                         "ihs_port_id": "18346", "imo_id": "9467873",
                         "last_port_of_call_arrival_date":
                             "2018-02-14T15:59:29",
                         "last_port_of_call_code": "",
                         "last_port_of_call_country": "",
                         "last_port_of_call_country_code": "",
                         "last_port_of_call_name": "",
                         "last_port_of_call_sail_date": "2018-02-14T16:43:49",
                         "latitude": None, "longitude": None,
                         "movement_type": canal,
                         "port_name": "",
                         "resource_uri": "/api/v1/ship_movement/43335772",
                         "sail_date": "2018-02-17",
                         "sail_date_full": "2018-02-17T17:59:25",
                         "ship_name": "BLUE CAT",
                         "ship_type": "Bulk Carrier",
                         "timestamp": "2018-02-14T16:43:49"}
                        ],
        }
        responses.add(
            responses.GET,
            '{0}ship_movement/?imo_id={1}'.format(sis_client.base_uri, imo_id),
            status=200, body=json.dumps(response),
        )

        # AIS data
        response = {
            "next_link": "/api/v2/track/{0}?"
                         "end_date=2016-10-31T00:20:37Z".format(mmsi),
            'count': 2,
            'data':
                [
                    {
                        'timestamp': '2018-04-10T23:46:00Z', 'course': 209.0,
                        'latitude': 38.71632, 'longitude': 125.40026,
                        'source': 'T', 'channel': 'A', 'heading': 135.0,
                        'status': 'At anchor', 'extdata': {'msgtype': 3},
                        'mmsi': 636016500, 'speed': 0.0
                    },
                    {
                        'timestamp': '2018-04-10T22:34:02Z', 'course': 236.0,
                        'latitude': 5.192067, 'longitude': -4.026917,
                        'source': 'T', 'channel': 'A', 'heading': 136.0,
                        'status': 'At anchor', 'extdata': {'msgtype': 3},
                        'mmsi': 636016500, 'speed': 0.1
                    }]
        }

        responses.add(
            responses.GET,
            'https://commaisservice.polestarglobal-test.com/api/v2/track/'
            '{0}?position_count=10'.format(mmsi),
            status=200, body=json.dumps(response),
        )
        task_args = (screening.id,)

        result = task.apply(task_args)

        result_value = result.get()
        assert result_value is None

        screening = application.screenings_repository.get_or_none(
            id=screening.id)
        assert screening is not None
        assert screening.account_id == account_id
        assert screening.port_visits_status == Status.DONE
        assert screening.port_visits_severity == Severity.OK

        report = application.screenings_reports_repository.get_or_none(
            screening_id=screening.id)
        assert report is not None
        assert len(report.port_visits['ihs_movement_data']) == 1
        assert len(report.port_visits['port_visits']) == 1
        assert report.port_visits['ihs_movement_data'][0]['port_name'] == canal

    @responses.activate
    @freeze_time("2020-04-11 07:59:00")
    def test_with_smh_service(self, application, factory, task):
        import os

        os.environ['USE_SMH_SERVICE'] = "1"

        imo_id = 12345
        account_id = 123456
        ship = factory.create_ship(
            imo_id=imo_id, country_id='KP',
            type='Bulk Carrier', mmsi='636016500')
        screening = factory.create_screening(
            ship=ship, account_id=account_id,
            severity=Severity.UNKNOWN, status=Status.SCHEDULED,
        )
        port = {
            "port_code": "JPNGO",
            "port_name": "Nagoya",
            "port_country_name": "Japan",
            "port_latitude": 35.0333328,
            "port_longitude": 136.850006
        }

        ShipMovementsCheck._get_ports = \
            mock.Mock(return_value=[port, port])
        IHSPositionLogic._get_port_data = \
            mock.Mock(return_value=port)

        # SMH data
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
                },
                {
                    "departed": "2018-01-06T11:56:12",
                    "entered": "2017-12-26T21:50:49",
                    "latitude": 35.029917,
                    "longitude": 136.850783,
                    "port": port,
                    "sail_date_full": "2018-01-06T11:56:12",
                    "speed": 0,
                    "type": "IHS"
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
            "ihs_movement_data": [
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
                 "timestamp": "2017-12-26T21:50:49"
                 }
            ]
        }

        responses.add(
            responses.GET,
            "http://smh.polestar-testing.local/api/v1/shipmovementhistory/"
            "12345?end_date=365&request_days=365&overwrite_cache=1"
            "&ais_rate=600&ais_last_midnight=1&speed_filter=99"
            "&response_type=7&use_cache=1&external_id=211",
            status=200, body=json.dumps(response),
        )

        task_args = (screening.id,)
        result = task.apply(task_args)
        result_value = result.get()
        assert result_value is None

        screening = application.screenings_repository.get_or_none(
            id=screening.id)
        assert screening is not None
        assert screening.account_id == account_id
        assert screening.port_visits_status == Status.DONE
        assert screening.port_visits_severity == Severity.OK

        report = application.screenings_reports_repository.get_or_none(
            screening_id=screening.id)
        assert report is not None
        assert len(report.port_visits['ihs_movement_data']) == 1
        assert len(report.port_visits['port_visits']) == 2
