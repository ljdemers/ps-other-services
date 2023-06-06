"""Screening Workers ship inspections reports makers module"""
from datetime import datetime, timedelta
from typing import List

from recordclass import recordclass

from screening_api.screenings.enums import Severity
from screening_api.ship_inspections.models import ShipInspection

from screening_workers.lib.screening.providers import DataProvider
from screening_workers.lib.screening.reports.makers import CheckReportMaker

from screening_workers.screenings_profiles.models import (
    DefaultScreeningProfile as ScreeningProfile,
)
from screening_workers.ship_inspections.reports.models import (
    ShipInspectionsReport, ShipInspectionReport,
)


ShipInspectionsReportState = recordclass(
    'ShipInspectionsReportState',
    [
        'created',
        'detained_last_12_months_critical_authorities_count',
        'detained_last_12_months_count',
        'detained_last_24_months_count',
        'is_last',
    ],
)


class ShipInspectionsReportMaker(CheckReportMaker):

    def __init__(self, screening_profile: ScreeningProfile):
        self.ship_inspection_report_maker = ShipInspectionReportMaker(
            screening_profile)

    def make_report(
            self, data_provider: DataProvider) -> ShipInspectionsReport:
        report_inspections = self._get_inspections(
            data_provider.inspections,
            data_provider.critical_authorities,
        )
        return ShipInspectionsReport(report_inspections)

    def _get_inspections(
            self,
            inspections: List[ShipInspection],
            critical_authorities: List[str],
    ) -> List[ShipInspectionReport]:
        reports = []
        state = ShipInspectionsReportState(
            created=datetime.utcnow(),
            detained_last_12_months_critical_authorities_count=0,
            detained_last_12_months_count=0,
            detained_last_24_months_count=0,
            is_last=False,
        )
        inspections_len = len(inspections)
        for idx, inspection in enumerate(reversed(inspections)):
            state.is_last = idx == inspections_len - 1
            report = self.ship_inspection_report_maker.make_report(
                inspection, critical_authorities, state)
            reports.append(report)
        return list(reversed(reports))

    def _get_inspection_report(
            self,
            inspection: ShipInspection,
            critical_authorities: List[str],
            state: ShipInspectionsReportState,
    ) -> ShipInspectionReport:
        return self.ship_inspection_report_maker.make_report(
            inspection, critical_authorities, state)


class ShipInspectionReportMaker:

    def __init__(self, screening_profile: ScreeningProfile):
        self.screening_profile = screening_profile

    def make_report(
            self,
            inspection: ShipInspection,
            critical_authorities: List[str],
            state: ShipInspectionsReportState,
    ) -> ShipInspectionReport:
        detention_severity = self._get_detention_severity(
            inspection, critical_authorities, state)
        deficiency_severity = self._get_deficiency_severity(inspection)
        return ShipInspectionReport(
            authority=inspection.authority,
            port_name=inspection.port_name,
            country_name=inspection.country_name,
            inspection_date=inspection.inspection_date,
            detained=inspection.detained,
            detained_days=inspection.detained_days,
            detained_days_severity=detention_severity,
            defects_count=inspection.defects_count,
            defects_count_severity=deficiency_severity,
        )

    def _get_detention_severity(
            self,
            inspection: ShipInspection,
            critical_authorities: List[str],
            state: ShipInspectionsReportState,
    ) -> Severity:
        if not inspection.detained:
            return Severity.OK

        last_12_months = state.created.date() - timedelta(days=365)
        if state.is_last and inspection.inspection_date > last_12_months:
            return self.screening_profile.\
                ship_last_inspection_detained_severity

        last_24_months = state.created.date() - timedelta(days=730)
        if not inspection.inspection_date > last_24_months:
            return self.screening_profile.\
                ship_detained_in_over_24_months_severity

        state.detained_last_24_months_count += 1

        last_12_months = state.created.date() - timedelta(days=365)
        if inspection.inspection_date > last_12_months:
            state.detained_last_12_months_count += 1
            if inspection.authority in critical_authorities:
                state.detained_last_12_months_critical_authorities_count += 1

        if state.detained_last_12_months_critical_authorities_count >= 1:
            return self.screening_profile.\
                ship_1_or_more_detained_in_12_months_ca_severity

        if state.detained_last_12_months_count >= 2:
            return self.screening_profile.\
                ship_2_or_more_detained_in_12_months_severity

        if state.detained_last_12_months_count >= 1:
            return self.screening_profile.\
                ship_1_or_more_detained_in_12_months_severity

        if state.detained_last_24_months_count >= 2:
            return self.screening_profile.\
                ship_2_or_more_detained_in_24_months_severity

        return self.screening_profile.ship_once_detained_in_24_months_severity

    def _get_deficiency_severity(self, inspection: ShipInspection) -> Severity:
        if inspection.deficiency:
            return self.screening_profile.ship_deficiency_severity

        return Severity.OK
