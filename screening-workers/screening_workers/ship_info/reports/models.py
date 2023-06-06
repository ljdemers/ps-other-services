"""Screening Workers ship info reports models module"""
from collections import namedtuple

from screening_api.screenings.enums import Severity


BaseShipInfoReport = namedtuple(
    'BaseShipInfoReport',
    [
        'name', 'imo', 'type', 'build_year', 'build_age', 'build_age_severity',
        'country_name', 'country_id', 'flag_effective_date', 'mmsi',
        'call_sign', 'status', 'port_of_registry', 'deadweight', 'weight',
        'length', 'breadth', 'displacement', 'draught', 'registered_owner',
        'operator', 'group_beneficial_owner', 'ship_manager',
        'technical_manager', 'shipbuilder', 'build_country_name',
        'classification_society',
    ],
)


class ShipInfoReport(BaseShipInfoReport):

    @property
    def severity(self):
        return Severity.OK

    def asdict(self):
        data = self._asdict()
        data['build_age_severity'] = self.build_age_severity.name
        return data
