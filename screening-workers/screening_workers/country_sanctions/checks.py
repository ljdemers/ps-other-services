"""Screening Workers country sanctions checks module"""
from screening_api.blacklisted_countries.repositories import (
    BlacklistedCountriesRepository,
)
from screening_api.screenings.enums import Severity
from screening_api.screenings.models import Screening
from screening_api.screenings.repositories import ScreeningsRepository
from screening_api.screenings_reports.repositories import (
    ScreeningsReportsRepository,
)

from screening_workers.lib.screening.checks import BaseCheck, ReportCheck
from screening_workers.lib.screening.providers import DataProvider
from screening_workers.lib.sis_api.cache.collections import ShipsCollection
from screening_workers.country_sanctions.reports.makers import (
    ShipFlagReportMaker, ShipAssociatedCountryReportMaker,
)
from screening_workers.country_sanctions.reports.models import (
    ShipFlagReport, ShipAssociatedCountryReport,
)


class BaseCountryCheck(ReportCheck):
    """
    Perform a country check for a relevant ship associate.
    """
    def __init__(
            self,
            screenings_repository: ScreeningsRepository,
            screenings_reports_repository: ScreeningsReportsRepository,
            ships_collection: ShipsCollection,
            blacklisted_countries_repository: BlacklistedCountriesRepository,
    ):
        super().__init__(screenings_repository, screenings_reports_repository)
        self.ships_collection = ships_collection
        self.blacklisted_countries_repository =\
            blacklisted_countries_repository

    def get_data_provider(self, screening: Screening) -> DataProvider:
        data_provider = super(BaseCountryCheck, self).get_data_provider(
            screening)
        ship = self._get_ship(screening.ship_id)

        data_provider.update(ship=ship)

        return data_provider

    def _get_ship(self, ship_id: int):
        return self.ships_collection.get(ship_id)


class BaseAssociateCountryCheck(BaseCountryCheck):

    associate_name = NotImplemented

    def make_report(
            self, data_provider: DataProvider) -> ShipAssociatedCountryReport:
        return ShipAssociatedCountryReportMaker(
            data_provider.screening_profile,
            self.blacklisted_countries_repository,
            self.associate_name,
        ).make_report(data_provider)


class ShipFlagCheck(BaseCountryCheck):

    name = 'ship_flag'

    def make_report(self, data_provider: DataProvider) -> ShipFlagReport:
        return ShipFlagReportMaker(
            data_provider.screening_profile,
            self.blacklisted_countries_repository,
        ).make_report(data_provider)

    def _get_or_create_plain_report(self, data_provider, session):
        report = super(ShipFlagCheck, self)._get_or_create_plain_report(
            data_provider, session)

        # @todo: move to separate check task
        from screening_workers.ship_info.checks import (
            ShipInfoCheck,
        )
        ship_info_check = ShipInfoCheck(
            self.screenings_repository, self.screenings_reports_repository)
        ship_info_check.update_report(report, data_provider, session=session)

        return report


class ShipRegisteredOwnerCheck(BaseAssociateCountryCheck):

    name = 'ship_registered_owner'
    associate_name = 'registered_owner'


class ShipOperatorCheck(BaseAssociateCountryCheck):

    name = 'ship_operator'
    associate_name = 'operator'


class ShipBeneficialOwnerCheck(BaseAssociateCountryCheck):

    name = 'ship_beneficial_owner'
    associate_name = 'group_beneficial_owner'


class ShipManagerCheck(BaseAssociateCountryCheck):

    name = 'ship_manager'
    associate_name = 'ship_manager'


class ShipTechnicalManagerCheck(BaseAssociateCountryCheck):

    name = 'ship_technical_manager'
    associate_name = 'technical_manager'


class DocCompanyCheck(BaseCheck):

    name = 'doc_company'

    def process(self, screening: Screening) -> Severity:
        # @todo: implement
        return Severity.OK
