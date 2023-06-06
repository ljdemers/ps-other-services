"""Screening Workers ship inspections checks module"""
from typing import List

from screening_api.screenings_reports.repositories import (
    ScreeningsReportsRepository,
)
from screening_api.screenings.enums import Severity
from screening_api.screenings.models import Screening
from screening_api.screenings.repositories import ScreeningsRepository
from screening_api.ship_sanctions.models import ShipSanction

from screening_workers.lib.screening.checks import BaseCheck, ReportCheck
from screening_workers.lib.screening.providers import DataProvider
from screening_workers.lib.compliance_api.cache.collections import (
    ShipSanctionsCollection,
)
from screening_workers.ship_sanctions.reports.makers import (
    ShipSanctionsReportMaker,
)
from screening_workers.ship_sanctions.reports.models import ShipSanctionsReport


class ShipAssociationCheck(BaseCheck):

    name = 'ship_association'

    def process(self, screening: Screening) -> Severity:
        # @todo: implement
        return Severity.OK


class ShipSanctionCheck(ReportCheck):

    name = 'ship_sanction'

    def __init__(
            self,
            screenings_repository: ScreeningsRepository,
            screenings_reports_repository: ScreeningsReportsRepository,
            ship_sanctions_collection: ShipSanctionsCollection,
    ):
        super(ShipSanctionCheck, self).__init__(
            screenings_repository, screenings_reports_repository)
        self.ship_sanctions_collection = ship_sanctions_collection

    def get_data_provider(self, screening: Screening) -> DataProvider:
        data_provider = super(ShipSanctionCheck, self).get_data_provider(
            screening)
        sanctions = self._find_sanctions(
            screening.ship_id,
            data_provider.screening_profile.blacklisted_sanction_list_id,
        )

        data_provider.update(sanctions=sanctions)

        return data_provider

    def make_report(self, data_provider: DataProvider) -> ShipSanctionsReport:
        return ShipSanctionsReportMaker(
            data_provider.screening_profile,
        ).make_report(data_provider)

    def _find_sanctions(
            self, ship_id: int, blacklisted_sanction_list_id: int = None,
    ) -> List[ShipSanction]:
        return self.ship_sanctions_collection.query(
            ship_id, blacklisted_sanction_list_id)
