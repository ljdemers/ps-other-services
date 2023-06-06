import importlib
import logging
import socket

import psutil
from django import db
from django.conf import settings
from django.conf.urls import url
from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist
from django.http import HttpResponse
from django.template import Context, loader
from tastypie.authentication import Authentication
from tastypie.authorization import Authorization
from tastypie.bundle import Bundle
from tastypie.exceptions import ImmediateHttpResponse
from tastypie.fields import CharField
from tastypie.http import HttpMethodNotAllowed
from tastypie.resources import Resource
from tastypie.serializers import Serializer
from tastypie.utils import trailing_slash


logger = logging.getLogger(__name__)


def convert_to_float(value):
    try:
        return None if value is None else float(value)
    except ValueError:
        return None


def convert_to_int(value):
    try:
        return None if value is None else int(value)
    except ValueError:
        return None


class DictObject(object):
    """
    **Moved into codebase from ``ps-restutils`` package.**

    Wrapper for dicts returned by a non-ORM data source, enabling them to be
    treated like objects.

    :param key: The unique key identifier for this resource.
    :param initial: Attribute values for this resource.
     :type initial: dict
    """
    def __init__(self, key=None, initial=None):
        self.__dict__['pk'] = key
        self.__dict__['_data'] = initial or {}

    def __getattr__(self, name):
        return self._data.get(name, None)

    def __setattr__(self, name, value):
        self.__dict__['_data'][name] = value

    def __delattr__(self, name):
        self._data.pop(name, None)

    def to_dict(self):
        """Returns a dict representation of the original object data."""
        return self._data

    def __str__(self):
        return 'DictObject<%s>' % [self.pk]

    def __repr__(self):
        return 'DictObject<%s>' % [self.pk]


class LazyObjectList(object):
    """
    **Moved into codebase from ``ps-restutils`` package.**

    Lazily evaluate a list of keys, retrieving the actual objects only for the
    items which are of interest.

    :param get_object: Method for retrieving objects by key
    :param data: List of keys to be passed to ``get_object``.
    """
    #: Wrapper class for the retrieved resources.
    ItemClass = DictObject

    def __init__(self, get_object, data):
        self.get_object = get_object
        self.data = data

    def __getitem__(self, sl):
        if isinstance(sl, slice):
            return [
                self.ItemClass(key, self.get_object(key))
                for key in self.data[sl]
            ]
        key = self.data[sl]
        return self.ItemClass(key, self.get_object(key))

    def __len__(self):
        return len(self.data)

    def __iter__(self):
        for item in self.data:
            yield item

    def all(self):
        """Returns an iterable over the contained objects."""
        return self

    def count(self):
        """Returns the number of contained objects."""
        return len(self.data)


