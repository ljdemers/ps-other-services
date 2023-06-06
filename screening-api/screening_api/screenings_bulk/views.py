"""Screening API screenings bulk views module"""
import logging

from flask.wrappers import Request
from openapi_core.schema.specs.models import Spec

from screening_api.lib.auth.base import Authentication
from screening_api.lib.flask.views import OpenAPIHTTPMethodView
from screening_api.lib.flask.responses import HTTPResponse, json
from screening_api.screenings_bulk.readers import (
    BulkScreeningCSVReader, BulkScreeningCSVReaderError,
)
from screening_api.screenings_bulk.recorders import (
    BytesRecoder, ListRecorder, StreamRecoder,
)
from screening_api.screenings_bulk.repositories import BulkScreeningsRepository

log = logging.getLogger(__name__)


class BulkScreeningsView(OpenAPIHTTPMethodView):
    """Bulk screening view."""

    recorders_registry = {
        'application/json': ListRecorder,
        'text/csv': BytesRecoder,
        'application/vnd.ms-excel': BytesRecoder,
        'multipart/form-data': StreamRecoder,
    }

    def __init__(
            self, spec: Spec,
            authentication: Authentication,
            repository: BulkScreeningsRepository,
    ):
        super(BulkScreeningsView, self).__init__(spec, authentication)
        self.repository = repository

    def get(self, request: Request, *args, **kwargs) -> HTTPResponse:
        statuses = request.openapi.parameters.query.get('statuses')
        results = request.openapi.parameters.query.get('results')

        data = self.repository.find(
            account_id=request.user.account_id, statuses=statuses,
            results=results,
        )

        count = len(data)

        resp = {
            "data": data,
            "meta": {
                "count": count,
            },
            "links": {
                "first": request.url,
            },
        }
        return json(resp)

    def post(self, request: Request, *args, **kwargs) -> HTTPResponse:
        try:
            recorder_class = self.recorders_registry[request.mimetype]
        except KeyError as exc:
            errors = [{
                'title': str(exc),
                'status': 400,
                'class': str(type(exc)),
            }]
            resp = {
                'errors': errors,
            }
            return json(resp, status=400)

        recorder = recorder_class.from_request(request)
        reader = BulkScreeningCSVReader(recorder)

        try:
            imo_ids = reader.read_imo_ids()
        except BulkScreeningCSVReaderError as exc:
            errors = [{
                'title': str(exc),
                'status': 400,
                'class': str(type(exc)),
            }]
            resp = {
                'errors': errors,
            }
            return json(resp, status=400)

        self.repository.create_many(request.user.account_id, *imo_ids)

        return HTTPResponse(status=202)

    def delete(self, request: Request, *args, **kwargs) -> HTTPResponse:
        self.repository.delete(account_id=request.user.account_id)

        return HTTPResponse(status=204)


class BulkScreeningView(OpenAPIHTTPMethodView):
    """Bulk screening view."""

    def __init__(
            self,
            spec: Spec,
            authentication: Authentication,
            repository: BulkScreeningsRepository,
    ):
        super(BulkScreeningView, self).__init__(spec, authentication)
        self.repository = repository

    def delete(self, request: Request, *args, **kwargs) -> HTTPResponse:
        bulk_screening_id = request.openapi.parameters.path[
            'bulk_screening_id']

        self.repository.delete(
            id=bulk_screening_id, account_id=request.user.account_id)

        return HTTPResponse(status=204)
