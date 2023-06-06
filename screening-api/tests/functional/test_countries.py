import pytest


class TestCountriesViewOptions:

    uri = '/v1/countries'

    def test_allowed_methods(self, test_client):
        env, resp = test_client.options(self.uri, as_tuple=True)

        assert resp.status_code == 200
        assert set(resp.allow) == set(['OPTIONS', 'GET', 'HEAD'])
        assert resp.headers['Access-Control-Allow-Origin'] == '*'


@pytest.mark.usefixtures('authenticated')
class TestCountriesViewGet:

    uri = '/v1/countries'

    def test_unauthenticated(self, test_client):
        test_client.environ_base['HTTP_AUTHORIZATION'] = ''

        env, resp = test_client.get(self.uri, as_tuple=True)

        assert resp.status_code == 401

    def test_valid(self, test_client, factory):
        ship_1 = factory.create_ship(
            imo_id=12345, country_id='PL', country_name='Poland')
        ship_2 = factory.create_ship(
            imo_id=12346, country_id='UK', country_name='United Kingdom')
        ship_3 = factory.create_ship(
            imo_id=12347, country_id='US', country_name='US and A')
        factory.create_ship(
            imo_id=12348, country_id='US', country_name='US and A')

        env, resp = test_client.get(self.uri, as_tuple=True)

        assert resp.status_code == 200
        ships = [ship_1, ship_2, ship_3]
        assert resp.json == {
            'data': [[ship.country_id, ship.country_name] for ship in ships],
            'meta': {
                'count': 3,
            },
            'links': {},
        }

    def test_no_country_id(self, test_client, factory):
        ship_1 = factory.create_ship(
            imo_id=12345, country_id=None, country_name='Poland')
        ship_2 = factory.create_ship(
            imo_id=12346, country_id=None, country_name='US and A')
        ship_3 = factory.create_ship(
            imo_id=12347, country_id=None, country_name='United Kingdom')

        env, resp = test_client.get(self.uri, as_tuple=True)

        assert resp.status_code == 200
        ships = [ship_1, ship_2, ship_3]
        assert resp.json == {
            'data': [[ship.country_id, ship.country_name] for ship in ships],
            'meta': {
                'count': 3,
            },
            'links': {},
        }

    def test_search_by_country_id(self, test_client, factory):
        factory.create_ship(
            imo_id=12345, country_id='PL', country_name='Poland')
        ship_2 = factory.create_ship(
            imo_id=12346, country_id='UK', country_name='United Kingdom')
        ship_3 = factory.create_ship(
            imo_id=12347, country_id='US', country_name='US and A')
        factory.create_ship(
            imo_id=12348, country_id='US', country_name='US and A')

        search = 'U'
        params = {'search': search}
        env, resp = test_client.get(
            self.uri, query_string=params, as_tuple=True)

        assert resp.status_code == 200
        ships = [ship_2, ship_3]
        assert resp.json == {
            'data': [[ship.country_id, ship.country_name] for ship in ships],
            'meta': {
                'count': len(ships),
            },
            'links': {},
        }

    def test_search_by_country_name(self, test_client, factory):
        ship_1 = factory.create_ship(
            imo_id=12345, country_id='PL', country_name='Poland')
        factory.create_ship(
            imo_id=12346, country_id='UK', country_name='United Kingdom')
        ship_3 = factory.create_ship(
            imo_id=12347, country_id='US', country_name='US and A')
        factory.create_ship(
            imo_id=12348, country_id='US', country_name='US and A')

        search = 'and'
        params = {'search': search}
        env, resp = test_client.get(
            self.uri, query_string=params, as_tuple=True)

        assert resp.status_code == 200
        ships = [ship_1, ship_3]
        assert resp.json == {
            'data': [[ship.country_id, ship.country_name] for ship in ships],
            'meta': {
                'count': len(ships),
            },
            'links': {},
        }
