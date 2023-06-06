import json
from unittest import mock
from urllib.parse import quote_plus

import pytest
from freezegun import freeze_time

from screening_api.lib.messaging.publishers import CeleryTaskPublisher
from screening_api.screenings.enums import Severity, SeverityChange, Status
from screening_api.screenings.subscribers import ScreeningsScreenSubscriber


class TestScreeningsViewOptions:

    uri = '/v1/screenings'

    def test_allowed_methods(self, test_client):
        env, resp = test_client.options(self.uri, as_tuple=True)

        assert resp.status_code == 200
        assert set(resp.allow) == set(['OPTIONS', 'GET', 'HEAD', 'DELETE'])
        assert resp.headers['Access-Control-Allow-Origin'] == '*'


@pytest.mark.usefixtures('authenticated')
class TestScreeningsViewGet:

    uri = '/v1/screenings'

    def test_unauthenticated(self, test_client):
        test_client.environ_base['HTTP_AUTHORIZATION'] = ''

        env, resp = test_client.get(self.uri, as_tuple=True)

        assert resp.status_code == 401

    @freeze_time("2001-09-11 07:59:00")
    def test_get(self, test_client, factory):
        account_id = 54321
        imo_id = 12345678
        ship_1 = factory.create_ship(imo_id=imo_id, country_id='PL')
        screening_1 = factory.create_screening(
            account_id=account_id, ship=ship_1, severity=Severity.UNKNOWN,
            previous_severity=Severity.UNKNOWN,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        screening_2 = factory.create_screening(
            account_id=account_id, ship=ship_1, severity=Severity.OK,
            previous_severity=Severity.OK,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        screening_3 = factory.create_screening(
            account_id=account_id, ship=ship_1, severity=Severity.WARNING,
            previous_severity=Severity.WARNING,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        screening_4 = factory.create_screening(
            account_id=account_id, ship=ship_1, severity=Severity.CRITICAL,
            previous_severity=Severity.CRITICAL,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        params = {'sort': '-id'}

        env, resp = test_client.get(
            self.uri, query_string=params, as_tuple=True)

        assert resp.status_code == 200
        expected_data = [
            {
                'id': screening.id,
                'created': '2001-09-11T07:59:00Z',
                'updated': '2001-09-11T07:59:00Z',
                'account_id': account_id,
                'ship': {
                    'imo_id': imo_id,
                    'name': ship_1.name,
                    'type': ship_1.type,
                    'country_id': ship_1.country_id,
                    'country_name': ship_1.country_name,
                },
                'ship_id': screening.ship_id,
                'status': screening.status.name,
                'severity': screening.severity.name,
                "severity_change": screening.severity_change.name,
                "previous_severity": screening.previous_severity.name,
                "previous_severity_date": '2001-09-11T07:59:00Z',
            }
            for screening in [
                screening_4, screening_3, screening_2, screening_1,
            ]
        ]
        assert resp.json == {
            "data": expected_data,
            "meta": {
                "count": len(expected_data),
            },
            "links": {
                'first': (
                    'http://api/v1/screenings?sort=-id&page=1'
                ),
                'last': (
                    'http://api/v1/screenings?sort=-id&page=1'
                ),
            },
        }

    @freeze_time("2001-09-11 07:59:00")
    def test_get_no_previous_result(self, test_client, factory):
        account_id = 54321
        imo_id = 12345678
        ship_1 = factory.create_ship(imo_id=imo_id, country_id='PL')
        screening_1 = factory.create_screening(
            account_id=account_id, ship=ship_1, severity=Severity.UNKNOWN,
            previous_severity=None, previous_severity_date=None,
        )
        screening_2 = factory.create_screening(
            account_id=account_id, ship=ship_1, severity=Severity.OK,
            previous_severity=None, previous_severity_date=None,
        )
        screening_3 = factory.create_screening(
            account_id=account_id, ship=ship_1, severity=Severity.WARNING,
            previous_severity=None, previous_severity_date=None,
        )
        screening_4 = factory.create_screening(
            account_id=account_id, ship=ship_1, severity=Severity.CRITICAL,
            previous_severity=None, previous_severity_date=None,
        )
        params = {'sort': '-id'}

        env, resp = test_client.get(
            self.uri, query_string=params, as_tuple=True)

        assert resp.status_code == 200
        expected_data = [
            {
                'id': screening.id,
                'created': '2001-09-11T07:59:00Z',
                'updated': '2001-09-11T07:59:00Z',
                'account_id': account_id,
                'ship': {
                    'imo_id': imo_id,
                    'name': ship_1.name,
                    'type': ship_1.type,
                    'country_id': ship_1.country_id,
                    'country_name': ship_1.country_name,
                },
                'ship_id': screening.ship_id,
                'status': screening.status.name,
                'severity': screening.severity.name,
                "severity_change": screening.severity_change.name,
                "previous_severity": screening.previous_severity,
                "previous_severity_date": screening.previous_severity_date,
            }
            for screening in [
                screening_4, screening_3, screening_2, screening_1,
            ]
        ]
        assert resp.json == {
            "data": expected_data,
            "meta": {
                "count": len(expected_data),
            },
            "links": {
                'first': (
                    'http://api/v1/screenings?sort=-id&page=1'
                ),
                'last': (
                    'http://api/v1/screenings?sort=-id&page=1'
                ),
            },
        }

    @freeze_time("2001-09-11 07:59:00.123456")
    def test_get_csv(self, test_client, factory):
        account_id = 54321
        imo_id_1 = 12345678
        imo_id_2 = 12345679
        ship_1 = factory.create_ship(imo_id=imo_id_1, country_id='PL')
        ship_2 = factory.create_ship(imo_id=imo_id_2, country_id='UK')
        screening_1 = factory.create_screening(
            account_id=account_id, ship=ship_1, severity=Severity.UNKNOWN,
            previous_severity=Severity.UNKNOWN,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        screening_2 = factory.create_screening(
            account_id=account_id, ship=ship_2, severity=Severity.OK,
            previous_severity=Severity.OK,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        params = {'sort': '-id', 'format': 'csv'}

        env, resp = test_client.get(
            self.uri, query_string=params, as_tuple=True)

        assert resp.status_code == 200
        assert resp.json is None
        csv_header = ','.join([
            'Flag', 'Ship Name',
            'IMO', 'Ship Type',
            'Current Result', 'Previous severity',
            'Previous severity date (UTC)', 'Last Updated (UTC)\r\n',
        ])
        csv_rows = [
            ','.join([
                screening.ship.country_name, screening.ship.name,
                screening.ship.imo, screening.ship.type,
                screening.result, screening.previous_severity.name,
                "2001-09-11T07:59:00",
                "2001-09-11T07:59:00\r\n",
            ])
            for screening in (screening_2, screening_1)
        ]
        expected_data = ''.join([csv_header, ] + csv_rows)
        assert resp.data == expected_data.encode()

    @freeze_time("2001-09-11 07:59:00.123456")
    def test_get_csv_no_previous_severity(self, test_client, factory):
        account_id = 54321
        imo_id_1 = 12345678
        imo_id_2 = 12345679
        ship_1 = factory.create_ship(imo_id=imo_id_1, country_id='PL')
        ship_2 = factory.create_ship(imo_id=imo_id_2, country_id='UK')
        screening_1 = factory.create_screening(
            account_id=account_id, ship=ship_1, severity=Severity.UNKNOWN,
            previous_severity=None,
            previous_severity_date=None,
        )
        screening_2 = factory.create_screening(
            account_id=account_id, ship=ship_2, severity=Severity.OK,
            previous_severity=None,
            previous_severity_date=None,
        )
        params = {'sort': '-id', 'format': 'csv'}

        env, resp = test_client.get(
            self.uri, query_string=params, as_tuple=True)

        assert resp.status_code == 200
        assert resp.json is None
        csv_header = ','.join([
            'Flag', 'Ship Name',
            'IMO', 'Ship Type',
            'Current Result', 'Previous severity',
            'Previous severity date (UTC)', 'Last Updated (UTC)\r\n',
        ])
        csv_rows = [
            ','.join([
                screening.ship.country_name, screening.ship.name,
                screening.ship.imo, screening.ship.type,
                screening.result, "", "", "2001-09-11T07:59:00\r\n",
            ])
            for screening in (screening_2, screening_1)
        ]
        expected_data = ''.join([csv_header, ] + csv_rows)
        assert resp.data == expected_data.encode()

    @freeze_time("2001-09-11 07:59:00")
    def test_returns_created_before_request(self, test_client, factory):
        account_id = 54321
        imo_id = 12345678
        ship_1 = factory.create_ship(imo_id=imo_id, country_id='PL')
        screening_1 = factory.create_screening(
            account_id=account_id, ship=ship_1, severity=Severity.UNKNOWN,
            previous_severity=Severity.UNKNOWN,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        screening_2 = factory.create_screening(
            account_id=account_id, ship=ship_1, severity=Severity.OK,
            previous_severity=Severity.OK,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        screening_3 = factory.create_screening(
            account_id=account_id, ship=ship_1, severity=Severity.WARNING,
            previous_severity=Severity.WARNING,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        screening_4 = factory.create_screening(
            account_id=account_id, ship=ship_1, severity=Severity.CRITICAL,
            previous_severity=Severity.CRITICAL,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        factory.create_screening(
            account_id=account_id, ship=ship_1, severity=Severity.CRITICAL,
            previous_severity=Severity.CRITICAL,
            created="2002-01-01 01:00:00",
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        params = {'sort': '-id'}

        env, resp = test_client.get(
            self.uri, query_string=params, as_tuple=True)

        assert resp.status_code == 200
        expected_data = [
            {
                'id': screening.id,
                'created': '2001-09-11T07:59:00Z',
                'updated': '2001-09-11T07:59:00Z',
                'account_id': account_id,
                'ship': {
                    'imo_id': imo_id,
                    'name': ship_1.name,
                    'type': ship_1.type,
                    'country_id': ship_1.country_id,
                    'country_name': ship_1.country_name,
                },
                'ship_id': screening.ship_id,
                'status': screening.status.name,
                'severity': screening.severity.name,
                "severity_change": screening.severity_change.name,
                "previous_severity": screening.previous_severity.name,
                'previous_severity_date': '2001-09-11T07:59:00Z',
            }
            for screening in [
                screening_4, screening_3, screening_2, screening_1,
            ]
        ]
        assert resp.json == {
            "data": expected_data,
            "meta": {
                "count": len(expected_data),
            },
            "links": {
                'first': (
                    'http://api/v1/screenings?sort=-id&page=1'
                ),
                'last': (
                    'http://api/v1/screenings?sort=-id&page=1'
                ),
            },
        }

    @freeze_time("2001-09-11 07:59:00")
    def test_get_ship_no_flag(self, test_client, factory):
        account_id = 54321
        imo_id = 12345678
        ship_1 = factory.create_ship(
            imo_id=imo_id, country_id=None, country_name=None)
        screening_1 = factory.create_screening(
            account_id=account_id, ship=ship_1, severity=Severity.UNKNOWN,
            previous_severity=Severity.UNKNOWN,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        screening_2 = factory.create_screening(
            account_id=account_id, ship=ship_1, severity=Severity.OK,
            previous_severity=Severity.OK,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        screening_3 = factory.create_screening(
            account_id=account_id, ship=ship_1, severity=Severity.WARNING,
            previous_severity=Severity.WARNING,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        screening_4 = factory.create_screening(
            account_id=account_id, ship=ship_1, severity=Severity.CRITICAL,
            previous_severity=Severity.CRITICAL,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        params = {'sort': '-id'}

        env, resp = test_client.get(
            self.uri, query_string=params, as_tuple=True)

        assert resp.status_code == 200
        expected_data = [
            {
                'id': screening.id,
                'created': '2001-09-11T07:59:00Z',
                'updated': '2001-09-11T07:59:00Z',
                'account_id': account_id,
                'ship': {
                    'imo_id': imo_id,
                    'name': ship_1.name,
                    'type': ship_1.type,
                    'country_id': None,
                    'country_name': None,
                },
                'ship_id': screening.ship_id,
                'status': screening.status.name,
                'severity': screening.severity.name,
                "severity_change": screening.severity_change.name,
                "previous_severity": screening.previous_severity.name,
                'previous_severity_date': '2001-09-11T07:59:00Z',
            }
            for screening in [
                screening_4, screening_3, screening_2, screening_1,
            ]
        ]
        assert resp.json == {
            "data": expected_data,
            "meta": {
                "count": len(expected_data),
            },
            "links": {
                'first': (
                    'http://api/v1/screenings?sort=-id&page=1'
                ),
                'last': (
                    'http://api/v1/screenings?sort=-id&page=1'
                ),
            },
        }

    @freeze_time("2001-09-11 07:59:00")
    def test_get_self_screenings(self, test_client, factory):
        account_id = 54321
        account_id_2 = 543210
        imo_id = 12345678
        ship_1 = factory.create_ship(imo_id=imo_id, country_id='PL')
        factory.create_screening(
            account_id=account_id_2, ship=ship_1, severity=Severity.UNKNOWN,
            previous_severity=Severity.UNKNOWN,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        screening_2 = factory.create_screening(
            account_id=account_id, ship=ship_1, severity=Severity.OK,
            previous_severity=Severity.OK,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        screening_3 = factory.create_screening(
            account_id=account_id, ship=ship_1, severity=Severity.WARNING,
            previous_severity=Severity.WARNING,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        factory.create_screening(
            account_id=account_id_2, ship=ship_1, severity=Severity.CRITICAL,
            previous_severity=Severity.CRITICAL,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        params = {'sort': '-id'}

        env, resp = test_client.get(
            self.uri, query_string=params, as_tuple=True)

        assert resp.status_code == 200
        expected_data = [
            {
                'id': screening.id,
                'created': '2001-09-11T07:59:00Z',
                'updated': '2001-09-11T07:59:00Z',
                'account_id': account_id,
                'ship': {
                    'imo_id': imo_id,
                    'name': ship_1.name,
                    'type': ship_1.type,
                    'country_id': ship_1.country_id,
                    'country_name': ship_1.country_name,
                },
                'ship_id': screening.ship_id,
                'status': screening.status.name,
                'severity': screening.severity.name,
                "severity_change": screening.severity_change.name,
                "previous_severity": screening.previous_severity.name,
                'previous_severity_date': '2001-09-11T07:59:00Z',
            }
            for screening in [screening_3, screening_2]
        ]
        assert resp.json == {
            "data": expected_data,
            "meta": {
                "count": len(expected_data),
            },
            "links": {
                'first': (
                    'http://api/v1/screenings?sort=-id&page=1'
                ),
                'last': (
                    'http://api/v1/screenings?sort=-id&page=1'
                ),
            },
        }

    @pytest.mark.parametrize('reverse', [False, True])
    @freeze_time("2001-09-11 07:59:00")
    def test_get_sort_by_ship_imo_id(
            self, test_client, factory, reverse):
        account_id = 54321
        imo_id_1 = 12345678
        imo_id_2 = 12345679
        imo_id_3 = 12345680
        ship_1 = factory.create_ship(imo_id=imo_id_1, country_id='PL')
        ship_2 = factory.create_ship(imo_id=imo_id_2, country_id='UK')
        ship_3 = factory.create_ship(imo_id=imo_id_3, country_id='US')
        screening_1 = factory.create_screening(
            account_id=account_id, ship=ship_1, severity=Severity.UNKNOWN,
            previous_severity=Severity.UNKNOWN,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        screening_2 = factory.create_screening(
            account_id=account_id, ship=ship_2, severity=Severity.OK,
            previous_severity=Severity.OK,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        screening_3 = factory.create_screening(
            account_id=account_id, ship=ship_3, severity=Severity.WARNING,
            previous_severity=Severity.WARNING,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        sort = 'ship__imo_id' if reverse else '-ship__imo_id'
        params = {'sort': sort}

        env, resp = test_client.get(
            self.uri, query_string=params, as_tuple=True)

        assert resp.status_code == 200
        expected_order = [screening_3, screening_2, screening_1]
        if reverse:
            expected_order = reversed(expected_order)
        expected_data = [
            {
                'id': screening.id,
                'created': '2001-09-11T07:59:00Z',
                'updated': '2001-09-11T07:59:00Z',
                'account_id': account_id,
                'ship': {
                    'imo_id': screening.ship.imo_id,
                    'name': screening.ship.name,
                    'type': screening.ship.type,
                    'country_id': screening.ship.country_id,
                    'country_name': screening.ship.country_name,
                },
                'ship_id': screening.ship_id,
                'status': screening.status.name,
                'severity': screening.severity.name,
                "severity_change": screening.severity_change.name,
                "previous_severity": screening.previous_severity.name,
                'previous_severity_date': '2001-09-11T07:59:00Z',
            }
            for screening in expected_order
        ]
        assert resp.json == {
            "data": expected_data,
            "meta": {
                "count": len(expected_data),
            },
            "links": {
                "first": (
                    'http://api/v1/screenings?'
                    'sort={0}&page=1'.format(sort)
                ),
                'last': (
                    'http://api/v1/screenings?'
                    'sort={0}&page=1'.format(sort)
                ),
            },
        }

    @pytest.mark.parametrize('reverse', [False, True])
    @freeze_time("2001-09-11 07:59:00")
    def test_get_sort_by_ship_country_id(self, test_client, factory, reverse):
        account_id = 54321
        imo_id_1 = 12345678
        imo_id_2 = 12345679
        imo_id_3 = 12345680
        ship_1 = factory.create_ship(imo_id=imo_id_1, country_id='PL')
        ship_2 = factory.create_ship(imo_id=imo_id_2, country_id='UK')
        ship_3 = factory.create_ship(imo_id=imo_id_3, country_id='US')
        screening_1 = factory.create_screening(
            account_id=account_id, ship=ship_1, severity=Severity.UNKNOWN,
            previous_severity=Severity.UNKNOWN,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        screening_2 = factory.create_screening(
            account_id=account_id, ship=ship_2, severity=Severity.OK,
            previous_severity=Severity.OK,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        screening_3 = factory.create_screening(
            account_id=account_id, ship=ship_3, severity=Severity.WARNING,
            previous_severity=Severity.WARNING,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        sort = 'ship__country_id' if reverse else '-ship__country_id'
        params = {'sort': sort}

        env, resp = test_client.get(
            self.uri, query_string=params, as_tuple=True)

        assert resp.status_code == 200
        expected_order = [screening_3, screening_2, screening_1]
        if reverse:
            expected_order = reversed(expected_order)
        expected_data = [
            {
                'id': screening.id,
                'created': '2001-09-11T07:59:00Z',
                'updated': '2001-09-11T07:59:00Z',
                'account_id': account_id,
                'ship': {
                    'imo_id': screening.ship.imo_id,
                    'name': screening.ship.name,
                    'type': screening.ship.type,
                    'country_id': screening.ship.country_id,
                    'country_name': screening.ship.country_name,
                },
                'ship_id': screening.ship_id,
                'status': screening.status.name,
                'severity': screening.severity.name,
                "severity_change": screening.severity_change.name,
                "previous_severity": screening.previous_severity.name,
                'previous_severity_date': '2001-09-11T07:59:00Z',
            }
            for screening in expected_order
        ]
        assert resp.json == {
            "data": expected_data,
            "meta": {
                "count": len(expected_data),
            },
            "links": {
                "first": (
                    'http://api/v1/screenings?'
                    'sort={0}&page=1'.format(sort)
                ),
                'last': (
                    'http://api/v1/screenings?'
                    'sort={0}&page=1'.format(sort)
                ),
            },
        }

    @pytest.mark.parametrize('reverse', [False, True])
    @freeze_time("2001-09-11 07:59:00")
    def test_get_sort_by_ship_name(self, test_client, factory, reverse):
        account_id = 54321
        imo_id_1 = 12345678
        imo_id_2 = 12345679
        imo_id_3 = 12345680
        ship_1 = factory.create_ship(imo_id=imo_id_1, name='Beskidy')
        ship_2 = factory.create_ship(imo_id=imo_id_2, name='Karpaty')
        ship_3 = factory.create_ship(imo_id=imo_id_3, name='Sudety')
        screening_1 = factory.create_screening(
            account_id=account_id, ship=ship_1, severity=Severity.UNKNOWN,
            previous_severity=Severity.UNKNOWN,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        screening_2 = factory.create_screening(
            account_id=account_id, ship=ship_2, severity=Severity.OK,
            previous_severity=Severity.OK,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        screening_3 = factory.create_screening(
            account_id=account_id, ship=ship_3, severity=Severity.WARNING,
            previous_severity=Severity.WARNING,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        sort = 'ship__name' if reverse else '-ship__name'
        params = {'sort': sort}

        env, resp = test_client.get(
            self.uri, query_string=params, as_tuple=True)

        assert resp.status_code == 200
        expected_order = [screening_3, screening_2, screening_1]
        if reverse:
            expected_order = reversed(expected_order)
        expected_data = [
            {
                'id': screening.id,
                'created': '2001-09-11T07:59:00Z',
                'updated': '2001-09-11T07:59:00Z',
                'account_id': account_id,
                'ship': {
                    'imo_id': screening.ship.imo_id,
                    'name': screening.ship.name,
                    'type': screening.ship.type,
                    'country_id': screening.ship.country_id,
                    'country_name': screening.ship.country_name,
                },
                'ship_id': screening.ship_id,
                'status': screening.status.name,
                'severity': screening.severity.name,
                "severity_change": screening.severity_change.name,
                "previous_severity": screening.previous_severity.name,
                'previous_severity_date': '2001-09-11T07:59:00Z',
            }
            for screening in expected_order
        ]
        assert resp.json == {
            "data": expected_data,
            "meta": {
                "count": len(expected_data),
            },
            "links": {
                "first": (
                    'http://api/v1/screenings?'
                    'sort={0}&page=1'.format(sort)
                ),
                'last': (
                    'http://api/v1/screenings?'
                    'sort={0}&page=1'.format(sort)
                ),
            },
        }

    @pytest.mark.parametrize('reverse', [False, True])
    @freeze_time("2001-09-11 07:59:00")
    def test_get_sort_by_ship_type(self, test_client, factory, reverse):
        account_id = 54321
        imo_id_1 = 12345678
        imo_id_2 = 12345679
        imo_id_3 = 12345680
        ship_1 = factory.create_ship(imo_id=imo_id_1, type='Bulk Carrier')
        ship_2 = factory.create_ship(imo_id=imo_id_2, type='Container')
        ship_3 = factory.create_ship(imo_id=imo_id_3, type='Crude Oil Tanker')
        screening_1 = factory.create_screening(
            account_id=account_id, ship=ship_1, severity=Severity.UNKNOWN,
            previous_severity=Severity.UNKNOWN,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        screening_2 = factory.create_screening(
            account_id=account_id, ship=ship_2, severity=Severity.OK,
            previous_severity=Severity.OK,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        screening_3 = factory.create_screening(
            account_id=account_id, ship=ship_3, severity=Severity.WARNING,
            previous_severity=Severity.WARNING,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        sort = 'ship__type' if reverse else '-ship__type'
        params = {'sort': sort}

        env, resp = test_client.get(
            self.uri, query_string=params, as_tuple=True)

        assert resp.status_code == 200
        expected_order = [screening_3, screening_2, screening_1]
        if reverse:
            expected_order = reversed(expected_order)
        expected_data = [
            {
                'id': screening.id,
                'created': '2001-09-11T07:59:00Z',
                'updated': '2001-09-11T07:59:00Z',
                'account_id': account_id,
                'ship': {
                    'imo_id': screening.ship.imo_id,
                    'name': screening.ship.name,
                    'type': screening.ship.type,
                    'country_id': screening.ship.country_id,
                    'country_name': screening.ship.country_name,
                },
                'ship_id': screening.ship_id,
                'status': screening.status.name,
                'severity': screening.severity.name,
                "severity_change": screening.severity_change.name,
                "previous_severity": screening.previous_severity.name,
                'previous_severity_date': '2001-09-11T07:59:00Z',
            }
            for screening in expected_order
        ]
        assert resp.json == {
            "data": expected_data,
            "meta": {
                "count": len(expected_data),
            },
            "links": {
                "first": (
                    'http://api/v1/screenings?'
                    'sort={0}&page=1'.format(sort)
                ),
                'last': (
                    'http://api/v1/screenings?'
                    'sort={0}&page=1'.format(sort)
                ),
            },
        }

    @pytest.mark.parametrize('reverse', [False, True])
    @freeze_time("2001-09-11 07:59:00")
    def test_get_sort_by_updated(self, test_client, factory, reverse):
        account_id = 54321
        imo_id_1 = 12345678
        imo_id_2 = 12345679
        imo_id_3 = 12345680
        ship_1 = factory.create_ship(imo_id=imo_id_1)
        ship_2 = factory.create_ship(imo_id=imo_id_2)
        ship_3 = factory.create_ship(imo_id=imo_id_3)
        screening_1 = factory.create_screening(
            account_id=account_id, ship=ship_1, severity=Severity.UNKNOWN,
            previous_severity=Severity.UNKNOWN,
            updated="2001-09-11 07:59:00",
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        screening_2 = factory.create_screening(
            account_id=account_id, ship=ship_2, severity=Severity.OK,
            previous_severity=Severity.OK,
            updated="2002-09-11 07:59:00",
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        screening_3 = factory.create_screening(
            account_id=account_id, ship=ship_3, severity=Severity.WARNING,
            previous_severity=Severity.WARNING,
            updated="2003-09-11 07:59:00",
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        sort = 'updated' if reverse else '-updated'
        params = {'sort': sort}

        env, resp = test_client.get(
            self.uri, query_string=params, as_tuple=True)

        assert resp.status_code == 200
        expected_order = [screening_3, screening_2, screening_1]
        if reverse:
            expected_order = reversed(expected_order)
        expected_data = [
            {
                'id': screening.id,
                'created': '2001-09-11T07:59:00Z',
                'updated': screening.updated.isoformat() + 'Z',
                'account_id': account_id,
                'ship': {
                    'imo_id': screening.ship.imo_id,
                    'name': screening.ship.name,
                    'type': screening.ship.type,
                    'country_id': screening.ship.country_id,
                    'country_name': screening.ship.country_name,
                },
                'ship_id': screening.ship_id,
                'status': screening.status.name,
                'severity': screening.severity.name,
                "severity_change": screening.severity_change.name,
                "previous_severity": screening.previous_severity.name,
                'previous_severity_date': '2001-09-11T07:59:00Z',
            }
            for screening in expected_order
        ]
        assert resp.json == {
            "data": expected_data,
            "meta": {
                "count": len(expected_data),
            },
            "links": {
                "first": (
                    'http://api/v1/screenings?'
                    'sort={0}&page=1'.format(sort)
                ),
                'last': (
                    'http://api/v1/screenings?'
                    'sort={0}&page=1'.format(sort)
                ),
            },
        }

    @pytest.mark.parametrize('reverse', [False, True])
    @freeze_time("2001-09-11 07:59:00")
    def test_get_sort_by_severity(self, test_client, factory, reverse):
        account_id = 54321
        imo_id_1 = 12345678
        imo_id_2 = 12345679
        imo_id_3 = 12345680
        ship_1 = factory.create_ship(imo_id=imo_id_1)
        ship_2 = factory.create_ship(imo_id=imo_id_2)
        ship_3 = factory.create_ship(imo_id=imo_id_3)
        screening_1 = factory.create_screening(
            account_id=account_id, ship=ship_1, severity=Severity.OK,
            previous_severity=Severity.OK,
            updated="2001-09-11 07:59:00",
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        screening_2 = factory.create_screening(
            account_id=account_id, ship=ship_2, severity=Severity.CRITICAL,
            previous_severity=Severity.CRITICAL,
            updated="2002-09-11 07:59:00",
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        screening_3 = factory.create_screening(
            account_id=account_id, ship=ship_3, severity=Severity.WARNING,
            previous_severity=Severity.WARNING,
            updated="2003-09-11 07:59:00",
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        screening_4 = factory.create_screening(
            account_id=account_id, ship=ship_3, severity=Severity.UNKNOWN,
            previous_severity=Severity.UNKNOWN,
            updated="2003-09-11 07:59:00",
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        sort = 'severity' if reverse else '-severity'
        params = {'sort': sort}

        env, resp = test_client.get(
            self.uri, query_string=params, as_tuple=True)

        assert resp.status_code == 200
        expected_order = [screening_2, screening_3, screening_1, screening_4]
        if reverse:
            expected_order = reversed(expected_order)
        expected_data = [
            {
                'id': screening.id,
                'created': '2001-09-11T07:59:00Z',
                'updated': screening.updated.isoformat() + 'Z',
                'account_id': account_id,
                'ship': {
                    'imo_id': screening.ship.imo_id,
                    'name': screening.ship.name,
                    'type': screening.ship.type,
                    'country_id': screening.ship.country_id,
                    'country_name': screening.ship.country_name,
                },
                'ship_id': screening.ship_id,
                'status': screening.status.name,
                'severity': screening.severity.name,
                "severity_change": screening.severity_change.name,
                "previous_severity": screening.previous_severity.name,
                'previous_severity_date': '2001-09-11T07:59:00Z',
            }
            for screening in expected_order
        ]
        assert resp.json == {
            "data": expected_data,
            "meta": {
                "count": len(expected_data),
            },
            "links": {
                "first": (
                    'http://api/v1/screenings?'
                    'sort={0}&page=1'.format(sort)
                ),
                'last': (
                    'http://api/v1/screenings?'
                    'sort={0}&page=1'.format(sort)
                ),
            },
        }

    @pytest.mark.parametrize('reverse', [False, True])
    @freeze_time("2001-09-11 07:59:00")
    def test_get_sort_by_severity_change(self, test_client, factory, reverse):
        account_id = 54321
        imo_id_1 = 12345678
        imo_id_2 = 12345679
        imo_id_3 = 12345680
        ship_1 = factory.create_ship(imo_id=imo_id_1)
        ship_2 = factory.create_ship(imo_id=imo_id_2)
        ship_3 = factory.create_ship(imo_id=imo_id_3)
        screening_1 = factory.create_screening(
            account_id=account_id, ship=ship_1,
            severity_change=SeverityChange.DECREASED,
            updated="2001-09-11 07:59:00",
            previous_severity=Severity.UNKNOWN,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        screening_2 = factory.create_screening(
            account_id=account_id, ship=ship_2,
            severity_change=SeverityChange.INCREASED,
            updated="2002-09-11 07:59:00",
            previous_severity=Severity.UNKNOWN,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        screening_3 = factory.create_screening(
            account_id=account_id, ship=ship_3,
            severity_change=SeverityChange.NOCHANGE,
            updated="2003-09-11 07:59:00",
            previous_severity=Severity.UNKNOWN,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        sort = 'severity_change' if reverse else '-severity_change'
        params = {'sort': sort}

        env, resp = test_client.get(
            self.uri, query_string=params, as_tuple=True)

        assert resp.status_code == 200
        expected_order = [screening_2, screening_3, screening_1]
        if reverse:
            expected_order = reversed(expected_order)
        expected_data = [
            {
                'id': screening.id,
                'created': '2001-09-11T07:59:00Z',
                'updated': screening.updated.isoformat() + 'Z',
                'account_id': account_id,
                'ship': {
                    'imo_id': screening.ship.imo_id,
                    'name': screening.ship.name,
                    'type': screening.ship.type,
                    'country_id': screening.ship.country_id,
                    'country_name': screening.ship.country_name,
                },
                'ship_id': screening.ship_id,
                'status': screening.status.name,
                'severity': screening.severity.name,
                "severity_change": screening.severity_change.name,
                "previous_severity": screening.previous_severity.name,
                'previous_severity_date': '2001-09-11T07:59:00Z',
            }
            for screening in expected_order
        ]
        assert resp.json == {
            "data": expected_data,
            "meta": {
                "count": len(expected_data),
            },
            "links": {
                "first": (
                    'http://api/v1/screenings?'
                    'sort={0}&page=1'.format(sort)
                ),
                'last': (
                    'http://api/v1/screenings?'
                    'sort={0}&page=1'.format(sort)
                ),
            },
        }

    @pytest.mark.parametrize('reverse', [False, True])
    @freeze_time("2001-09-11 07:59:00")
    def test_get_sort_by_severity_and_severity_change(
            self, test_client, factory, reverse):
        account_id = 54321
        imo_id_1 = 12345678
        imo_id_2 = 12345679
        imo_id_3 = 12345680
        ship_1 = factory.create_ship(imo_id=imo_id_1)
        ship_2 = factory.create_ship(imo_id=imo_id_2)
        ship_3 = factory.create_ship(imo_id=imo_id_3)
        screening_1 = factory.create_screening(
            account_id=account_id, ship=ship_1, severity=Severity.WARNING,
            severity_change=SeverityChange.NOCHANGE,
            updated="2001-09-11 07:59:00",
            previous_severity=None,
            previous_severity_date=None,
        )
        screening_2 = factory.create_screening(
            account_id=account_id, ship=ship_1, severity=Severity.OK,
            severity_change=SeverityChange.DECREASED,
            updated="2001-09-11 07:59:00",
            previous_severity=None,
            previous_severity_date=None,
        )
        screening_3 = factory.create_screening(
            account_id=account_id, ship=ship_2, severity=Severity.CRITICAL,
            severity_change=SeverityChange.INCREASED,
            updated="2002-09-11 07:59:00",
            previous_severity=None,
            previous_severity_date=None,
        )
        screening_4 = factory.create_screening(
            account_id=account_id, ship=ship_1, severity=Severity.WARNING,
            severity_change=SeverityChange.INCREASED,
            updated="2001-09-11 07:59:00",
            previous_severity=None,
            previous_severity_date=None,
        )
        screening_5 = factory.create_screening(
            account_id=account_id, ship=ship_1, severity=Severity.OK,
            severity_change=SeverityChange.NOCHANGE,
            updated="2001-09-11 07:59:00",
            previous_severity=None,
            previous_severity_date=None,
        )
        screening_6 = factory.create_screening(
            account_id=account_id, ship=ship_3, severity=Severity.UNKNOWN,
            severity_change=SeverityChange.NOCHANGE,
            updated="2003-09-11 07:59:00",
            previous_severity=None,
            previous_severity_date=None,
        )
        screening_7 = factory.create_screening(
            account_id=account_id, ship=ship_1, severity=Severity.WARNING,
            severity_change=SeverityChange.DECREASED,
            updated="2001-09-11 07:59:00",
            previous_severity=None,
            previous_severity_date=None,
        )
        screening_8 = factory.create_screening(
            account_id=account_id, ship=ship_2, severity=Severity.CRITICAL,
            severity_change=SeverityChange.NOCHANGE,
            updated="2002-09-11 07:59:00",
            previous_severity=None,
            previous_severity_date=None,
        )
        sort = 'severity,severity_change' if reverse \
            else '-severity,-severity_change'
        params = {'sort': sort}

        env, resp = test_client.get(
            self.uri, query_string=params, as_tuple=True)

        assert resp.status_code == 200
        expected_order = [
            screening_3, screening_8, screening_4, screening_1, screening_7,
            screening_5, screening_2, screening_6,
        ]
        if reverse:
            expected_order = reversed(expected_order)
        expected_data = [
            {
                'id': screening.id,
                'created': '2001-09-11T07:59:00Z',
                'updated': screening.updated.isoformat() + 'Z',
                'account_id': account_id,
                'ship': {
                    'imo_id': screening.ship.imo_id,
                    'name': screening.ship.name,
                    'type': screening.ship.type,
                    'country_id': screening.ship.country_id,
                    'country_name': screening.ship.country_name,
                },
                'ship_id': screening.ship_id,
                'status': screening.status.name,
                'severity': screening.severity.name,
                "severity_change": screening.severity_change.name,
                "previous_severity": screening.previous_severity,
                'previous_severity_date': screening.previous_severity_date,
            }
            for screening in expected_order
        ]
        sort_enc = quote_plus(sort)
        assert resp.json == {
            "data": expected_data,
            "meta": {
                "count": len(expected_data),
            },
            "links": {
                "first": (
                    'http://api/v1/screenings?'
                    'sort={0}&page=1'.format(sort_enc)
                ),
                'last': (
                    'http://api/v1/screenings?'
                    'sort={0}&page=1'.format(sort_enc)
                ),
            },
        }

    @pytest.mark.parametrize('reverse', [False, True])
    @freeze_time("2001-09-11 07:59:00")
    def test_get_sort_by_status(self, test_client, factory, reverse):
        account_id = 54321
        imo_id_1 = 12345678
        imo_id_2 = 12345679
        imo_id_3 = 12345680
        ship_1 = factory.create_ship(imo_id=imo_id_1)
        ship_2 = factory.create_ship(imo_id=imo_id_2)
        ship_3 = factory.create_ship(imo_id=imo_id_3)
        screening_1 = factory.create_screening(
            account_id=account_id, ship=ship_1, status=Status.CREATED,
            previous_severity=Severity.OK,
            updated="2001-09-11 07:59:00",
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        screening_2 = factory.create_screening(
            account_id=account_id, ship=ship_2, status=Status.SCHEDULED,
            previous_severity=Severity.CRITICAL,
            updated="2002-09-11 07:59:00",
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        screening_3 = factory.create_screening(
            account_id=account_id, ship=ship_3, status=Status.PENDING,
            previous_severity=Severity.WARNING,
            updated="2003-09-11 07:59:00",
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        screening_4 = factory.create_screening(
            account_id=account_id, ship=ship_3, status=Status.DONE,
            previous_severity=Severity.UNKNOWN,
            updated="2003-09-11 07:59:00",
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        sort = 'status' if reverse else '-status'
        params = {'sort': sort}

        env, resp = test_client.get(
            self.uri, query_string=params, as_tuple=True)

        assert resp.status_code == 200
        expected_order = [screening_4, screening_3, screening_2, screening_1]
        if reverse:
            expected_order = reversed(expected_order)
        expected_data = [
            {
                'id': screening.id,
                'created': '2001-09-11T07:59:00Z',
                'updated': screening.updated.isoformat() + 'Z',
                'account_id': account_id,
                'ship': {
                    'imo_id': screening.ship.imo_id,
                    'name': screening.ship.name,
                    'type': screening.ship.type,
                    'country_id': screening.ship.country_id,
                    'country_name': screening.ship.country_name,
                },
                'ship_id': screening.ship_id,
                'status': screening.status.name,
                'severity': screening.severity.name,
                "severity_change": screening.severity_change.name,
                "previous_severity": screening.previous_severity.name,
                'previous_severity_date': '2001-09-11T07:59:00Z',
            }
            for screening in expected_order
        ]
        assert resp.json == {
            "data": expected_data,
            "meta": {
                "count": len(expected_data),
            },
            "links": {
                "first": (
                    'http://api/v1/screenings?'
                    'sort={0}&page=1'.format(sort)
                ),
                'last': (
                    'http://api/v1/screenings?'
                    'sort={0}&page=1'.format(sort)
                ),
            },
        }

    @freeze_time("2001-09-11 07:59:00")
    def test_get_pagination(self, test_client, factory):
        account_id = 54321
        imo_id_1 = 12345678
        imo_id_2 = 12345679
        imo_id_3 = 12345680
        ship_1 = factory.create_ship(imo_id=imo_id_1, country_id='PL')
        ship_2 = factory.create_ship(imo_id=imo_id_2, country_id='UK')
        ship_3 = factory.create_ship(imo_id=imo_id_3, country_id='US')
        screening_1 = factory.create_screening(
            account_id=account_id, ship=ship_1, severity=Severity.UNKNOWN,
            previous_severity=None,
            previous_severity_date=None,
        )
        screening_2 = factory.create_screening(
            account_id=account_id, ship=ship_2, severity=Severity.OK,
            previous_severity=None,
            previous_severity_date=None,
        )
        screening_3 = factory.create_screening(
            account_id=account_id, ship=ship_3, severity=Severity.WARNING,
            previous_severity=None,
            previous_severity_date=None,
        )
        page = 2
        limit = 1
        params = {'page': page, 'limit': limit}

        env, resp = test_client.get(
            self.uri, query_string=params, as_tuple=True)

        assert resp.status_code == 200
        expected_data = [
            {
                'id': screening_2.id,
                'created': '2001-09-11T07:59:00Z',
                'updated': '2001-09-11T07:59:00Z',
                'account_id': account_id,
                'ship': {
                    'imo_id': screening_2.ship.imo_id,
                    'name': screening_2.ship.name,
                    'type': screening_2.ship.type,
                    'country_id': screening_2.ship.country_id,
                    'country_name': screening_2.ship.country_name,
                },
                'ship_id': screening_2.ship_id,
                'status': screening_2.status.name,
                'severity': screening_2.severity.name,
                "severity_change": screening_2.severity_change.name,
                "previous_severity": screening_2.previous_severity,
                'previous_severity_date': screening_2.previous_severity_date,
            },
        ]
        assert resp.json == {
            "data": expected_data,
            "meta": {
                "count": len([screening_1, screening_2, screening_3]),
            },
            "links": {
                "first": (
                    'http://api/v1/screenings?page=1&limit=1'
                ),
                'last': (
                    'http://api/v1/screenings?page=3&limit=1'
                ),
                'next': (
                    'http://api/v1/screenings?page=3&limit=1'
                ),
                'prev': (
                    'http://api/v1/screenings?page=1&limit=1'
                ),
            },
        }

    @freeze_time("2001-09-11 07:59:00")
    def test_get_search_ship_name(self, test_client, factory):
        account_id = 54321
        imo_id_1 = 12345678
        imo_id_2 = 12345679
        imo_id_3 = 12345680
        ship_1 = factory.create_ship(
            imo_id=imo_id_1, country_id='PL', name='ship_1_name')
        ship_2 = factory.create_ship(
            imo_id=imo_id_2, country_id='UK', name='ship_2_name')
        ship_3 = factory.create_ship(
            imo_id=imo_id_3, country_id='US', name='ship_3_name')
        factory.create_screening(
            account_id=account_id, ship=ship_1, severity=Severity.UNKNOWN,
            previous_severity=Severity.UNKNOWN,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        screening_2 = factory.create_screening(
            account_id=account_id, ship=ship_2, severity=Severity.OK,
            previous_severity=Severity.OK,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        factory.create_screening(
            account_id=account_id, ship=ship_3, severity=Severity.WARNING,
            previous_severity=Severity.WARNING,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        search = 'P_2_n'
        params = {'search': search}

        env, resp = test_client.get(
            self.uri, query_string=params, as_tuple=True)

        assert resp.status_code == 200
        expected_data = [
            {
                'id': screening_2.id,
                'created': '2001-09-11T07:59:00Z',
                'updated': '2001-09-11T07:59:00Z',
                'account_id': account_id,
                'ship': {
                    'imo_id': screening_2.ship.imo_id,
                    'name': screening_2.ship.name,
                    'type': screening_2.ship.type,
                    'country_id': screening_2.ship.country_id,
                    'country_name': screening_2.ship.country_name,
                },
                'ship_id': screening_2.ship_id,
                'status': screening_2.status.name,
                'severity': screening_2.severity.name,
                "severity_change": screening_2.severity_change.name,
                "previous_severity": screening_2.previous_severity.name,
                'previous_severity_date': '2001-09-11T07:59:00Z',
            }
        ]
        assert resp.json == {
            "data": expected_data,
            "meta": {
                "count": len(expected_data),
            },
            "links": {
                "first": (
                    'http://api/v1/screenings?'
                    'search={0}&page=1'.format(search)
                ),
                'last': (
                    'http://api/v1/screenings?'
                    'search={0}&page=1'.format(search)
                ),
            },
        }

    @freeze_time("2001-09-11 07:59:00")
    def test_get_search_ship_imo_id(self, test_client, factory):
        account_id = 54321
        imo_id_1 = 12345678
        imo_id_2 = 12345679
        imo_id_3 = 12345680
        ship_1 = factory.create_ship(imo_id=imo_id_1, country_id='PL')
        ship_2 = factory.create_ship(imo_id=imo_id_2, country_id='UK')
        ship_3 = factory.create_ship(imo_id=imo_id_3, country_id='US')
        factory.create_screening(
            account_id=account_id, ship=ship_1, severity=Severity.UNKNOWN,
            previous_severity=Severity.UNKNOWN,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        screening_2 = factory.create_screening(
            account_id=account_id, ship=ship_2, severity=Severity.OK,
            previous_severity=Severity.OK,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        factory.create_screening(
            account_id=account_id, ship=ship_3, severity=Severity.WARNING,
            previous_severity=Severity.WARNING,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        search = '679'
        params = {'search': search}

        env, resp = test_client.get(
            self.uri, query_string=params, as_tuple=True)

        assert resp.status_code == 200
        expected_data = [
            {
                'id': screening_2.id,
                'created': '2001-09-11T07:59:00Z',
                'updated': '2001-09-11T07:59:00Z',
                'account_id': account_id,
                'ship': {
                    'imo_id': screening_2.ship.imo_id,
                    'name': screening_2.ship.name,
                    'type': screening_2.ship.type,
                    'country_id': screening_2.ship.country_id,
                    'country_name': screening_2.ship.country_name,
                },
                'ship_id': screening_2.ship_id,
                'status': screening_2.status.name,
                'severity': screening_2.severity.name,
                "severity_change": screening_2.severity_change.name,
                "previous_severity": screening_2.previous_severity.name,
                'previous_severity_date': '2001-09-11T07:59:00Z',
            }
        ]
        assert resp.json == {
            "data": expected_data,
            "meta": {
                "count": len(expected_data),
            },
            "links": {
                "first": (
                    'http://api/v1/screenings?'
                    'search={0}&page=1'.format(search)
                ),
                'last': (
                    'http://api/v1/screenings?'
                    'search={0}&page=1'.format(search)
                ),
            },
        }

    @freeze_time("2001-09-11 07:59:00")
    def test_get_filter_country_id(self, test_client, factory):
        account_id = 54321
        imo_id_1 = 12345678
        imo_id_2 = 12345679
        imo_id_3 = 12345680
        ship_1 = factory.create_ship(imo_id=imo_id_1, country_id='PL')
        ship_2 = factory.create_ship(imo_id=imo_id_2, country_id='UK')
        ship_3 = factory.create_ship(imo_id=imo_id_3, country_id='US')
        screening_1 = factory.create_screening(
            account_id=account_id, ship=ship_1, severity=Severity.UNKNOWN,
            previous_severity=Severity.UNKNOWN,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        factory.create_screening(
            account_id=account_id, ship=ship_2, severity=Severity.OK,
            previous_severity=Severity.OK,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        screening_3 = factory.create_screening(
            account_id=account_id, ship=ship_3, severity=Severity.WARNING,
            previous_severity=Severity.WARNING,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        country_ids = 'PL,US'
        params = {'ship__country_ids': country_ids}

        env, resp = test_client.get(
            self.uri, query_string=params, as_tuple=True)

        assert resp.status_code == 200
        expected_data = [
            {
                'id': screening.id,
                'created': '2001-09-11T07:59:00Z',
                'updated': '2001-09-11T07:59:00Z',
                'account_id': account_id,
                'ship': {
                    'imo_id': screening.ship.imo_id,
                    'name': screening.ship.name,
                    'type': screening.ship.type,
                    'country_id': screening.ship.country_id,
                    'country_name': screening.ship.country_name,
                },
                'ship_id': screening.ship_id,
                'status': screening.status.name,
                'severity': screening.severity.name,
                "severity_change": screening.severity_change.name,
                "previous_severity": screening.previous_severity.name,
                'previous_severity_date': '2001-09-11T07:59:00Z',
            } for screening in [screening_1, screening_3]
        ]
        country_ids_enc = quote_plus(country_ids)
        assert resp.json == {
            "data": expected_data,
            "meta": {
                "count": len(expected_data),
            },
            "links": {
                "first": (
                    'http://api/v1/screenings?'
                    'ship__country_ids={0}&page=1'.format(country_ids_enc)
                ),
                'last': (
                    'http://api/v1/screenings?'
                    'ship__country_ids={0}&page=1'.format(country_ids_enc)
                ),
            },
        }

    @freeze_time("2001-09-11 07:59:00")
    def test_get_filter_ship_type(self, test_client, factory):
        account_id = 54321
        imo_id_1 = 12345678
        imo_id_2 = 12345679
        imo_id_3 = 12345680
        ship_1 = factory.create_ship(imo_id=imo_id_1, type='Bulk Carrier')
        ship_2 = factory.create_ship(imo_id=imo_id_2, type='Container')
        ship_3 = factory.create_ship(imo_id=imo_id_3, type='Crude Oil Tanker')
        screening_1 = factory.create_screening(
            account_id=account_id, ship=ship_1, severity=Severity.UNKNOWN,
            previous_severity=Severity.UNKNOWN,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        factory.create_screening(
            account_id=account_id, ship=ship_2, severity=Severity.OK,
            previous_severity=Severity.OK,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        screening_3 = factory.create_screening(
            account_id=account_id, ship=ship_3, severity=Severity.WARNING,
            previous_severity=Severity.WARNING,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        ship_types = 'Bulk Carrier,Crude Oil Tanker'
        params = {'ship__types': ship_types}

        env, resp = test_client.get(
            self.uri, query_string=params, as_tuple=True)

        assert resp.status_code == 200
        expected_data = [
            {
                'id': screening.id,
                'created': '2001-09-11T07:59:00Z',
                'updated': '2001-09-11T07:59:00Z',
                'account_id': account_id,
                'ship': {
                    'imo_id': screening.ship.imo_id,
                    'name': screening.ship.name,
                    'type': screening.ship.type,
                    'country_id': screening.ship.country_id,
                    'country_name': screening.ship.country_name,
                },
                'ship_id': screening.ship_id,
                'status': screening.status.name,
                'severity': screening.severity.name,
                "severity_change": screening.severity_change.name,
                "previous_severity": screening.previous_severity.name,
                'previous_severity_date': '2001-09-11T07:59:00Z',
            } for screening in [screening_1, screening_3]
        ]
        ship_types_enc = quote_plus(ship_types)
        assert resp.json == {
            "data": expected_data,
            "meta": {
                "count": len(expected_data),
            },
            "links": {
                "first": (
                    'http://api/v1/screenings?'
                    'ship__types={0}&page=1'.format(ship_types_enc)
                ),
                'last': (
                    'http://api/v1/screenings?'
                    'ship__types={0}&page=1'.format(ship_types_enc)
                ),
            },
        }

    @freeze_time("2001-09-11 07:59:00")
    def test_get_filter_severities(self, test_client, factory):
        account_id = 54321
        imo_id = 12345678
        ship = factory.create_ship(imo_id=imo_id, type='Bulk Carrier')
        screening_1 = factory.create_screening(
            account_id=account_id, ship=ship, severity=Severity.UNKNOWN,
            previous_severity=Severity.UNKNOWN,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        factory.create_screening(
            account_id=account_id, ship=ship, severity=Severity.OK,
            previous_severity=Severity.OK,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        screening_3 = factory.create_screening(
            account_id=account_id, ship=ship, severity=Severity.WARNING,
            previous_severity=Severity.WARNING,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        severities = 'UNKNOWN,WARNING'
        params = {'severities': severities}

        env, resp = test_client.get(
            self.uri, query_string=params, as_tuple=True)

        assert resp.status_code == 200
        expected_data = [
            {
                'id': screening.id,
                'created': '2001-09-11T07:59:00Z',
                'updated': '2001-09-11T07:59:00Z',
                'account_id': account_id,
                'ship': {
                    'imo_id': screening.ship.imo_id,
                    'name': screening.ship.name,
                    'type': screening.ship.type,
                    'country_id': screening.ship.country_id,
                    'country_name': screening.ship.country_name,
                },
                'ship_id': screening.ship_id,
                'status': screening.status.name,
                'severity': screening.severity.name,
                "severity_change": screening.severity_change.name,
                "previous_severity": screening.previous_severity.name,
                'previous_severity_date': '2001-09-11T07:59:00Z',
            } for screening in [screening_1, screening_3]
        ]
        severities_enc = quote_plus(severities)
        assert resp.json == {
            "data": expected_data,
            "meta": {
                "count": len(expected_data),
            },
            "links": {
                "first": (
                    'http://api/v1/screenings?'
                    'severities={0}&page=1'.format(severities_enc)
                ),
                'last': (
                    'http://api/v1/screenings?'
                    'severities={0}&page=1'.format(severities_enc)
                ),
            },
        }

    @pytest.mark.parametrize('check_name', [
        'company_sanctions', 'ship_sanctions', 'country_sanctions',
        'ship_inspections', 'ship_movements',
    ])
    @freeze_time("2001-09-11 07:59:00")
    def test_filter_check_severities(self, test_client, factory, check_name):
        account_id = 54321
        imo_id = 12345678
        check_severity_field_name = '{0}_severity'.format(check_name)
        check_param_name = '{0}_severities'.format(check_name)
        ship = factory.create_ship(imo_id=imo_id, type='Bulk Carrier')
        screening_1 = factory.create_screening(
            account_id=account_id, ship=ship,
            previous_severity=Severity.UNKNOWN,
            previous_severity_date='2001-09-11T07:59:00Z',
            **{check_severity_field_name: Severity.UNKNOWN},
        )
        factory.create_screening(
            account_id=account_id, ship=ship,
            previous_severity=Severity.OK,
            previous_severity_date='2001-09-11T07:59:00Z',
            **{check_severity_field_name: Severity.OK},
        )
        screening_3 = factory.create_screening(
            account_id=account_id, ship=ship,
            previous_severity=Severity.WARNING,
            previous_severity_date='2001-09-11T07:59:00Z',
            **{check_severity_field_name: Severity.WARNING},
        )
        severities = 'UNKNOWN,WARNING'
        params = {check_param_name: severities}

        env, resp = test_client.get(
            self.uri, query_string=params, as_tuple=True)

        assert resp.status_code == 200
        expected_data = [
            {
                'id': screening.id,
                'created': '2001-09-11T07:59:00Z',
                'updated': '2001-09-11T07:59:00Z',
                'account_id': account_id,
                'ship': {
                    'imo_id': screening.ship.imo_id,
                    'name': screening.ship.name,
                    'type': screening.ship.type,
                    'country_id': screening.ship.country_id,
                    'country_name': screening.ship.country_name,
                },
                'ship_id': screening.ship_id,
                'status': screening.status.name,
                'severity': screening.severity.name,
                "severity_change": screening.severity_change.name,
                "previous_severity": screening.previous_severity.name,
                'previous_severity_date': '2001-09-11T07:59:00Z',
            } for screening in [screening_1, screening_3]
        ]
        severities_enc = quote_plus(severities)
        assert resp.json == {
            "data": expected_data,
            "meta": {
                "count": len(expected_data),
            },
            "links": {
                "first": (
                    'http://api/v1/screenings?'
                    '{0}={1}&page=1'.format(check_param_name, severities_enc)
                ),
                'last': (
                    'http://api/v1/screenings?'
                    '{0}={1}&page=1'.format(check_param_name, severities_enc)
                ),
            },
        }

    @freeze_time("2001-09-11 07:59:00")
    def test_get_filter_severity_change(self, test_client, factory):
        account_id = 54321
        imo_id = 12345678
        ship = factory.create_ship(imo_id=imo_id, type='Bulk Carrier')
        factory.create_screening(
            account_id=account_id, ship=ship,
            severity_change=SeverityChange.INCREASED,
            previous_severity=Severity.UNKNOWN,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        screening_2 = factory.create_screening(
            account_id=account_id, ship=ship,
            severity_change=SeverityChange.DECREASED,
            previous_severity=Severity.OK,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        factory.create_screening(
            account_id=account_id, ship=ship,
            severity_change=SeverityChange.NOCHANGE,
            previous_severity=Severity.WARNING,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        severity_change = 'DECREASED'
        params = {'severity_change': severity_change}

        env, resp = test_client.get(
            self.uri, query_string=params, as_tuple=True)

        assert resp.status_code == 200
        expected_data = [
            {
                'id': screening.id,
                'created': '2001-09-11T07:59:00Z',
                'updated': '2001-09-11T07:59:00Z',
                'account_id': account_id,
                'ship': {
                    'imo_id': screening.ship.imo_id,
                    'name': screening.ship.name,
                    'type': screening.ship.type,
                    'country_id': screening.ship.country_id,
                    'country_name': screening.ship.country_name,
                },
                'ship_id': screening.ship_id,
                'status': screening.status.name,
                'severity': screening.severity.name,
                "severity_change": screening.severity_change.name,
                "previous_severity": screening.previous_severity.name,
                'previous_severity_date': '2001-09-11T07:59:00Z',
            } for screening in [screening_2, ]
        ]
        assert resp.json == {
            "data": expected_data,
            "meta": {
                "count": len(expected_data),
            },
            "links": {
                "first": (
                    'http://api/v1/screenings?'
                    'severity_change={0}&page=1'.format(severity_change)
                ),
                'last': (
                    'http://api/v1/screenings?'
                    'severity_change={0}&page=1'.format(severity_change)
                ),
            },
        }

    @freeze_time("2001-09-11 07:59:00")
    def test_get_filter_ids(self, test_client, factory):
        account_id = 54321
        imo_id = 12345678
        ship = factory.create_ship(imo_id=imo_id, type='Bulk Carrier')
        factory.create_screening(
            account_id=account_id, ship=ship,
            severity_change=SeverityChange.INCREASED,
            previous_severity=Severity.UNKNOWN,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        screening_2 = factory.create_screening(
            account_id=account_id, ship=ship,
            severity_change=SeverityChange.DECREASED,
            previous_severity=Severity.OK,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        screening_3 = factory.create_screening(
            account_id=account_id, ship=ship,
            severity_change=SeverityChange.NOCHANGE,
            previous_severity=Severity.WARNING,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        factory.create_screening(
            account_id=account_id, ship=ship,
            severity_change=SeverityChange.NOCHANGE,
            previous_severity=Severity.OK,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        ids = ','.join([str(s.id) for s in (screening_2, screening_3)])
        params = {'ids': ids}

        env, resp = test_client.get(
            self.uri, query_string=params, as_tuple=True)

        assert resp.status_code == 200
        expected_data = [
            {
                'id': screening.id,
                'created': '2001-09-11T07:59:00Z',
                'updated': '2001-09-11T07:59:00Z',
                'account_id': account_id,
                'ship': {
                    'imo_id': screening.ship.imo_id,
                    'name': screening.ship.name,
                    'type': screening.ship.type,
                    'country_id': screening.ship.country_id,
                    'country_name': screening.ship.country_name,
                },
                'ship_id': screening.ship_id,
                'status': screening.status.name,
                'severity': screening.severity.name,
                "severity_change": screening.severity_change.name,
                "previous_severity": screening.previous_severity.name,
                'previous_severity_date': '2001-09-11T07:59:00Z',
            } for screening in [screening_2, screening_3]
        ]
        ids_enc = quote_plus(ids)
        assert resp.json == {
            "data": expected_data,
            "meta": {
                "count": len(expected_data),
            },
            "links": {
                "first": (
                    'http://api/v1/screenings?'
                    'ids={0}&page=1'.format(ids_enc)
                ),
                'last': (
                    'http://api/v1/screenings?'
                    'ids={0}&page=1'.format(ids_enc)
                ),
            },
        }


@pytest.mark.usefixtures('authenticated')
class TestScreeningsViewDelete:

    uri = '/v1/screenings'

    def test_unauthenticated(self, test_client):
        test_client.environ_base['HTTP_AUTHORIZATION'] = ''

        env, resp = test_client.delete(self.uri, as_tuple=True)

        assert resp.status_code == 401

    def test_non_existing(self, test_client):
        ids = '12,13,14'
        params = {'ids': ids}

        env, resp = test_client.delete(
            self.uri, query_string=params, as_tuple=True)

        assert resp.status_code == 204
        assert not resp.data

    def test_delete_ids(self, test_client, factory, application):
        account_id = 54321
        imo_id_1 = 12345678
        imo_id_2 = 12345679
        imo_id_3 = 12345680
        ship_1 = factory.create_ship(imo_id=imo_id_1, type='Bulk Carrier')
        ship_2 = factory.create_ship(imo_id=imo_id_2, type='Container')
        ship_3 = factory.create_ship(imo_id=imo_id_3, type='Crude Oil Tanker')
        screening_1 = factory.create_screening(
            account_id=account_id, ship=ship_1, severity=Severity.UNKNOWN)
        screening_2 = factory.create_screening(
            account_id=account_id, ship=ship_2, severity=Severity.OK)
        screening_3 = factory.create_screening(
            account_id=account_id, ship=ship_3, severity=Severity.WARNING)
        screenings = [screening_2, screening_3]
        screenings_ids_list = map(lambda x: x.id, screenings)
        ids = ','.join(map(str, screenings_ids_list))
        params = {'ids': ids}

        env, resp = test_client.delete(
            self.uri, query_string=params, as_tuple=True)

        assert resp.status_code == 204
        assert not resp.data

        screenings = application.screenings_repository.find()
        assert len(screenings) == 1
        assert screenings[0].id == screening_1.id

    def test_delete_orphans(self, test_client, factory, application):
        account_id = 54321
        imo_id_1 = 12345678
        imo_id_2 = 12345679
        imo_id_3 = 12345680
        ship_1 = factory.create_ship(imo_id=imo_id_1, type='Bulk Carrier')
        ship_2 = factory.create_ship(imo_id=imo_id_2, type='Container')
        ship_3 = factory.create_ship(imo_id=imo_id_3, type='Crude Oil Tanker')
        factory.create_screening(
            account_id=account_id, ship=ship_1, severity=Severity.UNKNOWN)
        screening_2 = factory.create_screening(
            account_id=account_id, ship=ship_2, severity=Severity.OK)
        screening_3 = factory.create_screening(
            account_id=account_id, ship=ship_3, severity=Severity.WARNING)
        screenings = [screening_2, screening_3]
        screenings_ids_list = map(lambda x: x.id, screenings)
        ids = ','.join(map(str, screenings_ids_list))
        params = {'ids': ids}

        env, resp = test_client.delete(
            self.uri, query_string=params, as_tuple=True)

        assert resp.status_code == 204
        assert not resp.data

        ships = application.ships_repository.find()
        assert len(ships) == 1
        assert ships[0].id == ship_1.id

    def test_delete_search_ship_name(self, test_client, factory, application):
        account_id = 54321
        imo_id_1 = 12345678
        imo_id_2 = 12345679
        imo_id_3 = 12345680
        ship_1 = factory.create_ship(
            name='Ship1', imo_id=imo_id_1, type='Bulk Carrier')
        ship_2 = factory.create_ship(
            name='Ship2', imo_id=imo_id_2, type='Container')
        ship_3 = factory.create_ship(
            name='Crude1', imo_id=imo_id_3, type='Crude Oil Tanker')
        factory.create_screening(
            account_id=account_id, ship=ship_1, severity=Severity.UNKNOWN)
        factory.create_screening(
            account_id=account_id, ship=ship_2, severity=Severity.OK)
        screening_3 = factory.create_screening(
            account_id=account_id, ship=ship_3, severity=Severity.WARNING)
        params = {'search': 'Ship'}

        env, resp = test_client.delete(
            self.uri, query_string=params, as_tuple=True)

        assert resp.status_code == 204
        assert not resp.data

        screenings = application.screenings_repository.find()
        assert len(screenings) == 1
        assert screenings[0].id == screening_3.id

    @freeze_time("2001-09-11 07:59:00")
    def test_delete_search_ship_imo_id(
            self, test_client, factory, application):
        account_id = 54321
        imo_id_1 = 12345678
        imo_id_2 = 12345679
        imo_id_3 = 12345680
        ship_1 = factory.create_ship(imo_id=imo_id_1, country_id='PL')
        ship_2 = factory.create_ship(imo_id=imo_id_2, country_id='UK')
        ship_3 = factory.create_ship(imo_id=imo_id_3, country_id='US')
        factory.create_screening(
            account_id=account_id, ship=ship_1, severity=Severity.UNKNOWN,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        factory.create_screening(
            account_id=account_id, ship=ship_2, severity=Severity.OK,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        screening_3 = factory.create_screening(
            account_id=account_id, ship=ship_3, severity=Severity.WARNING,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        search = '234567'
        params = {'search': search}

        env, resp = test_client.delete(
            self.uri, query_string=params, as_tuple=True)

        assert resp.status_code == 204
        assert not resp.data

        screenings = application.screenings_repository.find()
        assert len(screenings) == 1
        assert screenings[0].id == screening_3.id

    @freeze_time("2001-09-11 07:59:00")
    def test_delete_filter_country_id(self, test_client, factory, application):
        account_id = 54321
        imo_id_1 = 12345678
        imo_id_2 = 12345679
        imo_id_3 = 12345680
        ship_1 = factory.create_ship(imo_id=imo_id_1, country_id='PL')
        ship_2 = factory.create_ship(imo_id=imo_id_2, country_id='UK')
        ship_3 = factory.create_ship(imo_id=imo_id_3, country_id='US')
        factory.create_screening(
            account_id=account_id, ship=ship_1, severity=Severity.UNKNOWN,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        factory.create_screening(
            account_id=account_id, ship=ship_2, severity=Severity.OK,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        screening_3 = factory.create_screening(
            account_id=account_id, ship=ship_3, severity=Severity.WARNING,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        country_ids = 'PL,UK'
        params = {'ship__country_ids': country_ids}

        env, resp = test_client.delete(
            self.uri, query_string=params, as_tuple=True)

        assert resp.status_code == 204
        assert not resp.data

        screenings = application.screenings_repository.find()
        assert len(screenings) == 1
        assert screenings[0].id == screening_3.id

    @freeze_time("2001-09-11 07:59:00")
    def test_delete_filter_ship_type(self, test_client, factory, application):
        account_id = 54321
        imo_id_1 = 12345678
        imo_id_2 = 12345679
        imo_id_3 = 12345680
        ship_1 = factory.create_ship(imo_id=imo_id_1, type='Bulk Carrier')
        ship_2 = factory.create_ship(imo_id=imo_id_2, type='Container')
        ship_3 = factory.create_ship(imo_id=imo_id_3, type='Crude Oil Tanker')
        factory.create_screening(
            account_id=account_id, ship=ship_1, severity=Severity.UNKNOWN,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        factory.create_screening(
            account_id=account_id, ship=ship_2, severity=Severity.OK,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        screening_3 = factory.create_screening(
            account_id=account_id, ship=ship_3, severity=Severity.WARNING,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        ship_types = 'Bulk Carrier,Container'
        params = {'ship__types': ship_types}

        env, resp = test_client.delete(
            self.uri, query_string=params, as_tuple=True)

        assert resp.status_code == 204
        assert not resp.data

        screenings = application.screenings_repository.find()
        assert len(screenings) == 1
        assert screenings[0].id == screening_3.id

    @freeze_time("2001-09-11 07:59:00")
    def test_delete_filter_severities(self, test_client, factory, application):
        account_id = 54321
        imo_id = 12345678
        ship = factory.create_ship(imo_id=imo_id, type='Bulk Carrier')
        factory.create_screening(
            account_id=account_id, ship=ship, severity=Severity.UNKNOWN,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        factory.create_screening(
            account_id=account_id, ship=ship, severity=Severity.OK,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        screening_3 = factory.create_screening(
            account_id=account_id, ship=ship, severity=Severity.WARNING,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        severities = 'UNKNOWN,OK'
        params = {'severities': severities}

        env, resp = test_client.delete(
            self.uri, query_string=params, as_tuple=True)

        assert resp.status_code == 204
        assert not resp.data

        screenings = application.screenings_repository.find()
        assert len(screenings) == 1
        assert screenings[0].id == screening_3.id

    @freeze_time("2001-09-11 07:59:00")
    def test_delete_filter_severity_change(
            self, test_client, factory, application):
        account_id = 54321
        imo_id = 12345678
        ship = factory.create_ship(imo_id=imo_id, type='Bulk Carrier')
        factory.create_screening(
            account_id=account_id, ship=ship,
            severity_change=SeverityChange.INCREASED,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        factory.create_screening(
            account_id=account_id, ship=ship,
            severity_change=SeverityChange.INCREASED,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        screening_3 = factory.create_screening(
            account_id=account_id, ship=ship,
            severity_change=SeverityChange.NOCHANGE,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        severity_change = 'INCREASED'
        params = {'severity_change': severity_change}

        env, resp = test_client.delete(
            self.uri, query_string=params, as_tuple=True)

        screenings = application.screenings_repository.find()
        assert len(screenings) == 1
        assert screenings[0].id == screening_3.id


class TestScreeningViewOptions:

    @pytest.fixture
    def screening(self, factory):
        account_id = 654321
        imo_id = 654321
        ship_1 = factory.create_ship(imo_id=imo_id, country_id='PL')
        return factory.create_screening(
            account_id=account_id, ship=ship_1, severity=Severity.UNKNOWN)

    def get_uri(self, screening_id):
        return '/v1/screenings/{0}'.format(screening_id)

    def test_allowed_methods(self, test_client, screening):
        env, resp = test_client.options(
            self.get_uri(screening.id), as_tuple=True)

        assert resp.status_code == 200
        assert set(resp.allow) == set(['OPTIONS', 'GET', 'HEAD'])
        assert resp.headers['Access-Control-Allow-Origin'] == '*'


@pytest.mark.usefixtures('authenticated')
class TestScreeningViewGet:

    def get_uri(self, screening_id):
        return '/v1/screenings/{0}'.format(screening_id)

    def test_unauthenticated(self, test_client):
        test_client.environ_base['HTTP_AUTHORIZATION'] = ''
        screening_id = 0

        env, resp = test_client.get(self.get_uri(screening_id), as_tuple=True)

        assert resp.status_code == 401

    def test_screening_not_found(self, test_client):
        screening_id = 0
        env, resp = test_client.get(self.get_uri(screening_id), as_tuple=True)

        assert resp.status_code == 404

    @freeze_time("2001-09-11 07:59:00")
    def test_valid(self, test_client, factory):
        account_id = 54321
        imo_id = 654321
        ship_1 = factory.create_ship(imo_id=imo_id, country_id='PL')
        screening = factory.create_screening(
            account_id=account_id, ship=ship_1, severity=Severity.UNKNOWN)

        env, resp = test_client.get(self.get_uri(screening.id), as_tuple=True)

        assert resp.status_code == 200
        assert resp.json == {
            "data": {
                'id': screening.id,
                'created': '2001-09-11T07:59:00Z',
                'updated': '2001-09-11T07:59:00Z',
                'status': screening.status.name,
                'company_sanctions_status':
                    screening.company_sanctions_status.name,
                'ship_sanctions_status':
                    screening.ship_sanctions_status.name,
                'country_sanctions_status':
                    screening.country_sanctions_status.name,
                'ship_inspections_status':
                    screening.ship_inspections_status.name,
                'ship_movements_status':
                    screening.ship_movements_status.name,
                'severity': screening.severity.name,
                'company_sanctions_severity':
                    screening.company_sanctions_severity.name,
                'ship_sanctions_severity':
                    screening.ship_sanctions_severity.name,
                'country_sanctions_severity':
                    screening.country_sanctions_severity.name,
                'ship_inspections_severity':
                    screening.ship_inspections_severity.name,
                'ship_movements_severity':
                    screening.ship_movements_severity.name,
            },
        }


class TestScreenViewOptions:

    uri = '/v1/screenings/screen'

    def test_unauthenticated(self, test_client):
        test_client.environ_base['HTTP_AUTHORIZATION'] = ''

        env, resp = test_client.get(self.uri, as_tuple=True)

        assert resp.status_code == 401

    def test_allowed_methods(self, test_client):
        env, resp = test_client.options(self.uri, as_tuple=True)

        assert resp.status_code == 200
        assert set(resp.allow) == set(['OPTIONS', 'GET', 'POST', 'HEAD'])
        assert resp.headers['Access-Control-Allow-Origin'] == '*'


@pytest.mark.usefixtures('authenticated')
class TestScreenViewPost:

    uri = '/v1/screenings/screen'

    def test_unauthenticated(self, test_client):
        test_client.environ_base['HTTP_AUTHORIZATION'] = ''

        env, resp = test_client.post(self.uri, as_tuple=True)

        assert resp.status_code == 401

    @mock.patch('screening_api.lib.messaging.publishers.get_origin')
    @mock.patch('screening_api.lib.messaging.publishers.uuid')
    @mock.patch('kombu.messaging.Producer.publish')
    def test_invalid_account_id(
            self, m_publish, m_uuid, m_get_origin, test_client, factory):
        frozen_uuid = '12345678-1234-1234-1234-1234567890ab'
        frozen_origin = 'origin@host'
        m_publish.return_value = None
        m_uuid.return_value = frozen_uuid
        m_get_origin.return_value = frozen_origin
        account_id_2 = 55555
        ship_1 = factory.create_ship()
        ship_2 = factory.create_ship()
        screening_1 = factory.create_screening(
            ship=ship_1, account_id=account_id_2)
        screening_2 = factory.create_screening(
            ship=ship_2, account_id=account_id_2)
        screenings = [screening_1, screening_2]
        screenings_ids = list(map(lambda x: x.id, screenings))
        ids = ','.join(map(str, screenings_ids))
        params = {'ids': ids}

        env, resp = test_client.post(
            self.uri, query_string=params, as_tuple=True)

        assert resp.status_code == 202
        assert not resp.data

        assert not m_publish.called

    @mock.patch('screening_api.lib.messaging.publishers.get_origin')
    @mock.patch('screening_api.lib.messaging.publishers.uuid')
    @mock.patch('kombu.messaging.Producer.publish')
    def test_valid(
            self, m_publish, m_uuid, m_get_origin, test_client, factory):
        frozen_uuid = '12345678-1234-1234-1234-1234567890ab'
        frozen_origin = 'origin@host'
        m_publish.return_value = None
        m_uuid.return_value = frozen_uuid
        m_get_origin.return_value = frozen_origin
        account_id = 54321
        ship_1 = factory.create_ship()
        ship_2 = factory.create_ship()
        screening_1 = factory.create_screening(
            ship=ship_1, account_id=account_id)
        screening_2 = factory.create_screening(
            ship=ship_2, account_id=account_id)
        screenings = [screening_1, screening_2]
        screenings_ids = list(map(lambda x: x.id, screenings))
        ids = ','.join(map(str, screenings_ids))
        params = {'ids': ids}

        env, resp = test_client.post(
            self.uri, query_string=params, as_tuple=True)

        assert resp.status_code == 202
        assert not resp.data

        assert m_publish.call_count == len(screenings)
        calls = [
            mock.call(
                json.dumps(
                    [[screening.id], {}, None]
                ),
                content_encoding='utf-8', content_type='application/json',
                correlation_id=frozen_uuid,
                headers={
                    'id': frozen_uuid,
                    'lang': CeleryTaskPublisher.lang,
                    'task': ScreeningsScreenSubscriber.name,
                    'argsrepr': str((screening.id,)),
                    'kwargsrepr': str({}),
                    'origin': frozen_origin,
                }
            )
            for screening in screenings
        ]
        m_publish.assert_has_calls(calls, any_order=True)

    @freeze_time("2001-09-11 07:59:00")
    @mock.patch('screening_api.lib.messaging.publishers.get_origin')
    @mock.patch('screening_api.lib.messaging.publishers.uuid')
    @mock.patch('kombu.messaging.Producer.publish')
    def test_post_ids(
            self, m_publish, m_uuid, m_get_origin, test_client, factory,
            application):
        frozen_uuid = '12345678-1234-1234-1234-1234567890ab'
        frozen_origin = 'origin@host'
        m_publish.return_value = None
        m_uuid.return_value = frozen_uuid
        m_get_origin.return_value = frozen_origin
        account_id = 54321
        imo_id_1 = 12345678
        imo_id_2 = 12345679
        imo_id_3 = 12345680
        ship_1 = factory.create_ship(imo_id=imo_id_1, type='Bulk Carrier')
        ship_2 = factory.create_ship(imo_id=imo_id_2, type='Container')
        ship_3 = factory.create_ship(imo_id=imo_id_3, type='Crude Oil Tanker')
        screening_1 = factory.create_screening(
            account_id=account_id, ship=ship_1, severity=Severity.UNKNOWN)
        screening_2 = factory.create_screening(
            account_id=account_id, ship=ship_2, severity=Severity.OK)
        factory.create_screening(
            account_id=account_id, ship=ship_3, severity=Severity.WARNING)
        screenings = [screening_1, screening_2]
        screenings_ids_list = map(lambda x: x.id, screenings)
        ids = ','.join(map(str, screenings_ids_list))
        params = {'ids': ids}

        env, resp = test_client.post(
            self.uri, query_string=params, as_tuple=True)

        assert resp.status_code == 202
        assert not resp.data

        assert m_publish.call_count == 2
        calls = [
            mock.call(
                json.dumps(
                    [[screening.id], {}, None]
                ),
                content_encoding='utf-8', content_type='application/json',
                correlation_id=frozen_uuid,
                headers={
                    'id': frozen_uuid,
                    'lang': CeleryTaskPublisher.lang,
                    'task': ScreeningsScreenSubscriber.name,
                    'argsrepr': str((screening.id,)),
                    'kwargsrepr': str({}),
                    'origin': frozen_origin,
                }
            )
            for screening in [screening_1, screening_2]
        ]
        m_publish.assert_has_calls(calls, any_order=True)

    @freeze_time("2001-09-11 07:59:00")
    @mock.patch('screening_api.lib.messaging.publishers.get_origin')
    @mock.patch('screening_api.lib.messaging.publishers.uuid')
    @mock.patch('kombu.messaging.Producer.publish')
    def test_post_search_ship_name(
            self, m_publish, m_uuid, m_get_origin, test_client, factory,
            application):
        frozen_uuid = '12345678-1234-1234-1234-1234567890ab'
        frozen_origin = 'origin@host'
        m_publish.return_value = None
        m_uuid.return_value = frozen_uuid
        m_get_origin.return_value = frozen_origin
        account_id = 54321
        imo_id_1 = 12345678
        imo_id_2 = 12345679
        imo_id_3 = 12345680
        ship_1 = factory.create_ship(
            name='Ship1', imo_id=imo_id_1, type='Bulk Carrier')
        ship_2 = factory.create_ship(
            name='Ship2', imo_id=imo_id_2, type='Container')
        ship_3 = factory.create_ship(
            name='Crude1', imo_id=imo_id_3, type='Crude Oil Tanker')
        screening_1 = factory.create_screening(
            account_id=account_id, ship=ship_1, severity=Severity.UNKNOWN)
        screening_2 = factory.create_screening(
            account_id=account_id, ship=ship_2, severity=Severity.OK)
        factory.create_screening(
            account_id=account_id, ship=ship_3, severity=Severity.WARNING)
        params = {'search': 'Ship'}

        env, resp = test_client.post(
            self.uri, query_string=params, as_tuple=True)

        assert resp.status_code == 202
        assert not resp.data

        assert m_publish.call_count == 2
        calls = [
            mock.call(
                json.dumps(
                    [[screening.id], {}, None]
                ),
                content_encoding='utf-8', content_type='application/json',
                correlation_id=frozen_uuid,
                headers={
                    'id': frozen_uuid,
                    'lang': CeleryTaskPublisher.lang,
                    'task': ScreeningsScreenSubscriber.name,
                    'argsrepr': str((screening.id,)),
                    'kwargsrepr': str({}),
                    'origin': frozen_origin,
                }
            )
            for screening in [screening_1, screening_2]
        ]
        m_publish.assert_has_calls(calls, any_order=True)

    @freeze_time("2001-09-11 07:59:00")
    @mock.patch('screening_api.lib.messaging.publishers.get_origin')
    @mock.patch('screening_api.lib.messaging.publishers.uuid')
    @mock.patch('kombu.messaging.Producer.publish')
    def test_post_search_ship_imo_id(
            self, m_publish, m_uuid, m_get_origin, test_client, factory,
            application):
        frozen_uuid = '12345678-1234-1234-1234-1234567890ab'
        frozen_origin = 'origin@host'
        m_publish.return_value = None
        m_uuid.return_value = frozen_uuid
        m_get_origin.return_value = frozen_origin
        account_id = 54321
        imo_id_1 = 12345678
        imo_id_2 = 12345679
        imo_id_3 = 12345680
        ship_1 = factory.create_ship(imo_id=imo_id_1, country_id='PL')
        ship_2 = factory.create_ship(imo_id=imo_id_2, country_id='UK')
        ship_3 = factory.create_ship(imo_id=imo_id_3, country_id='US')
        screening_1 = factory.create_screening(
            account_id=account_id, ship=ship_1, severity=Severity.UNKNOWN,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        screening_2 = factory.create_screening(
            account_id=account_id, ship=ship_2, severity=Severity.OK,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        factory.create_screening(
            account_id=account_id, ship=ship_3, severity=Severity.WARNING,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        search = '234567'
        params = {'search': search}

        env, resp = test_client.post(
            self.uri, query_string=params, as_tuple=True)

        assert resp.status_code == 202
        assert not resp.data

        assert m_publish.call_count == 2
        calls = [
            mock.call(
                json.dumps(
                    [[screening.id], {}, None]
                ),
                content_encoding='utf-8', content_type='application/json',
                correlation_id=frozen_uuid,
                headers={
                    'id': frozen_uuid,
                    'lang': CeleryTaskPublisher.lang,
                    'task': ScreeningsScreenSubscriber.name,
                    'argsrepr': str((screening.id,)),
                    'kwargsrepr': str({}),
                    'origin': frozen_origin,
                }
            )
            for screening in [screening_1, screening_2]
        ]
        m_publish.assert_has_calls(calls, any_order=True)

    @freeze_time("2001-09-11 07:59:00")
    @mock.patch('screening_api.lib.messaging.publishers.get_origin')
    @mock.patch('screening_api.lib.messaging.publishers.uuid')
    @mock.patch('kombu.messaging.Producer.publish')
    def test_post_filter_country_id(
            self, m_publish, m_uuid, m_get_origin, test_client, factory,
            application):
        frozen_uuid = '12345678-1234-1234-1234-1234567890ab'
        frozen_origin = 'origin@host'
        m_publish.return_value = None
        m_uuid.return_value = frozen_uuid
        m_get_origin.return_value = frozen_origin
        account_id = 54321
        imo_id_1 = 12345678
        imo_id_2 = 12345679
        imo_id_3 = 12345680
        ship_1 = factory.create_ship(imo_id=imo_id_1, country_id='PL')
        ship_2 = factory.create_ship(imo_id=imo_id_2, country_id='UK')
        ship_3 = factory.create_ship(imo_id=imo_id_3, country_id='US')
        screening_1 = factory.create_screening(
            account_id=account_id, ship=ship_1, severity=Severity.UNKNOWN,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        screening_2 = factory.create_screening(
            account_id=account_id, ship=ship_2, severity=Severity.OK,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        factory.create_screening(
            account_id=account_id, ship=ship_3, severity=Severity.WARNING,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        country_ids = 'PL,UK'
        params = {'ship__country_ids': country_ids}

        env, resp = test_client.post(
            self.uri, query_string=params, as_tuple=True)

        assert resp.status_code == 202
        assert not resp.data

        assert m_publish.call_count == 2
        calls = [
            mock.call(
                json.dumps(
                    [[screening.id], {}, None]
                ),
                content_encoding='utf-8', content_type='application/json',
                correlation_id=frozen_uuid,
                headers={
                    'id': frozen_uuid,
                    'lang': CeleryTaskPublisher.lang,
                    'task': ScreeningsScreenSubscriber.name,
                    'argsrepr': str((screening.id,)),
                    'kwargsrepr': str({}),
                    'origin': frozen_origin,
                }
            )
            for screening in [screening_1, screening_2]
        ]
        m_publish.assert_has_calls(calls, any_order=True)

    @freeze_time("2001-09-11 07:59:00")
    @mock.patch('screening_api.lib.messaging.publishers.get_origin')
    @mock.patch('screening_api.lib.messaging.publishers.uuid')
    @mock.patch('kombu.messaging.Producer.publish')
    def test_post_filter_ship_type(
            self, m_publish, m_uuid, m_get_origin, test_client, factory,
            application):
        frozen_uuid = '12345678-1234-1234-1234-1234567890ab'
        frozen_origin = 'origin@host'
        m_publish.return_value = None
        m_uuid.return_value = frozen_uuid
        m_get_origin.return_value = frozen_origin
        account_id = 54321
        imo_id_1 = 12345678
        imo_id_2 = 12345679
        imo_id_3 = 12345680
        ship_1 = factory.create_ship(imo_id=imo_id_1, type='Bulk Carrier')
        ship_2 = factory.create_ship(imo_id=imo_id_2, type='Container')
        ship_3 = factory.create_ship(imo_id=imo_id_3, type='Crude Oil Tanker')
        screening_1 = factory.create_screening(
            account_id=account_id, ship=ship_1, severity=Severity.UNKNOWN,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        screening_2 = factory.create_screening(
            account_id=account_id, ship=ship_2, severity=Severity.OK,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        factory.create_screening(
            account_id=account_id, ship=ship_3, severity=Severity.WARNING,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        ship_types = 'Bulk Carrier,Container'
        params = {'ship__types': ship_types}

        env, resp = test_client.post(
            self.uri, query_string=params, as_tuple=True)

        assert resp.status_code == 202
        assert not resp.data

        assert m_publish.call_count == 2
        calls = [
            mock.call(
                json.dumps(
                    [[screening.id], {}, None]
                ),
                content_encoding='utf-8', content_type='application/json',
                correlation_id=frozen_uuid,
                headers={
                    'id': frozen_uuid,
                    'lang': CeleryTaskPublisher.lang,
                    'task': ScreeningsScreenSubscriber.name,
                    'argsrepr': str((screening.id,)),
                    'kwargsrepr': str({}),
                    'origin': frozen_origin,
                }
            )
            for screening in [screening_1, screening_2]
        ]
        m_publish.assert_has_calls(calls, any_order=True)

    @freeze_time("2001-09-11 07:59:00")
    @mock.patch('screening_api.lib.messaging.publishers.get_origin')
    @mock.patch('screening_api.lib.messaging.publishers.uuid')
    @mock.patch('kombu.messaging.Producer.publish')
    def test_post_filter_severities(
            self, m_publish, m_uuid, m_get_origin, test_client, factory,
            application):
        frozen_uuid = '12345678-1234-1234-1234-1234567890ab'
        frozen_origin = 'origin@host'
        m_publish.return_value = None
        m_uuid.return_value = frozen_uuid
        m_get_origin.return_value = frozen_origin
        account_id = 54321
        imo_id = 12345678
        ship = factory.create_ship(imo_id=imo_id, type='Bulk Carrier')
        screening_1 = factory.create_screening(
            account_id=account_id, ship=ship, severity=Severity.UNKNOWN,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        screening_2 = factory.create_screening(
            account_id=account_id, ship=ship, severity=Severity.OK,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        factory.create_screening(
            account_id=account_id, ship=ship, severity=Severity.WARNING,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        severities = 'UNKNOWN,OK'
        params = {'severities': severities}

        env, resp = test_client.post(
            self.uri, query_string=params, as_tuple=True)

        assert resp.status_code == 202
        assert not resp.data

        assert m_publish.call_count == 2
        calls = [
            mock.call(
                json.dumps(
                    [[screening.id], {}, None]
                ),
                content_encoding='utf-8', content_type='application/json',
                correlation_id=frozen_uuid,
                headers={
                    'id': frozen_uuid,
                    'lang': CeleryTaskPublisher.lang,
                    'task': ScreeningsScreenSubscriber.name,
                    'argsrepr': str((screening.id,)),
                    'kwargsrepr': str({}),
                    'origin': frozen_origin,
                }
            )
            for screening in [screening_1, screening_2]
        ]
        m_publish.assert_has_calls(calls, any_order=True)

    @freeze_time("2001-09-11 07:59:00")
    @mock.patch('screening_api.lib.messaging.publishers.get_origin')
    @mock.patch('screening_api.lib.messaging.publishers.uuid')
    @mock.patch('kombu.messaging.Producer.publish')
    def test_post_filter_severity_change(
            self, m_publish, m_uuid, m_get_origin, test_client, factory,
            application):
        frozen_uuid = '12345678-1234-1234-1234-1234567890ab'
        frozen_origin = 'origin@host'
        m_publish.return_value = None
        m_uuid.return_value = frozen_uuid
        m_get_origin.return_value = frozen_origin
        account_id = 54321
        imo_id = 12345678
        ship = factory.create_ship(imo_id=imo_id, type='Bulk Carrier')
        screening_1 = factory.create_screening(
            account_id=account_id, ship=ship,
            severity_change=SeverityChange.INCREASED,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        screening_2 = factory.create_screening(
            account_id=account_id, ship=ship,
            severity_change=SeverityChange.INCREASED,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        factory.create_screening(
            account_id=account_id, ship=ship,
            severity_change=SeverityChange.NOCHANGE,
            previous_severity_date='2001-09-11T07:59:00Z',
        )
        severity_change = 'INCREASED'
        params = {'severity_change': severity_change}

        env, resp = test_client.post(
            self.uri, query_string=params, as_tuple=True)

        assert resp.status_code == 202
        assert not resp.data

        assert m_publish.call_count == 2
        calls = [
            mock.call(
                json.dumps(
                    [[screening.id], {}, None]
                ),
                content_encoding='utf-8', content_type='application/json',
                correlation_id=frozen_uuid,
                headers={
                    'id': frozen_uuid,
                    'lang': CeleryTaskPublisher.lang,
                    'task': ScreeningsScreenSubscriber.name,
                    'argsrepr': str((screening.id,)),
                    'kwargsrepr': str({}),
                    'origin': frozen_origin,
                }
            )
            for screening in [screening_1, screening_2]
        ]
        m_publish.assert_has_calls(calls, any_order=True)
