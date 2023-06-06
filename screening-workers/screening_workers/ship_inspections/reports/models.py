"""Screening Workers ship inspections reports models module"""
from collections import namedtuple
from typing import List

from screening_api.screenings.enums import Severity

from screening_workers.lib.screening.reports.models import Report
from screening_workers.lib.utils import date2str, DATE_FORMAT


BaseShipInspectionReport = namedtuple(
    'BaseShipInspectionEntry',
    [
        'authority', 'port_name', 'country_name', 'inspection_date',
        'detained', 'detained_days', 'defects_count', 'detained_days_severity',
        'defects_count_severity',
    ],
)


class ShipInspectionReport(BaseShipInspectionReport):

    @property
    def severity(self):
        return max(self.detained_days_severity, self.defects_count_severity)

    def asdict(self):
        data = self._asdict()
        data['inspection_date'] = date2str(
            self.inspection_date, date_format=DATE_FORMAT)
        data['detained_days_severity'] = self.detained_days_severity.name
        data['defects_count_severity'] = self.defects_count_severity.name
        return data


class ShipInspectionsReport(Report):

    def __init__(self, inspections: List[ShipInspectionReport]):
        self.inspections = inspections

    @property
    def severity(self) -> Severity:
        if not self.inspections:
            return Severity.OK

        return max(map(lambda x: x.severity, self.inspections))

    def asdict(self) -> dict:
        return {
            'inspections': list(map(lambda x: x.asdict(), self.inspections)),
        }
