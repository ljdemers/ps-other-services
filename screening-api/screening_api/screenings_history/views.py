"""Screening API screenings history views module"""
from flask.wrappers import Request
from openapi_core.schema.specs.models import Spec

from screening_api.lib.auth.base import Authentication
from screening_api.lib.flask.views import OpenAPIHTTPMethodView
from screening_api.lib.flask.responses import json, json_page
from screening_api.screenings.repositories import ScreeningsRepository
from screening_api.screenings_history.repositories import (
    ScreeningsHistoryRepository,
)


class ScreeningsHistoryView(OpenAPIHTTPMethodView):

    def __init__(
            self,
            spec: Spec,
            authentication: Authentication,
            repository: ScreeningsHistoryRepository,
            screenings_repository: ScreeningsRepository,
    ):
        super(ScreeningsHistoryView, self).__init__(spec, authentication)
        self.repository = repository
        self.screenings_repository = screenings_repository

    def get(self, request: Request, *args, **kwargs):
        screening_id = request.openapi.parameters.path['screening_id']

        page = request.openapi.parameters.query['page']
        limit = request.openapi.parameters.query['limit']
        offset = request.openapi.parameters.query['offset']

        screening = self.screenings_repository.get_or_none(
            id=screening_id, account_id=request.user.account_id)

        if screening is None:
            status = 404
            errors = [
                {
                    'title': "Screening not found",
                    'status': status,
                }
            ]
            resp = {
                'errors': errors,
            }
            return json(resp, status=status)

        paginator = self.repository.find_paginated(
            screening__account_id=request.user.account_id,
            screening_id=screening_id, limit=limit, offset=offset,
        )

        try:
            page_obj = paginator.page(page)
        except IndexError as exc:
            status = 404
            errors = [
                {
                    'title': str(exc),
                    'status': status,
                }
            ]
            resp = {
                'errors': errors,
            }
            return json(resp, status=status)

        return json_page(request, page_obj)
