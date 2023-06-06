"""Screening Workers ship sanctions reports makers module"""
from typing import List

from screening_api.screenings.enums import Severity
from screening_api.ship_sanctions.models import ShipSanction

from screening_workers.lib.screening.providers import DataProvider
from screening_workers.lib.screening.reports.makers import CheckReportMaker

from screening_workers.screenings_profiles.models import (
    DefaultScreeningProfile as ScreeningProfile,
)
from screening_workers.ship_sanctions.reports.models import (
    ShipSanctionsReport, ShipSanctionReport,
)


class ShipSanctionsReportMaker(CheckReportMaker):

    def __init__(self, screening_profile: ScreeningProfile):
        self.ship_sanction_report_maker = ShipSanctionReportMaker(
            screening_profile)

    def make_report(
            self, data_provider: DataProvider) -> ShipSanctionsReport:
        report_sanctions = self._get_sanctions(
            data_provider.sanctions)
        return ShipSanctionsReport(report_sanctions)

    def _get_sanctions(
            self,
            sanctions: List[ShipSanction],
    ) -> List[ShipSanctionReport]:
        return list(map(self._get_sanction_report, sanctions))

    def _get_sanction_report(
            self,
            sanction: ShipSanction,
    ) -> ShipSanctionReport:
        return self.ship_sanction_report_maker.make_report(sanction)


class ShipSanctionReportMaker:

    def __init__(self, screening_profile: ScreeningProfile):
        self.screening_profile = screening_profile

    def make_report(
            self,
            sanction: ShipSanction,
    ) -> ShipSanctionReport:
        sanction_severity = self._get_sanction_severity(sanction)
        return ShipSanctionReport(
            sanction_name=sanction.sanction_list_name,
            listed_since=sanction.start_date,
            listed_to=sanction.end_date,
            sanction_severity=sanction_severity,
        )

    def _get_sanction_severity(self, sanction: ShipSanction) -> Severity:
        if sanction.is_active:
            return self.screening_profile.ship_active_sanction_severity

        return Severity.OK
