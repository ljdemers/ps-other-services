from flask.wrappers import Request
from openapi_core.schema.specs.models import Spec

from screening_api.lib.auth.base import Authentication
from screening_api.lib.flask.views import OpenAPIHTTPMethodView
from screening_api.lib.flask.responses import json
from screening_api.ships.repositories import ShipsRepository


class ShipTypesView(OpenAPIHTTPMethodView):

    def __init__(
            self,
            repository: ShipsRepository,
            spec: Spec,
            authentication: Authentication,
    ):
        super(ShipTypesView, self).__init__(spec, authentication)
        self.repository = repository

    def get(self, request: Request, *args, **kwargs):
        search = request.openapi.parameters.query['search']

        data = self.repository.find_types(search=search)
        meta = {
            'count': len(data),
        }
        links = {}

        resp = {
            'data': data,
            'meta': meta,
            'links': links,
        }

        return json(resp)
