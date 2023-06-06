"""Screening Workers screenings history creators module"""
import logging

from screening_api.screenings.enums import Status
from screening_api.screenings.repositories import ScreeningsRepository
from screening_api.screenings_history.repositories import (
    ScreeningsHistoryRepository,
)
from screening_api.screenings_reports.repositories import (
    ScreeningsReportsRepository,
)

log = logging.getLogger(__name__)


class ScreeningsHistoryCreator:

    def __init__(
            self,
            screenings_repository: ScreeningsRepository,
            screenings_history_repository: ScreeningsHistoryRepository,
            screenings_reports_repository: ScreeningsReportsRepository,
    ):
        self.screenings_repository = screenings_repository
        self.screenings_history_repository = screenings_history_repository
        self.screenings_reports_repository = screenings_reports_repository

    def create(self, screening_id):
        screening = self._get_screening(screening_id)

        if screening.status != Status.DONE:
            return

        report = self._get_screening_report(screening_id)

        self._create_screening_history(screening, report)
        log.info(
            'Created screening history <%s>',
            screening_id
        )

    def _get_screening(self, screening_id):
        return self.screenings_repository.get(id=screening_id)

    def _get_screening_report(self, screening_id):
        return self.screenings_reports_repository.get_or_none(
            screening_id=screening_id)

    def _create_screening_history(self, screening, report):
        reports = {}
        severities = {
            'ship_registered_owner_company_severity':
                screening.ship_registered_owner_company_severity,
            'ship_operator_company_severity':
                screening.ship_operator_company_severity,
            'ship_beneficial_owner_company_severity':
                screening.ship_beneficial_owner_company_severity,
            'ship_manager_company_severity':
                screening.ship_manager_company_severity,
            'ship_technical_manager_company_severity':
                screening.ship_technical_manager_company_severity,
            'ship_company_associates_severity':
                screening.ship_company_associates_severity,

            'ship_association_severity': screening.ship_association_severity,
            'ship_sanction_severity': screening.ship_sanction_severity,
            'ship_flag_severity': screening.ship_flag_severity,
            'ship_registered_owner_severity':
                screening.ship_registered_owner_severity,
            'ship_operator_severity': screening.ship_operator_severity,
            'ship_beneficial_owner_severity':
                screening.ship_beneficial_owner_severity,
            'ship_manager_severity': screening.ship_manager_severity,
            'ship_technical_manager_severity':
                screening.ship_technical_manager_severity,
            'doc_company_severity': screening.doc_company_severity,
            'ship_inspections_severity': screening.ship_inspections_severity,
            'port_visits_severity': screening.port_visits_severity,
            'zone_visits_severity': screening.zone_visits_severity,
        }
        if report:
            reports = {
                'ship_info': report.ship_info,

                'ship_registered_owner_company':
                    report.ship_registered_owner_company,
                'ship_operator_company': report.ship_operator_company,
                'ship_beneficial_owner_company':
                    report.ship_beneficial_owner_company,
                'ship_manager_company':
                    report.ship_manager_company,
                'ship_technical_manager_company':
                    report.ship_technical_manager_company,
                'ship_company_associates':
                    report.ship_company_associates,

                'ship_association': report.ship_association,
                'ship_sanction': report. ship_sanction,
                'ship_flag': report.ship_flag,
                'ship_registered_owner': report.ship_registered_owner,
                'ship_operator': report.ship_operator,
                'ship_beneficial_owner': report.ship_beneficial_owner,
                'ship_manager': report.ship_manager,
                'ship_technical_manager': report.ship_technical_manager,
                'doc_company': report.doc_company,
                'ship_inspections': report.ship_inspections,
                'port_visits': report.port_visits,
                'zone_visits': report.zone_visits,
            }
        return self.screenings_history_repository.create(
            screening.id, screening.updated, **severities, **reports)
