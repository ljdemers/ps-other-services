"""Screening Workers country sanctions reports models module"""
from collections import namedtuple

from screening_api.screenings.enums import Severity


BaseShipFlagReport = namedtuple(
    'BaseShipFlagReport',
    [
        'country', 'severity'
    ],
)


BaseShipAssociatedCountryReport = namedtuple(
    'BaseShipAssociatedCountryReport',
    [
        'country_of_domicile', 'country_of_control', 'country_of_registration',
        'country_of_domicile_severity', 'country_of_control_severity',
        'country_of_registration_severity', 'company',
    ],
)


class ShipFlagReport(BaseShipFlagReport):

    def asdict(self) -> dict:
        data = self._asdict()
        data['severity'] = self.severity.name
        return data


class ShipAssociatedCountryReport(BaseShipAssociatedCountryReport):

    @property
    def severity(self) -> Severity:
        return max(
            self.country_of_domicile_severity,
            self.country_of_control_severity,
            self.country_of_registration_severity,
        )

    def asdict(self) -> dict:
        data = self._asdict()
        data['country_of_domicile_severity'] =\
            self.country_of_domicile_severity.name
        data['country_of_control_severity'] =\
            self.country_of_control_severity.name
        data['country_of_registration_severity'] =\
            self.country_of_registration_severity.name
        return data
