import pytest


class TestCountriesViewOptions:

    uri = '/v1/ship_types'

    def test_allowed_methods(self, test_client):
        env, resp = test_client.options(self.uri, as_tuple=True)

        assert resp.status_code == 200
        assert set(resp.allow) == set(['OPTIONS', 'GET', 'HEAD'])
        assert resp.headers['Access-Control-Allow-Origin'] == '*'


@pytest.mark.usefixtures('authenticated')
class TestCountriesViewGet:

    uri = '/v1/ship_types'

    def test_unauthenticated(self, test_client):
        test_client.environ_base['HTTP_AUTHORIZATION'] = ''

        env, resp = test_client.get(self.uri, as_tuple=True)

        assert resp.status_code == 401

    def test_valid(self, test_client, factory):
        ship_1 = factory.create_ship(
            imo_id=12345, country_id='PL', type='Bulk Carrier')
        ship_2 = factory.create_ship(
            imo_id=12346, country_id='UK', type='Crude Oil Tanker')
        factory.create_ship(
            imo_id=12347, country_id='US', type='Crude Oil Tanker')

        env, resp = test_client.get(self.uri, as_tuple=True)

        assert resp.status_code == 200
        ships = [ship_1, ship_2]
        assert resp.json == {
            'data': [ship.type for ship in ships],
            'meta': {
                'count': len(ships),
            },
            'links': {},
        }

    def test_search(self, test_client, factory):
        factory.create_ship(
            imo_id=12345, country_id='PL', type='Bulk Carrier')
        ship_2 = factory.create_ship(
            imo_id=12346, country_id='UK', type='Crude Oil Tanker')
        ship_3 = factory.create_ship(
            imo_id=12347, country_id='US', type='Crude Oil Container')

        search = 'Oil'
        params = {'search': search}
        env, resp = test_client.get(
            self.uri, query_string=params, as_tuple=True)

        assert resp.status_code == 200
        ships = [ship_3, ship_2]
        assert resp.json == {
            'data': [ship.type for ship in ships],
            'meta': {
                'count': len(ships),
            },
            'links': {},
        }
