"""Screening Workers country sanctions reports makers module"""
from typing import Tuple, Union

from screening_api.blacklisted_countries.models import BlacklistedCountry
from screening_api.blacklisted_countries.repositories import (
    BlacklistedCountriesRepository,
)
from screening_api.ships.models import Ship
from screening_api.screenings.enums import Severity

from screening_workers.lib.screening.providers import DataProvider
from screening_workers.lib.screening.reports.makers import CheckReportMaker

from screening_workers.country_sanctions.mixins import (
    ShipAssociatedCountriesMixin,
)
from screening_workers.country_sanctions.reports.models import (
    ShipFlagReport, ShipAssociatedCountryReport,
)
from screening_workers.screenings_profiles.models import (
    DefaultScreeningProfile as ScreeningProfile,
)


class ShipFlagReportMaker(CheckReportMaker):

    def __init__(
            self,
            screening_profile: ScreeningProfile,
            repository: BlacklistedCountriesRepository,
    ):
        self.screening_profile = screening_profile
        self.repository = repository

    def make_report(self, data_provider: DataProvider) -> ShipFlagReport:
        country_name = self._get_ship_flag_country_name(
            data_provider.ship)

        blacklisted = self._get_blacklisted_or_none(country_name)
        severity = blacklisted and blacklisted.severity or Severity.OK

        return ShipFlagReport(country=country_name, severity=severity)

    def _get_ship_flag_country_name(self, ship: Ship) -> str:
        return ship.country_name

    def _get_blacklisted_or_none(
            self, country_name: str) -> Union[BlacklistedCountry, None]:
        return self.repository.get_or_none(country_name=country_name)


class ShipAssociatedCountryReportMaker(CheckReportMaker):

    def __init__(
            self,
            screening_profile: ScreeningProfile,
            repository: BlacklistedCountriesRepository,
            associate_name: str,
    ):
        self.screening_profile = screening_profile
        self.repository = repository
        self.associate_name = associate_name

    def make_report(
            self, data_provider: DataProvider) -> ShipAssociatedCountryReport:
        ship = ShipAssociatedCountriesMixin(data_provider.ship)

        company = ship.get_company(self.associate_name)

        country_of_domicile = ship.get_country_of_domicile(self.associate_name)
        country_of_control = ship.get_country_of_control(self.associate_name)
        country_of_registration = ship.get_country_of_registration(
            self.associate_name)

        severities = self._get_associated_countries_severities(
            country_of_domicile, country_of_control, country_of_registration)

        country_of_domicile_severity, country_of_control_severity,\
            country_of_registration_severity = severities

        if country_of_domicile is None:
            country_of_domicile_severity = self.screening_profile.\
                unknown_country_of_domicile_severity

        if country_of_control is None:
            country_of_control_severity = self.screening_profile.\
                unknown_country_of_control_severity

        if country_of_registration is None:
            country_of_registration_severity = self.screening_profile.\
                unknown_country_of_registration_severity

        return ShipAssociatedCountryReport(
            company=company,
            country_of_domicile=country_of_domicile,
            country_of_control=country_of_control,
            country_of_registration=country_of_registration,
            country_of_domicile_severity=country_of_domicile_severity,
            country_of_control_severity=country_of_control_severity,
            country_of_registration_severity=country_of_registration_severity,
        )

    def _get_associated_countries_severities(
            self, country_of_domicile: str, country_of_control: str,
            country_of_registration: str,
    ) -> Tuple[Severity, Severity, Severity]:
        return self.repository.\
            get_associated_countries_severities(
                country_of_domicile, country_of_control,
                country_of_registration,
            )
