import json
import requests

from screening_workers.lib.utils import json_logger


class Collection(object):

    model = NotImplemented
    url = NotImplemented

    def __init__(self, client, log_level='INFO'):
        self.client = client
        self.logger = json_logger(__name__, level=log_level)

    def decode(self, data, many=False):
        if many:
            result = []
            for d in data:
                obj = self.model(**self.model.parse(d))
                obj._persisted = True
                result.append(obj)
            return result
        else:
            return self.model(**self.model.parse(data))

    def encode(self, obj):
        return obj.encode()

    def all(self):
        response = self.client.fetch(self.url)

        response.raise_for_status()

        data = response.json()

        return self.decode(data, many=True)

    def query(self, **kwargs):
        request = requests.Request(
            'GET', self.url,
            params=kwargs, headers={'Content-Type': 'application/json'}
        )
        response = self.client.fetch(request)

        response.raise_for_status()

        data = response.json()

        return self.decode(data, many=True)

    def get(self, id_):
        response = self.client.fetch(self._url(id_))

        response.raise_for_status()

        data = response.json()

        return self.decode(data)

    def _url(self, id_):
        url = self.url

        if callable(self.url):
            return self.url(id_)

        url, query = self.url.split('?')

        url = '{0}/{1}'.format(url, id_)

        if query is not None:
            return '{0}?{1}'.format(url, query)

        return url

    def _parse_url(self, url):
        parts = url.split('/')
        parts_len = len(parts)
        if parts_len:
            return parts[-1]
        else:
            return None

    def add(self, obj):
        if getattr(obj, '_persisted', False) is True:
            url = self._url(self._id(obj))
            method = 'PUT'
        else:
            url = getattr(obj, '_url', self.url)
            if callable(url):
                url = url()
            method = 'POST'

        data = self.encode(obj)

        request = requests.Request(
            method, url,
            data=json.dumps(data), headers={'Content-Type': 'application/json'}
        )

        response = self.client.fetch(request)

        response.raise_for_status()

        if len(response.content) > 0:
            data = response.json()

            try:
                obj.decode(data)
                obj._persisted = True
            except Exception:
                raise

            return obj
        else:
            try:
                url = response.headers.get('Location')
            except KeyError:
                return None
            id_ = self._parse_url(url)
            if id_ is not None:
                for name, field in obj._fields.items():
                    if field.options.get('primary', False):
                        setattr(obj, name, id_)
                        return obj
            return None

    def _id(self, obj):
        for name, field in obj._fields.items():
            if field.options.get('primary', False):
                return getattr(obj, name)
