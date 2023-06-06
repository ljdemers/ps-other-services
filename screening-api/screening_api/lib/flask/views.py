from flask.globals import request
from flask.views import MethodView
from openapi_core.schema.specs.models import Spec
from openapi_core.contrib.flask.views import FlaskOpenAPIView

from screening_api.lib.auth.base import Authentication
from screening_api.lib.auth.exceptions import BaseAuthenticationError
from screening_api.lib.flask.mixins import HTTPMethodViewMixin
from screening_api.lib.flask.responses import json


class HTTPMethodView(HTTPMethodViewMixin, MethodView):
    """Passes request object to dispached method."""
    pass


class OpenAPIHTTPMethodView(HTTPMethodViewMixin, FlaskOpenAPIView):
    """Brings OpenAPI specification validation and marshalling for requests."""

    def __init__(self, spec: Spec, authentication: Authentication):
        super(OpenAPIHTTPMethodView, self).__init__(spec)
        self.authentication = authentication

    def dispatch_request(self, *args, **kwargs):
        errors = []

        try:
            user = self.authentication.authenticate(request)
        except BaseAuthenticationError as exc:
            errors.append({
                'title': str(exc),
                'status': 401,
                'class': str(type(exc)),
            })
            resp = {
                'errors': errors,
            }
            return json(resp, status=401)
        else:
            request.user = user

        return super(OpenAPIHTTPMethodView, self).dispatch_request(
            *args, **kwargs)
