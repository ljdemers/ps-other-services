"""Screening API screenings history views module"""
from flask.wrappers import Request
from flask import render_template
from flask_weasyprint import HTML, render_pdf
from openapi_core.schema.specs.models import Spec
from screening_api.lib.auth.base import Authentication
from screening_api.lib.flask.views import OpenAPIHTTPMethodView
from screening_api.lib.flask.responses import json
from screening_api.screenings_reports.repositories import (
    ScreeningsReportsRepository,
)
from screening_api.screenings.repositories import (
    ScreeningsRepository,
)


class ScreeningShipInfoReportView(OpenAPIHTTPMethodView):
    def __init__(
            self,
            spec: Spec,
            authentication: Authentication,
            repository: ScreeningsReportsRepository,
    ):
        super(ScreeningShipInfoReportView, self).__init__(
            spec, authentication)
        self.repository = repository

    def get(self, request: Request, *args, **kwargs):
        screening_id = request.openapi.parameters.path['screening_id']

        report = self.repository.get_or_none(
            screening_id=screening_id,
            screening__account_id=request.user.account_id,
        )

        if report is None:
            status = 404
            errors = [
                {
                    'title': "Screening report not found",
                    'status': status,
                }
            ]
            resp = {
                'errors': errors,
            }
            return json(resp, status=status)

        resp = {
            'data': report.ship_info,
        }
        return json(resp)


class ScreeningShipInspectionsReportView(OpenAPIHTTPMethodView):
    def __init__(
            self,
            spec: Spec,
            authentication: Authentication,
            repository: ScreeningsReportsRepository,
    ):
        super(ScreeningShipInspectionsReportView, self).__init__(
            spec, authentication)
        self.repository = repository

    def get(self, request: Request, *args, **kwargs):
        screening_id = request.openapi.parameters.path['screening_id']

        report = self.repository.get_or_none(
            screening_id=screening_id,
            screening__account_id=request.user.account_id,
        )

        if report is None:
            status = 404
            errors = [
                {
                    'title': "Screening report not found",
                    'status': status,
                }
            ]
            resp = {
                'errors': errors,
            }
            return json(resp, status=status)

        resp = {
            'data': report.ship_inspections,
        }
        return json(resp)


class ScreeningShipSanctionsReportView(OpenAPIHTTPMethodView):
    def __init__(
            self,
            spec: Spec,
            authentication: Authentication,
            repository: ScreeningsReportsRepository,
    ):
        super(ScreeningShipSanctionsReportView, self).__init__(
            spec, authentication)
        self.repository = repository

    def get(self, request: Request, *args, **kwargs):
        screening_id = request.openapi.parameters.path['screening_id']

        report = self.repository.get_or_none(
            screening_id=screening_id,
            screening__account_id=request.user.account_id,
        )

        if report is None:
            status = 404
            errors = [
                {
                    'title': "Screening report not found",
                    'status': status,
                }
            ]
            resp = {
                'errors': errors,
            }
            return json(resp, status=status)

        resp = {
            'data': report.ship_sanction,
        }
        return json(resp)


class ScreeningCountrySanctionsReportView(OpenAPIHTTPMethodView):
    def __init__(
            self,
            spec: Spec,
            authentication: Authentication,
            repository: ScreeningsReportsRepository,
    ):
        super(ScreeningCountrySanctionsReportView, self).__init__(
            spec, authentication)
        self.repository = repository

    def get(self, request: Request, *args, **kwargs):
        screening_id = request.openapi.parameters.path['screening_id']

        report = self.repository.get_or_none(
            screening_id=screening_id,
            screening__account_id=request.user.account_id,
        )

        if report is None:
            status = 404
            errors = [
                {
                    'title': "Screening report not found",
                    'status': status,
                }
            ]
            resp = {
                'errors': errors,
            }
            return json(resp, status=status)

        resp = {
            "data": {
                'ship_flag': report.ship_flag,
                'ship_registered_owner': report.ship_registered_owner,
                'ship_operator': report.ship_operator,
                'ship_beneficial_owner': report.ship_beneficial_owner,
                'ship_manager': report.ship_manager,
                'ship_technical_manager': report.ship_technical_manager,
            },
        }
        return json(resp)


