"""Screening API screenings views module"""
from datetime import datetime
from io import StringIO

from flask.wrappers import Request
from openapi_core.schema.specs.models import Spec

from screening_api.lib.auth.base import Authentication
from screening_api.lib.flask.views import OpenAPIHTTPMethodView
from screening_api.lib.flask.responses import (
    HTTPResponse, json, json_page, csv,
)
from screening_api.screenings.repositories import ScreeningsRepository
from screening_api.screenings.writers import ScreeningsCSVWriter


class ScreeningsFilterMixin:

    def get_filters(self, request):
        ids = request.openapi.parameters.query.get('ids')
        search = request.openapi.parameters.query['search']
        ship__country_ids = request.openapi.parameters.query.get(
            'ship__country_ids')
        severities = request.openapi.parameters.query.get('severities')
        company_sanctions_severities = request.openapi.parameters.query.get(
            'company_sanctions_severities')
        ship_sanctions_severities = request.openapi.parameters.query.get(
            'ship_sanctions_severities')
        country_sanctions_severities = request.openapi.parameters.query.get(
            'country_sanctions_severities')
        ship_inspections_severities = request.openapi.parameters.query.get(
            'ship_inspections_severities')
        ship_movements_severities = request.openapi.parameters.query.get(
            'ship_movements_severities')
        severity_change = request.openapi.parameters.query.get(
            'severity_change')
        ship__types = request.openapi.parameters.query.get('ship__types')

        created__lte = datetime.utcnow()
        return dict(
            account_id=request.user.account_id,
            ship__country_ids=ship__country_ids,
            ship__types=ship__types, search=search,
            created__lte=created__lte, severities=severities,
            company_sanctions_severities=company_sanctions_severities,
            ship_sanctions_severities=ship_sanctions_severities,
            country_sanctions_severities=country_sanctions_severities,
            ship_inspections_severities=ship_inspections_severities,
            ship_movements_severities=ship_movements_severities,
            severity_change=severity_change, id__in=ids,
        )


class ScreeningsView(OpenAPIHTTPMethodView, ScreeningsFilterMixin):

    def __init__(
            self,
            repository: ScreeningsRepository,
            spec: Spec,
            authentication: Authentication,
    ):
        super(ScreeningsView, self).__init__(spec, authentication)
        self.repository = repository

    def get_options(self, request):
        joinedload_related = ['ship', ]
        sort = request.openapi.parameters.query['sort']
        return dict(
            joinedload_related=joinedload_related,
            innerjoin=True,
            sort=sort,
        )

    def get(self, request: Request, *args, **kwargs):
        response_format = request.openapi.parameters.query['format']
        page = request.openapi.parameters.query['page']
        limit = request.openapi.parameters.query['limit']

        filters = self.get_filters(request)
        options = self.get_options(request)

        if response_format == 'csv':
            screenings = self.repository.find(**filters, **options)

            if not screenings:
                errors = [
                    {
                        'title': 'Screenings not found',
                        'status': 404,
                    }
                ]
                resp = {
                    'errors': errors,
                }
                return json(resp, status=404)

            data = StringIO()
            writer = ScreeningsCSVWriter(data)
            writer.write(screenings)
            data.seek(0)
            return csv(data, 'screening.csv')

        paginator = self.repository.find_paginated(
            **filters, **options, limit=limit)

        try:
            page_obj = paginator.page(page)
        except IndexError as exc:
            errors = [
                {
                    'title': str(exc),
                    'status': 404,
                }
            ]
            resp = {
                'errors': errors,
            }
            return json(resp, status=404)

        return json_page(request, page_obj)

    def delete(self, request: Request, *args, **kwargs):
        filters = self.get_filters(request)

        self.repository.delete(**filters)
        self.repository.delete_orphans()

        return HTTPResponse(status=204)


class ScreeningView(OpenAPIHTTPMethodView):

    def __init__(
            self,
            repository: ScreeningsRepository,
            spec: Spec,
            authentication: Authentication,
    ):
        super(ScreeningView, self).__init__(spec, authentication)
        self.repository = repository

    def get(self, request: Request, *args, **kwargs):
        screening_id = request.openapi.parameters.path['screening_id']

        screening = self.repository.get_or_none(
            id=screening_id, account_id=request.user.account_id)

        if not screening:
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

        resp = {
            "data": {
                'id': screening.id,
                'created': screening.created,
                'updated': screening.updated,
                'severity': screening.severity,
                'company_sanctions_severity':
                    screening.company_sanctions_severity,
                'ship_sanctions_severity': screening.ship_sanctions_severity,
                'country_sanctions_severity':
                    screening.country_sanctions_severity,
                'ship_inspections_severity':
                    screening.ship_inspections_severity,
                'ship_movements_severity': screening.ship_movements_severity,

                'status': screening.status,
                'company_sanctions_status': screening.company_sanctions_status,
                'ship_sanctions_status': screening.ship_sanctions_status,
                'country_sanctions_status': screening.country_sanctions_status,
                'ship_inspections_status': screening.ship_inspections_status,
                'ship_movements_status': screening.ship_movements_status,
            },
        }
        return json(resp)


class ScreenView(OpenAPIHTTPMethodView, ScreeningsFilterMixin):

    def __init__(
            self,
            repository: ScreeningsRepository,
            spec: Spec,
            authentication: Authentication,
    ):
        super(ScreenView, self).__init__(spec, authentication)
        self.repository = repository

    def post(self, request: Request, *args, **kwargs):
        filters = self.get_filters(request)

        self.repository.screen_many(**filters)

        return HTTPResponse(status=202)
