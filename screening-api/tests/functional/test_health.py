from datetime import datetime

from freezegun import freeze_time

from screening_api import __name__, __version__


class TestLivenessViewOptions:

    uri = '/healthz'

    def test_allowed_methods(self, test_client):
        env, resp = test_client.options(self.uri, as_tuple=True)

        assert resp.status_code == 200
        assert set(resp.allow) == set(['OPTIONS', 'GET', 'HEAD'])


class TestLivenessViewGet:

    uri = '/healthz'

    def test_healthy(self, test_client):
        env, resp = test_client.get(self.uri, as_tuple=True)

        assert resp.status_code == 204


class TestReadinessViewOptions:

    uri = '/health'

    def test_allowed_methods(self, test_client):
        env, resp = test_client.options(self.uri, as_tuple=True)

        assert resp.status_code == 200
        assert set(resp.allow) == set(['OPTIONS', 'GET', 'HEAD'])


class TestReadinessViewGet:

    uri = '/health'

    @freeze_time("2001-09-11 07:59:00")
    def test_unhealthy(self, test_client):
        env, resp = test_client.get(self.uri, as_tuple=True)

        assert resp.status_code == 503
        assert resp.json == {
            "name": __name__,
            'version': __version__,
            'services': [
                {
                    'errors': [],
                    'notes': {
                        'drivername': 'postgresql+psycopg2',
                    },
                    'service_type': 'database',
                    'status': 'PASSING',
                },
                {
                    'errors': [],
                    'notes': {
                        'transport': 'memory',
                    },
                    'service_type': 'broker',
                    'status': 'PASSING',
                },
                {
                    'errors': [],
                    'notes': {
                        'context_missing': 'RUNTIME_ERROR',
                        'daemon_address': '127.0.0.1:2000',
                        'service': None,
                    },
                    'service_type': 'xray',
                    'status': 'DISABLED',
                },
                {
                    'errors': ['No heartbeat timestamp'],
                    'notes': {},
                    'service_type': 'beat',
                    'status': 'FAILING',
                }
            ]
        }

    @freeze_time("2001-09-11 07:59:00")
    def test_healthy(self, test_client, heartbeat_cache_region):
        heartbeat = {
            'timestamp': datetime(2001, 9, 11, 7, 59, 0),
        }
        heartbeat_cache_region.put('heartbeat', heartbeat)

        env, resp = test_client.get(self.uri, as_tuple=True)

        assert resp.status_code == 200
        assert resp.json == {
            "name": __name__,
            'version': __version__,
            'services': [
                {
                    'errors': [],
                    'notes': {
                        'drivername': 'postgresql+psycopg2',
                    },
                    'service_type': 'database',
                    'status': 'PASSING',
                },
                {
                    'errors': [],
                    'notes': {
                        'transport': 'memory',
                    },
                    'service_type': 'broker',
                    'status': 'PASSING',
                },
                {
                    'errors': [],
                    'notes': {
                        'context_missing': 'RUNTIME_ERROR',
                        'daemon_address': '127.0.0.1:2000',
                        'service': None,
                    },
                    'service_type': 'xray',
                    'status': 'DISABLED',
                },
                {
                    'errors': [],
                    'notes': {
                        'timestamp': '2001-09-11T07:59:00Z',
                    },
                    'service_type': 'beat',
                    'status': 'PASSING',
                }
            ]
        }