class ScreeningShipMovementsReportView(OpenAPIHTTPMethodView):
    def __init__(
            self,
            spec: Spec,
            authentication: Authentication,
            repository: ScreeningsReportsRepository,
    ):
        super(ScreeningShipMovementsReportView, self).__init__(
            spec, authentication)
        self.repository = repository

    def get(self, request: Request, *args, **kwargs):
        screening_id = request.openapi.parameters.path['screening_id']

        report = self.repository.get_or_none(
            screening_id=screening_id,
            screening__account_id=request.user.account_id,
        )

        if report is None:
            status = 404
            errors = [
                {
                    'title': "Screening report not found",
                    'status': status,
                }
            ]
            resp = {
                'errors': errors,
            }
            return json(resp, status=status)

        resp = {
            'data': report.port_visits,
        }
        return json(resp)


class ScreeningCompanySanctionsReportView(OpenAPIHTTPMethodView):
    def __init__(
            self,
            spec: Spec,
            authentication: Authentication,
            repository: ScreeningsReportsRepository,
    ):
        super(ScreeningCompanySanctionsReportView, self).__init__(
            spec, authentication)
        self.repository = repository

    def get(self, request: Request, *args, **kwargs):
        screening_id = request.openapi.parameters.path['screening_id']

        report = self.repository.get_or_none(
            screening_id=screening_id,
            screening__account_id=request.user.account_id,
        )

        if report is None:
            status = 404
            errors = [
                {
                    'title': "Screening report not found",
                    'status': status,
                }
            ]
            resp = {
                'errors': errors,
            }
            return json(resp, status=status)

        resp = {
            "data": {
                'ship_registered_owner_company':
                    report.ship_registered_owner_company,
                'ship_operator_company':
                    report.ship_operator_company,
                'ship_beneficial_owner_company':
                    report.ship_beneficial_owner_company,
                'ship_manager_company':
                    report.ship_manager_company,
                'ship_technical_manager_company':
                    report.ship_technical_manager_company,
                'ship_company_associates':
                    report.ship_company_associates,
            },
        }
        return json(resp)


class ScreeningPdfReportView(OpenAPIHTTPMethodView):
    def __init__(
            self,
            spec: Spec,
            authentication: Authentication,
            screening: ScreeningsRepository,
            screening_report,
            template_name
    ):
        super(ScreeningPdfReportView, self).__init__(
            spec, authentication)
        self.screening = screening
        self.screening_report = screening_report
        self.template_name = template_name

    def get(self, request: Request, *args, **kwargs):
        screening_id = request.openapi.parameters.path['screening_id']
        history_id = request.openapi.parameters.path.get('history_id')

        if history_id is not None:  # getting data from history
            report = self.screening_report.get_or_none(
                id=history_id,
            )
        else:
            report = self.screening_report.get_or_none(
                screening_id=screening_id,
                screening__account_id=request.user.account_id,
            )

        screening = self.screening.get_or_none(
            id=screening_id, account_id=request.user.account_id)

        if history_id is not None:
            screening = report

        if report is None or screening is None:
            status = 404
            errors = [
                {
                    'title': "Screening report not found",
                    'status': status,
                }
            ]
            resp = {
                'errors': errors,
            }
            return json(resp, status=status)

        associations = ["ship_technical_manager", "ship_operator",
                        "ship_registered_owner", "ship_beneficial_owner",
                        "ship_manager"]
        association_names = ["Technical manager", "Operator",
                             "Registered owner",
                             "Group beneficial owner",
                             "Ship manager"]

        try:  # Catch any exception during report generation
            html = render_template(self.template_name,
                                   screening=screening,
                                   screening_result=report,
                                   associations=associations,
                                   association_names=association_names)

            filename = report.ship_info['imo']
            resp = render_pdf(HTML(string=html),
                              download_filename=filename + ".pdf")
        except Exception as exc:
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

        return resp
