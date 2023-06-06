import logging
import sys
import time
from collections.abc import Mapping
from functools import wraps
from json.decoder import JSONDecodeError
from typing import (
    Any, Callable, Dict, Hashable, Iterator, Optional, Tuple
)
from urllib.parse import urlencode

import requests
from requests.exceptions import (
    Timeout,
    ConnectionError as RequestsConnectionError
)

logger = logging.getLogger(__name__)


def handle_connection_errors(f: Callable) -> Callable:
    """
    Catch connection and timeout errors in wrapped function.

    Args:
        f (Callable): The Api client method to be wrapped.

    Returns:
        (Callable): The wrapped client method.
    """
    @wraps(f)
    def wrapper(*args, **kwargs) -> ResponseDict:  # pylint: disable=E0601
        try:
            return f(*args, **kwargs)
        except (RequestsConnectionError, Timeout) as err:
            url = kwargs.get('url') or args[1]
            logger.exception('Calling %s connection error.', url)
            calling_class = args[0]
            error = {
                'message': f'{calling_class.__class__.__name__} '
                           f'request failed '
                           f'with Exception {err}',
                'details': f'url: {url}',
            }
            return ResponseDict(_error=error)
    return wrapper


class ObjectDict(Mapping):
    """
    Makes Dict keys accessible like Object but it still
    keeps the dict properties
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._storage = dict(*args, **kwargs)

    def __getitem__(self, key: Hashable) -> Any:
        return self._storage[key]

    def __setitem__(self, key: Hashable, value: Any) -> None:
        self._storage[key] = value

    def __getattr__(self, name: Hashable) -> Any:
        try:
            return self._storage[name]
        except KeyError:
            raise AttributeError(name)

    def __iter__(self) -> Iterator:
        return iter(self._storage)

    def __len__(self) -> int:
        return len(self._storage)

    def __dict__(self) -> Dict:  # type: ignore
        return self._storage

    def update(self, other: Dict) -> Dict:
        return self._storage.update(other)  # type: ignore

    def pop(self, k: Hashable, default: Any) -> Any:
        return self._storage.pop(k, default)

    def __str__(self) -> str:
        return f'{self._storage}'

    def __sizeof__(self):
        return sys.getsizeof(self._storage)


class ResponseDict(ObjectDict):
    """
    Response Dict from ObjectDict
    """
    def __init__(
        self,
        *args: Any,
        _error: Dict = None,
        _meta: Dict = None,
        **kwargs: Any
    ) -> None:
        if _error is None:
            self._error_dict: Dict = {}
        else:
            self._error_dict = _error

        if _meta is None:
            self._meta_dict: Dict = {}
        else:
            self._meta_dict = _meta
        super().__init__(*args, **kwargs)

    @property
    def raw_data(self) -> Dict:
        return self._storage

    @property
    def error(self) -> Dict:
        return self._error_dict

    def has_error(self) -> bool:
        return bool(self.error)

    @property
    def meta(self) -> Dict:
        return self._meta_dict

    def __str__(self) -> str:
        return f'{self._storage} - meta: {self.meta}, error: {self.error}'


class Auth:
    auth: Optional[Tuple]
    username: str
    key: Optional[str]
    default_params: Dict
    headers: Dict

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)  # type: ignore
        self.authenticate()

    def authenticate(self) -> None:
        raise NotImplementedError

    @classmethod
    def get_authentication_names(cls) -> Tuple:
        # FIXME: this should be a `staticmethod` and don't use `self` argument.
        return 'user_name', 'password'


class BasicAuthMixin(Auth):
    def authenticate(self) -> None:
        # FIXME: would be nice to define `self.auth` as an `Auth` attribute.
        # Make this thing more robust.
        self.auth = (self.username, self.key)


class ApiKeyAuthMixin(Auth):
    def authenticate(self) -> None:
        username_name, api_key_name = self.get_authentication_names()
        self.default_params.update(
            {username_name: self.username, api_key_name: self.key}
        )


class URLParamsAuthMixin(Auth):
    def authenticate(self):
        username_name, api_key_name = self.get_authentication_names()
        self.default_params.update(
            {username_name: self.username, api_key_name: self.key}
        )


class ApiKeyHeadersAuthMixin(Auth):
    def authenticate(self) -> None:
        username_name, api_key_name = self.get_authentication_names()

        self.headers[username_name] = self.username
        self.headers[api_key_name] = self.key


class ApiClient:
    """Generic API client for JSON APIs"""
    ssl_verify = True
    auth: Optional[Tuple] = None
    request_timeout: Optional[int] = None

    def __init__(
        self,
        host: str,
        *args: Any,
        username: Optional[str] = None,
        key: Optional[str] = None,
        session: requests.Session = None,
        **kwargs: Any
    ) -> None:
        self.host = host
        self.username = username
        self.key = key
        self.default_params: Dict = {}
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        self.session = session or requests.Session()

    @handle_connection_errors
    def _request(self, method: str, url: str, **kwargs: Any) -> ResponseDict:
        full_url = f'{self.host}{url}'
        kwr = dict(url=full_url, headers=self.headers, **kwargs)
        if self.request_timeout:
            kwr['timeout'] = self.request_timeout

        response = self.session.request(
            method=method,
            verify=self.ssl_verify,
            auth=self.auth,
            **kwr
        )

        return self.create_response_dict(
            response, details={'full_url': full_url, 'kwr': kwr}
        )

    #
    # generic HTTP methods functions, if there is a payload accept ``data``
    # and pass it as JSON.
    #

    def get(self, url: str, params: Dict = None) -> ResponseDict:
        if params is None:
            params = {}
        req_params = self.default_params.copy()
        req_params.update(params)

        return self._request(method='get', url=url, params=req_params)

    def delete(
        self, url: str, data: Dict = None, params: Dict = None
    ) -> ResponseDict:
        if data is not None and not isinstance(data, dict):
            raise ValueError('Data for DELETE must be a dict.')

        if params:
            # if url parameters are passed
            url = f'{url}?{urlencode(params)}'

        return self._request(method='delete', url=url, json=data)

    def post(
            self, url: str, data: Dict = None, params: Dict = None
    ) -> ResponseDict:
        if data is not None and not isinstance(data, dict):
            raise ValueError('Data for POST must be a dict.')

        if params:
            # if url parameters are passed
            url = f'{url}?{urlencode(params)}'

        return self._request(method='post', url=url, json=data)

    def put(
        self, url: str, data: Dict = None, params: Dict = None
    ) -> ResponseDict:
        if data is not None and not isinstance(data, dict):
            raise ValueError('Data for PUT must be a dict.')

        if params:
            # if url parameters are passed
            url = f'{url}?{urlencode(params)}'

        return self._request(method='put', url=url, json=data)

    def create_response_dict(
        self, response: requests.Response, details: Dict = None
    ) -> ResponseDict:
        """
        Create a `ResponseDict` object from a `requests.Response` object.

        Errors are set on the `ResponseDict` based on non-20X response codes.
        An empty `ResponseDict` is returned if the response is not valid json.

        Args:
            response (requests.Response): The raw response object.
            details (dict, optional): Additional context for potential errors.

        Returns:
            (ResponseDict): The response packaged up in our internal
                representation.
        """
        if response.status_code in (200, 201, 202, 203, 204):
            try:
                resp = response.json()
                if isinstance(resp, list):
                    resp = {'response': resp}
                if resp is None:
                    resp = {}
                meta = resp.pop('meta', None)
                return ResponseDict(resp, _meta=meta)
            except JSONDecodeError:
                return ResponseDict({})
        else:
            error = {
                'message': f'{self.__class__.__name__} request failed with '
                           f'status {response.status_code} '
                           f'headers: {response.headers}',
                           f'text: {response.text}'
                'details': details,
            }
            return ResponseDict(_error=error)


def retry(func: Callable, ret_count: int = 0, retry_sleep: int = 1) \
        -> Callable:
    @wraps(func)
    def wrapped(*args: Any, **kwargs: Any) -> Callable:
        nonlocal ret_count
        res = func(*args, **kwargs)
        while res.error and ret_count > 0:
            logger.error(
                'Retrying %s because of: %s', func.__name__, res.error)
            time.sleep(retry_sleep)
            ret_count = ret_count - 1
            res = func(*args, **kwargs)

        return res
    return wrapped
