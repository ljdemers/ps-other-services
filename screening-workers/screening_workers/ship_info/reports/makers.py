"""Screening Workers ship info reports makers module"""
from screening_api.ships.models import Ship

from screening_workers.lib.screening.providers import DataProvider
from screening_workers.lib.screening.reports.makers import CheckReportMaker

from screening_workers.screenings_profiles.models import (
    DefaultScreeningProfile as ScreeningProfile,
)
from screening_workers.ship_info.reports.models import ShipInfoReport


class ShipInfoReportMaker(CheckReportMaker):

    def __init__(self, screening_profile: ScreeningProfile):
        self.screening_profile = screening_profile

    def make_report(self, data_provider: DataProvider) -> ShipInfoReport:
        data = self._get_data(data_provider.ship)
        return ShipInfoReport(**data)

    def _get_data(self, ship: Ship) -> dict:
        return {
            field_name: getattr(ship, field_name)
            for field_name in ShipInfoReport._fields
        }