class TopResource(Resource):
    # pylint: disable=arguments-differ
    """
    **Moved into codebase from ``ps-restutils`` package.**

    Base class for resources that deal with attribute-value dictionaries as
    their underlying data.
    To use, set up your metaclass as follows::

      class Meta:
          detail_uri_name = '<primary key attribute name>'
          object_class = DictObject

    Then implement the ``get_object`` and ``get_object_list`` methods.
    """
    resource_uri = CharField(readonly=True, help_text='Resource URI')

    def get_object_list(self, request, **kwargs):
        """
        Returns a list of keys, with optional filtering applied. To be
        overridden by subclasses.

        :param request: The request object.
        :type request: HTTPRequest
        """
        raise NotImplementedError()

    def get_object(self, key):
        """
        Return a dictionary of attributes, using the names as keys. To be
        overridden by subclasses.
        """
        raise NotImplementedError()

    def detail_uri_kwargs(self, bundle_or_obj):
        """
        Given a ``Bundle`` or an object, returns the extra kwargs needed to
        generate a detail URI.
        """
        if isinstance(bundle_or_obj, Bundle):
            bundle_or_obj = bundle_or_obj.obj

        return {
            self._meta.detail_uri_name: getattr(
                bundle_or_obj, self._meta.detail_uri_name
            )
        }

    def get_key(self, **kwargs):
        """
        Returns the key value from the keywords. Used to find the primary key
        from URL parameters.
        This value will be passed to get_object for retrieval of the actual
        attribute dict.
        """
        return kwargs[self._meta.detail_uri_name]

    def obj_get_list(self, bundle=None, **kwargs):
        """
        Retrieves a list of keys and passes it on to the dispatch wrapped in a
        lazy-evaluating wrapper. This minimizes the necessary object retrieval.
        """
        data = list(self.get_object_list(bundle, **kwargs))
        return LazyObjectList(self.get_object, data)

    def obj_get(self, request=None, **kwargs):
        """
        Retrieve a single resource as a value dict, wrapping it as an object.
        """
        key = self.get_key(**kwargs)
        message = self.get_object(key)
        if not message:
            raise ObjectDoesNotExist()
        return DictObject(key, message)

    def rollback(self, bundles):
        """
        Given the list of bundles, delete all objects pertaining to those
        bundles.
        """
        pass

    def apply_filters(self, request, applicable_filters):
        ''' Called by the original get_object_list, which is overridden '''
        raise RuntimeError('Should not be called')

    def method_check(self, request, allowed=None):
        """ Provide a verbose error message """
        try:
            return super(TopResource, self).method_check(
                request, allowed=allowed
            )
        except ImmediateHttpResponse as err:
            err.response['content-type'] = 'application/json'
            err.response.content = \
                '{"error": {"code": 405, "message": "HTTP Method not allowed"}}'
            raise

    def _forbidden(self, bundle, **kwargs):
        """ Trap calls that should not be processed """
        response = HttpMethodNotAllowed()
        response['content-type'] = 'application/json'
        response.content = \
            '{"error": {"code": 405, "message": "HTTP Method not allowed"}}'

    def obj_create(self, bundle, **kwargs):
        """Creates a new object based on the provided data."""
        return self._forbidden(bundle, **kwargs)

    def obj_delete(self, bundle, **kwargs):
        """ Deletes a single object. """
        return self._forbidden(bundle, **kwargs)

    def obj_delete_list(self, bundle, **kwargs):
        """ Deletes an entire list of objects. """
        return self._forbidden(bundle, **kwargs)

    def obj_delete_list_for_update(self, bundle, **kwargs):
        """ Deletes an entire list of objects, specific to PUT list. """
        return self._forbidden(bundle, **kwargs)

    def obj_update(self, bundle, **kwargs):
        """
        Updates an existing object (or creates a new object) based on the
        provided data.
        """
        return self._forbidden(bundle, **kwargs)

    nested_resources = {}  # Override where necessary - see NestedResource

    def prepend_urls(self):
        """
        If the resource has nested child resources, this will insert the
        necessary urls to access them through the parent.
        """
        result = []
        for related_attr, related_resource in self.nested_resources.items():
            key1 = self._meta.detail_uri_name
            key2 = related_resource._meta.detail_uri_name
            result.extend(
                [
                    url(
                        r'^%s/(?P<%s>\w[\w-]*)/(?P<resource_name>%s)%s$' % (
                            self._meta.resource_name,
                            key1,
                            related_attr,
                            trailing_slash()
                        ),
                        related_resource.wrap_view('dispatch_list'),
                        name='api_dispatch_list'
                    ),
                    url(
                        r'^%s/(?P<%s>\w[\w-]*)/(?P<resource_name>%s)/'
                        r'(?P<%s>\w[\w-]*)%s$' % (
                            self._meta.resource_name,
                            key1,
                            related_attr,
                            key2,
                            trailing_slash()
                        ),
                        related_resource.wrap_view('dispatch_detail'),
                        name='api_dispatch_detail'
                    )
                ]
            )

            # Modify the nested resource metaclass to set up the necessary
            # relations.
            related_resource._meta.api_name = self._meta.api_name
            related_resource._meta.resource_name = related_attr
            related_resource._meta.parent_uri_name = key1

        return result


class SystemSerializer(Serializer):
    """
    **Moved into codebase from ``ps-restutils`` package.**
    """
    formats = ['json', 'html', 'basic']

    content_types = {'json': 'application/json',
                     'html': 'text/html',
                     'basic': 'text/plain'}

    def to_json(self, data, options=None):
        """to_json"""
        logger.debug(data)
        if hasattr(data, 'data') and '_template_name' in data.data:
            del data.data['_template_name']
        return super(SystemSerializer, self).to_json(data, options=options)

    def to_basic(self, data, options=None):
        """to_basic"""
        options = options or {}
        data = self.to_simple(data, options)
        return '%s\n%s' % (data['version'], data['overall_status'])

    def to_html(self, data, options=None):
        """to_html"""
        options = options or {}
        data = self.to_simple(data, options)
        if '_template_name' not in data:
            return 'Sorry, not implemented yet. Please append "?format=json" ' \
                   'to your URL.'
        template = loader.get_template(data['_template_name'])
        return template.render(Context(data))


