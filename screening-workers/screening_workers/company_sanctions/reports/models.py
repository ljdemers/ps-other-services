"""Screening Workers company sanctions reports models module"""
from collections import namedtuple
from typing import List

from screening_api.screenings.enums import Severity

from screening_workers.lib.screening.reports.models import Report
from screening_workers.lib.utils import date2str


BaseShipAssociatedCompanyReport = namedtuple(
    'BaseShipAssociatedCompanyReport',
    [
        'company_name', 'sanctions',
    ],
)


BaseCompanySanctionReport = namedtuple(
    'BaseCompanySanctionReport',
    [
        'sanction_name', 'listed_since', 'listed_to', 'sanction_severity',
    ],
)


BaseShipCompanyAssociatesReport = namedtuple(
    'BaseShipCompanyAssociatesReport',
    [
        'company_name', 'relationship', 'dst_type', 'dst_name', 'sanctions',
    ],
)


class CompanySanctionReport(BaseCompanySanctionReport):

    @property
    def severity(self):
        return self.sanction_severity

    def asdict(self):
        data = self._asdict()
        if self.listed_since is not None:
            data['listed_since'] = date2str(self.listed_since)
        if self.listed_to is not None:
            data['listed_to'] = date2str(self.listed_to)
        data['sanction_severity'] = self.sanction_severity.name
        return data


class ShipAssociatedCompanyReport(BaseShipAssociatedCompanyReport):

    @property
    def severity(self) -> Severity:
        if not self.sanctions:
            return Severity.OK

        return max(map(lambda x: x.severity, self.sanctions))

    def asdict(self) -> dict:
        data = self._asdict()
        data['sanctions'] = list(map(lambda x: x.asdict(), self.sanctions))
        return data


class ShipCompanyAssociateReport(BaseShipCompanyAssociatesReport):

    @property
    def severity(self) -> Severity:
        if not self.sanctions:
            return Severity.OK

        return max(map(lambda x: x.severity, self.sanctions))

    def asdict(self) -> dict:
        data = self._asdict()
        data['sanctions'] = list(map(lambda x: x.asdict(), self.sanctions))
        return data


class ShipCompanyAssociatesReport(Report):

    def __init__(self, associates: List[ShipCompanyAssociateReport]):
        self.associates = associates

    @property
    def severity(self) -> Severity:
        if not self.associates:
            return Severity.OK

        return max(map(lambda x: x.severity, self.associates))

    def asdict(self) -> dict:
        return {
            'associates': list(map(lambda x: x.asdict(), self.associates)),
        }
