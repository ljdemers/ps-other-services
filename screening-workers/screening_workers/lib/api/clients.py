from time import time
from urllib.parse import urljoin
import requests

from screening_workers.lib.utils import json_logger


class Client(object):

    def __init__(
            self, base_uri, verify=False, log_level='INFO', encoding=None):
        self.base_uri = base_uri
        self.logger = json_logger(__name__, level=log_level)
        self.verify = verify
        self.encoding = encoding
        self._session = None
        self._auth = None
        self._headers = {}

    def set_basic_auth(self, user, password):
        self.session.auth = (user, password)
        self._auth = (user, password)

    def set_headers(self, headers):
        self.session.headers.update(headers)
        self._headers.update(headers)

    @property
    def session(self):
        if self._session is None:
            self._session = requests.Session()
        return self._session

    def log_request(self, request):
        if isinstance(request, str):
            self.logger.debug('GET %s' % request)
        else:
            self.logger.debug('%s %s' % (request.method, request.url))
            self.logger.debug(Headers=request.headers)
            self.logger.debug(Params=request.params)
            self.logger.debug(Data=request.data)
            self.logger.debug(Auth=request.auth)

    def log_response(self, response):
        self.logger.debug(Response=response.text)

    def fetch(self, request, params=None):
        if isinstance(request, str):
            joined = urljoin(self.base_uri, request)
            self.log_request(joined)
            response = self.session.get(joined, params=params,
                                        verify=self.verify)
        elif isinstance(request, requests.Request):
            request.url = urljoin(self.base_uri, request.url)
            request.auth = self.session.auth
            headers = self._headers
            headers.update(request.headers)
            request.headers = headers
            self.log_request(request)
            prepared = request.prepare()
            response = self.session.send(prepared, verify=self.verify)
        else:
            raise TypeError(
                'Request should be an instance of request.Request or a string')

        if self.encoding is not None:
            response.encoding = self.encoding

        self.log_response(response)

        return response


class TastyPieClient(Client):

    def __init__(self, base_url, username='', api_key='', encoding=None):
        super(TastyPieClient, self). __init__(base_url, encoding=encoding)
        self.username = username
        self.api_key = api_key

    def get_auth_headers(self, nonce=None):
        if not nonce:
            nonce = int(time())

        return {
            'Authorization': 'ApiKey {username}:{api_key}'.format(
                username=self.username,
                api_key=self.api_key
            ),
            'X-Authentication-Nonce': str(nonce),
        }

    def fetch(self, request, params=None):
        auth_headers = self.get_auth_headers()
        self.set_headers(auth_headers)
        return super(TastyPieClient, self).fetch(request, params)