class SystemResource(Resource):
    # pylint: disable=abstract-method
    """System Resource"""
    class Meta:
        object_class = DictObject
        authorization = Authorization()
        authentication = Authentication()
        allowed_methods = []
        resource_name = 'system'
        serializer = SystemSerializer(formats=['json', 'html', 'basic'])
        extra_actions = [
            {
                'name': 'healthcheck',
                'http_method': 'GET',
                'resource_type': 'list',
                'summary': 'Endpoint that just checks that the API is able to '
                           'connect to its primary database',
                'fields': {},
                'response_class': 'healthcheck',
            },
            {
                'name': 'status',
                'http_method': 'GET',
                'resource_type': 'list',
                'summary': 'Endpoint for getting the service status of the api.'
                           ' i.e. if the api is encountering any issues',
                'fields': {},
                'response_class': 'status'
            },
            {
                'name': 'version',
                'http_method': 'GET',
                'resource_type': 'list',
                'summary': 'Endpoint for getting the version of the api',
                'fields': {},
                'response_class': 'version'
            },
        ]
        extra_models = {
            'status': {
                'properties': {
                    'environment': {
                        'type': 'string',
                        'description': 'The kind of environment the API is '
                                       'deployed to: test, production etc'
                    },
                    'overall_status': {
                        'type': 'string',
                        'description': 'The overall status of the API'
                    },
                    'product': {
                        'type': 'string',
                        'description': 'Name of the API'
                    },
                    'systems': {
                        'type': 'systems',
                        'description': 'Individual systems and their status'
                    },
                    'uptime': {
                        'type': 'string',
                        'description': 'Result of uptime command on the machine'
                    },
                    'version': {
                        'type': 'string',
                        'description': 'Current Version of the API in the form '
                                       'Major.Minor.Patch'
                    },
                },
                'id': 'status'
            },
            'systems': {
                'properties': {
                    'API': {
                        'type': 'string',
                        'description': 'Status of the API; OK/ERROR/WARNING'
                    },
                    'Database': {
                        'type': 'string',
                        'description': 'Status of the Database; '
                                       'OK/ERROR/WARNING'
                    },
                },
                'id': 'systems'
            },
            'components': {
                'properties': {
                    'name': {
                        'type': 'string',
                        'description': 'Component name as defined in settings'
                    },
                    'commit': {
                        'type': 'string',
                        'description': 'Git commit SHA'
                    },
                    'tag': {
                        'type': 'string',
                        'description': 'Git tag'
                    },
                },
                'id': 'components'
            },
            'version': {
                'properties': {
                    'commit': {
                        'type': 'string',
                        'description': 'Git commit SHA'
                    },
                    'description': {
                        'type': 'string',
                        'description': 'Description of this API'
                    },
                    'product': {
                        'type': 'string',
                        'description': 'Name of the API'
                    },
                    'tag': {
                        'type': 'string',
                        'description': 'Git tag'
                    },
                    'version': {
                        'type': 'string',
                        'description': 'Current Version of the API in the form '
                                       'Major.Minor.Patch'
                    },
                },
                'id': 'version'
            },
        }

    def prepend_urls(self):
        """prepend_url"""
        resource_name = self._meta.resource_name
        return [
            url(
                r'^(?P<resource_name>%s)/healthcheck%s$' % (
                    resource_name, trailing_slash()
                ),
                self.wrap_view('healthcheck'),
                name='api_healthcheck'
            ),
            url(
                r'^(?P<resource_name>%s)/status%s$' % (
                    resource_name, trailing_slash()
                ),
                self.wrap_view('status'),
                name='api_status'
            ),
            url(
                r'^(?P<resource_name>%s)/version%s$' % (
                    resource_name, trailing_slash()
                ),
                self.wrap_view('version'),
                name='api_version'
            ),
        ]

    def get_class_value(self, check=None):
        try:
            check_list = check.split('.')
            mod = '.'.join(check_list[0:-1])
            module = importlib.import_module(mod)
            func = getattr(module, check_list[-1])
            return func().value
        except (IndexError, ImportError):
            logger.error("can not import check class `%s`", check, exc_info=1)
            return "UNKNOWN"

    def get_system_status(self):
        systems_checks = getattr(settings, 'SYSTEM_STATUS', {})
        overall_status = 'OK'
        systems = {}
        for system, check in systems_checks.items():
            systems[system] = self.get_class_value(check)
            if systems[system] == 'OK':
                continue
            elif systems[system] == 'WARNING' and overall_status == 'OK':
                overall_status = 'WARNING'
            else:
                overall_status = 'ERROR'

        system_status = {
            '_template_name': 'system_status',
            'product': getattr(settings, 'PRODUCT', 'Unknown System'),
            'version': self.get_version(),
            'overall_status': overall_status,
            'systems': systems,
            'environment': str(socket.gethostname()),
        }
        return system_status

    def get_version(self):
        return getattr(settings, 'VERSION', 'MASTER')

    def healthcheck(self, request, **kwargs):
        # will raise OperationalError if unable to connect
        assert db.connection.cursor()
        return HttpResponse('OK')

    def status(self, request, **kwargs):
        self.method_check(request, allowed=['get'])
        self.throttle_check(request)
        system_status = self.get_system_status()
        bundle = self.build_bundle(data=system_status, request=request)
        bundle = self.alter_detail_data_to_serialize(request, bundle)
        return self.create_response(request, bundle)

    def version(self, request, **kwargs):
        self.method_check(request, allowed=['get'])
        self.throttle_check(request)

        data = {
            'version': self.get_version(),
            'product': getattr(settings, 'PRODUCT', 'PoleStar'),
            'description': getattr(settings, 'PRODUCT_DESCRIPTION', None),
        }

        bundle = self.build_bundle(data=data, request=request)
        bundle = self.alter_detail_data_to_serialize(request, bundle)
        return self.create_response(request, bundle)


class SystemCheck(object):
    """System Check Class."""
    def __init__(self):
        self.value = self.run()

    def run(self):
        """Run the check."""
        return "OK"


class ProcessCheck(SystemCheck):
    """Process Check Class."""
    process_name = None

    def run(self):
        """Run the check."""
        if self.process_name is None:
            raise ImproperlyConfigured(
                f'{self.__class__.__name__} has to have process_name defined'
            )

        for p in psutil.process_iter():
            if self.process_name in p.name():
                return 'OK'

        return 'ERROR'
