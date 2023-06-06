"""Screening Workers ship info checks module"""
from screening_api.screenings.enums import Severity
from screening_api.screenings_reports.models import ScreeningReport

from screening_workers.lib.screening.checks import ReportCheck
from screening_workers.lib.screening.providers import DataProvider
from screening_workers.ship_info.reports.makers import ShipInfoReportMaker
from screening_workers.ship_info.reports.models import ShipInfoReport


class ShipInfoCheck(ReportCheck):

    name = 'ship_info'

    def update_report(
            self,
            report: ScreeningReport,
            data_provider: DataProvider,
            session,
    ):
        # @todo: remove when moved to separate check task
        ship_info_report = self.make_report(data_provider)
        self._set_check_report(
            report, ship_info_report, session=session)

    def make_report(self, data_provider: DataProvider) -> ShipInfoReport:
        return ShipInfoReportMaker(
            data_provider.screening_profile,
        ).make_report(data_provider)

    def _set_screening_check_status_pending(self, screening_id: int):
        pass

    def _set_screening_check_status_done(
            self, screening_id: int, severity: Severity):
        pass
