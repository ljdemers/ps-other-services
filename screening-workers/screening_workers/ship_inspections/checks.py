"""Screening Workers ship inspections checks module"""
from screening_api.screenings_reports.repositories import (
    ScreeningsReportsRepository,
)
from screening_api.screenings.models import Screening
from screening_api.screenings.repositories import ScreeningsRepository

from screening_workers.lib.screening.checks import ReportCheck
from screening_workers.lib.screening.providers import DataProvider
from screening_workers.lib.sis_api.cache.collections import (
    ShipInspectionsCollection,
)
from screening_workers.ship_inspections.reports.makers import (
    ShipInspectionsReportMaker,
)
from screening_workers.ship_inspections.reports.models import (
    ShipInspectionsReport,
)


class ShipInspectionsCheck(ReportCheck):

    name = 'ship_inspections'

    CRITICAL_AUTHORITIES = ['Paris MOU', 'US Coastguard', 'US Coastguard LE']

    def __init__(
            self,
            screenings_repository: ScreeningsRepository,
            screenings_reports_repository: ScreeningsReportsRepository,
            ship_inspections_collection: ShipInspectionsCollection,
    ):
        super(ShipInspectionsCheck, self).__init__(
            screenings_repository, screenings_reports_repository)
        self.ship_inspections_collection = ship_inspections_collection

    def get_data_provider(self, screening: Screening) -> DataProvider:
        data_provider = super(ShipInspectionsCheck, self).get_data_provider(
            screening)
        inspections = self._find_inspections(screening.ship_id)
        critical_authorities = self._find_critical_authorities()

        data_provider.update(
            screening=screening,
            inspections=inspections,
            critical_authorities=critical_authorities,
        )

        return data_provider

    def make_report(
            self, data_provider: DataProvider) -> ShipInspectionsReport:
        return ShipInspectionsReportMaker(
            data_provider.screening_profile,
        ).make_report(data_provider)

    def _find_inspections(self, ship_id: int):
        return self.ship_inspections_collection.query(ship_id)

    def _find_critical_authorities(self):
        return self.CRITICAL_AUTHORITIES
