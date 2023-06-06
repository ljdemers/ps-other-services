import pytest
from freezegun import freeze_time

from screening_api.screenings.enums import Severity


class TestScreeningsHistoryViewOptions:

    @pytest.fixture
    def screening(self, factory):
        account_id = 654321
        imo_id = 654321
        ship_1 = factory.create_ship(imo_id=imo_id, country_id='PL')
        return factory.create_screening(
            account_id=account_id, ship=ship_1, severity=Severity.UNKNOWN)

    def get_uri(self, screening_id):
        return '/v1/screenings/{0}/history'.format(screening_id)

    def test_allowed_methods(self, test_client, screening):
        env, resp = test_client.options(
            self.get_uri(screening.id), as_tuple=True)

        assert resp.status_code == 200
        assert set(resp.allow) == set(['OPTIONS', 'GET', 'HEAD'])
        assert resp.headers['Access-Control-Allow-Origin'] == '*'


@pytest.mark.usefixtures('authenticated')
class TestScreeningsHistoryViewGet:

    @pytest.fixture
    def screening(self, factory):
        account_id = 54321
        imo_id = 654321
        ship_1 = factory.create_ship(imo_id=imo_id, country_id='PL')
        return factory.create_screening(
            account_id=account_id, ship=ship_1, severity=Severity.UNKNOWN)

    def get_uri(self, screening_id):
        return '/v1/screenings/{0}/history'.format(screening_id)

    def test_unauthenticated(self, test_client, screening):
        test_client.environ_base['HTTP_AUTHORIZATION'] = ''

        env, resp = test_client.get(self.get_uri(screening.id), as_tuple=True)

        assert resp.status_code == 401

    def test_screening_not_found(self, test_client, screening):
        screening_id = 0
        env, resp = test_client.get(self.get_uri(screening_id), as_tuple=True)

        assert resp.status_code == 404

    @freeze_time("2001-09-11 07:59:00")
    def test_valid(self, test_client, factory, screening):
        history_1 = factory.create_screenings_history(
            screening=screening, severity_date="2001-09-11 07:59:00")
        history_2 = factory.create_screenings_history(
            screening=screening, severity_date="2001-09-11 07:59:00")
        history_3 = factory.create_screenings_history(
            screening=screening, severity_date="2001-09-11 07:59:00")
        history_4 = factory.create_screenings_history(
            screening=screening, severity_date="2001-09-11 07:59:00")

        env, resp = test_client.get(self.get_uri(screening.id), as_tuple=True)

        assert resp.status_code == 200
        expected_data = [
            {
                'id': history.id,
                'created': '2001-09-11T07:59:00Z',
                'updated': '2001-09-11T07:59:00Z',
                'severity_date': '2001-09-11T07:59:00Z',
                'screening_id': history.screening_id,
                'severity': history.severity.name,
                'company_sanctions_severity':
                    history.company_sanctions_severity.name,
                'ship_sanctions_severity':
                    history.ship_sanctions_severity.name,
                'country_sanctions_severity':
                    history.country_sanctions_severity.name,
                'ship_inspections_severity':
                    history.ship_inspections_severity.name,
                'ship_movements_severity':
                    history.ship_movements_severity.name,
            }
            for history in [
                history_4, history_3, history_2, history_1,
            ]
        ]
        assert resp.json == {
            "data": expected_data,
            "meta": {
                "count": len(expected_data),
            },
            "links": {
                'first': (
                    'http://api/v1/screenings/{0}/history?'
                    'page=1'.format(screening.id)
                ),
                'last': (
                    'http://api/v1/screenings/{0}/history?'
                    'page=1'.format(screening.id)
                ),
            },
        }

    @pytest.mark.parametrize('offset', [0, 1, 2, 3])
    @freeze_time("2001-09-11 07:59:00")
    def test_offset(self, test_client, factory, screening, offset):
        history_1 = factory.create_screenings_history(
            screening=screening, severity_date="2001-09-11 07:59:00")
        history_2 = factory.create_screenings_history(
            screening=screening, severity_date="2001-09-11 07:59:00")
        history_3 = factory.create_screenings_history(
            screening=screening, severity_date="2001-09-11 07:59:00")
        history_4 = factory.create_screenings_history(
            screening=screening, severity_date="2001-09-11 07:59:00")
        params = {'offset': offset}

        env, resp = test_client.get(
            self.get_uri(screening.id), query_string=params, as_tuple=True)

        assert resp.status_code == 200
        history_list = [history_4, history_3, history_2, history_1][offset:]
        expected_data = [
            {
                'id': history.id,
                'created': '2001-09-11T07:59:00Z',
                'updated': '2001-09-11T07:59:00Z',
                'severity_date': '2001-09-11T07:59:00Z',
                'screening_id': history.screening_id,
                'severity': history.severity.name,
                'company_sanctions_severity':
                    history.company_sanctions_severity.name,
                'ship_sanctions_severity':
                    history.ship_sanctions_severity.name,
                'country_sanctions_severity':
                    history.country_sanctions_severity.name,
                'ship_inspections_severity':
                    history.ship_inspections_severity.name,
                'ship_movements_severity':
                    history.ship_movements_severity.name,
            }
            for history in history_list
        ]
        assert resp.json == {
            "data": expected_data,
            "meta": {
                "count": len(expected_data),
            },
            "links": {
                'first': (
                    'http://api/v1/screenings/{0}/history?'
                    'offset={1}&page=1'.format(screening.id, offset)
                ),
                'last': (
                    'http://api/v1/screenings/{0}/history?'
                    'offset={1}&page=1'.format(screening.id, offset)
                ),
            },
        }
