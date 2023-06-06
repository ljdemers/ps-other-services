from unittest.mock import patch
import responses
from contextlib import ContextDecorator

from requests.exceptions import (
    Timeout,
    ConnectionError as RequestsConnectionError
)

from api_clients.base_client import (
    ApiClient,
    ResponseDict,
    ApiKeyAuthMixin,
    ApiKeyHeadersAuthMixin,
    BasicAuthMixin,
)


class M(ContextDecorator):
    def __init__(self, *response_list):
        super().__init__()
        self.response_list = response_list
        self.resp = responses.RequestsMock(assert_all_requests_are_fired=False)

    def __enter__(self):
        for response in self.response_list:
            multi = getattr(response, 'multi', 1)
            for i in range(multi):
                self.resp.add(response)

        self.resp.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        success = type is None
        self.resp.stop(allow_assert=success)
        self.resp.reset()
        return success


class ServiceResponse(responses.Response):
    method = responses.GET
    status = 200
    url = ''
    response_data = {}
    multi = 1
    body = None

    def __init__(self, method=None, url=None, body='', json=None, status=None,
                 headers=None, stream=False, content_type=responses.UNSET,
                 **kwargs):
        method = method or self.method
        url = url or self.url
        body = body or self.body
        status = status or self.status
        if not body:
            json = json or self.response_data
        headers = headers or self.headers
        self.multi = kwargs.pop('multi', self.multi)

        super().__init__(method, url, body, json, status,
                         headers, stream, content_type, **kwargs)


class TestApiClient:

    @patch('api_clients.base_client.requests.Session', spec=True)
    def test_authenticate_username_api_key_params(self, mock_session):
        expected_call_args = {
            'method': 'get',
            'verify': True,
            'url': 'localhost/endpoint/',
            'auth': None,
            'headers': {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            },
            'params': {
                'user_name': 'user',
                'password': 'key',
            },
        }

        class TApiClient(ApiKeyAuthMixin, ApiClient):
            pass

        client = TApiClient(host='localhost', username='user', key='key')

        client.get(url='/endpoint/')

        assert client.session.request.call_args[1] == expected_call_args

    @patch('api_clients.base_client.requests.Session', spec=True)
    def test_authenticate_auth_header(self, mock_session):
        expected_call_args = {
            'method': 'get',
            'verify': True,
            'url': 'localhost/endpoint/',
            'auth': None,
            'headers': {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'user_name': 'user',
                'password': 'key',
            },
            'params': {},
        }

        class TApiClient(ApiKeyHeadersAuthMixin, ApiClient):
            pass

        client = TApiClient(host='localhost', username='user', key='key')

        client.get(url='/endpoint/')

        assert client.session.request.call_args[1] == expected_call_args

    @patch('api_clients.base_client.requests.Session', spec=True)
    def test_authenticate_different_field_names(self, mock_session):
        expected_call_args = {
            'method': 'get',
            'verify': True,
            'url': 'localhost/endpoint/',
            'auth': None,
            'headers': {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'test_username': 'user',
                'test_password': 'key',
            },
            'params': {},
        }

        class TApiClient(ApiKeyHeadersAuthMixin, ApiClient):
            @classmethod
            def get_authentication_names(cls):
                return 'test_username', 'test_password'

        client = TApiClient(host='localhost', username='user', key='key')

        client.get(url='/endpoint/')

        assert client.session.request.call_args[1] == expected_call_args

    def test_check_error_response(self):
        with M(ServiceResponse(status=500, url='http://localhost/endpoint/')):
            client = ApiClient(host='http://localhost',
                               username='user', key='key')
            resp = client.get(url='/endpoint/')

            assert resp.error['message'] == "ApiClient request failed with " \
                                            "status 500 headers: " \
                                            "{'Content-Type': " \
                                            "'application/json'}"

    def test_authenticate_basic_auth(self):
        expected_authorisation = 'Basic YWRtaW46c2VjcmV0'

        class TApiClient(BasicAuthMixin, ApiClient):
            pass

        client = TApiClient(host='http://localhost',
                            username='admin', key='secret')

        class LocalhostEndpoint(ServiceResponse):
            url = 'http://localhost/endpoint/'
            response_data = {}

        with M(LocalhostEndpoint()) as m:
            client.get(url='/endpoint/')

            assert m.resp.calls[0].request.headers['authorization'] == \
                expected_authorisation

    def test_response_dict(self):
        response = ResponseDict({'a': 1, 'b': '2'}, _meta={'count': 100})
        assert response.a == 1
        assert response.b == '2'
        assert response.meta.get('count') == 100

    @patch('api_clients.base_client.requests.Session', spec=True)
    def test_request_handles_timeout(self, mock_session):
        client = ApiClient(host='http://localhost', username='admin')
        client.session.request.side_effect = Timeout('time is up')

        resp = client._request('get', '/docs')

        assert resp.error['message'] == 'ApiClient request failed with ' \
                                        'Exception time is up'

    @patch('api_clients.base_client.requests.Session', spec=True)
    def test_request_handles_connection_error(self, mock_session):
        client = ApiClient(host='http://localhost', username='admin')
        client.session.request.side_effect = RequestsConnectionError(
            'cannot connect'
        )

        resp = client._request('get', '/docs')
        assert resp.error['message'] == 'ApiClient request failed with ' \
                                        'Exception cannot connect'
