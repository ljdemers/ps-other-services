"""Screening Workers ship sanctions reports models module"""
from collections import namedtuple
from typing import List

from screening_api.screenings.enums import Severity

from screening_workers.lib.screening.reports.models import Report
from screening_workers.lib.utils import date2str


BaseShipSanctionReport = namedtuple(
    'BaseShipSanctionReport',
    [
        'sanction_name', 'listed_since', 'listed_to', 'sanction_severity',
    ],
)


class ShipSanctionReport(BaseShipSanctionReport):

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


class ShipSanctionsReport(Report):

    def __init__(self, sanctions: List[ShipSanctionReport]):
        self.sanctions = sanctions

    @property
    def severity(self) -> Severity:
        if not self.sanctions:
            return Severity.OK

        return max(map(lambda x: x.severity, self.sanctions))

    def asdict(self) -> dict:
        return {
            'sanctions': list(map(lambda x: x.asdict(), self.sanctions)),
        }
