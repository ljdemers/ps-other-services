"""Screening Workers company sanctions reports makers module"""
from typing import List

from screening_api.company_associations.models import CompanyAssociation
from screening_api.sanctions.models import ComplianceEntitySanction
from screening_api.ships.enums import ShipAssociateType
from screening_api.screenings.enums import Severity

from screening_workers.lib.screening.providers import DataProvider
from screening_workers.lib.screening.reports.makers import CheckReportMaker

from screening_workers.company_sanctions.reports.models import (
    ShipAssociatedCompanyReport, CompanySanctionReport,
    ShipCompanyAssociatesReport, ShipCompanyAssociateReport,
)
from screening_workers.screenings_profiles.models import (
    DefaultScreeningProfile as ScreeningProfile,
)


class ShipAssociatedCompanyReportMaker(CheckReportMaker):

    def __init__(
            self,
            screening_profile: ScreeningProfile,
            associate_type: ShipAssociateType,
    ):
        self.screening_profile = screening_profile
        self.associate_type = associate_type
        self.company_sanction_report_maker = CompanySanctionReportMaker(
            screening_profile)

    def make_report(
            self, data_provider: DataProvider) -> ShipAssociatedCompanyReport:
        company = data_provider.company
        report_sanctions = self._get_sanctions(data_provider.sanctions)
        return ShipAssociatedCompanyReport(
            company_name=company and company.name,
            sanctions=report_sanctions,
        )

    def _get_sanctions(
            self,
            sanctions: List[ComplianceEntitySanction],
    ) -> List[CompanySanctionReport]:
        return list(map(self._get_sanction_report, sanctions))

    def _get_sanction_report(
            self,
            sanction: ComplianceEntitySanction,
    ) -> CompanySanctionReport:
        return self.company_sanction_report_maker.make_report(sanction)


class ShipCompanyAssociatesReportMaker(CheckReportMaker):

    def __init__(self, screening_profile: ScreeningProfile):
        self.screening_profile = screening_profile
        self.company_associate_report_maker = ShipCompanyAssociateReportMaker(
            screening_profile)

    def make_report(
            self, data_provider: DataProvider) -> ShipCompanyAssociatesReport:
        associates_reports = self._get_associates(
            data_provider.associations)
        return ShipCompanyAssociatesReport(
            associates=associates_reports,
        )

    def _get_associates(
            self,
            associations: List[CompanyAssociation],
    ) -> List[ShipCompanyAssociateReport]:
        return list(map(self._get_associates_report, associations))

    def _get_associates_report(
            self,
            association: CompanyAssociation,
    ) -> ShipCompanyAssociateReport:
        return self.company_associate_report_maker.make_report(association)


class ShipCompanyAssociateReportMaker:

    def __init__(self, screening_profile: ScreeningProfile):
        self.screening_profile = screening_profile
        self.company_sanction_report_maker = CompanySanctionReportMaker(
            screening_profile)

    def make_report(
            self,
            association: CompanyAssociation,
    ) -> ShipCompanyAssociateReport:
        sanctions = self._get_sanctions(association.dst.entity_sanctions)
        dst_type = association.dst.entity_type.name.lower()
        return ShipCompanyAssociateReport(
            company_name=association.src.name,
            relationship=association.relationship,
            dst_type=dst_type,
            dst_name=association.dst.name,
            sanctions=sanctions,
        )

    def _get_sanctions(
            self,
            sanctions: List[ComplianceEntitySanction],
    ) -> List[CompanySanctionReport]:
        return list(map(self._get_sanction_report, sanctions))

    def _get_sanction_report(
            self,
            sanction: ComplianceEntitySanction,
    ) -> CompanySanctionReport:
        return self.company_sanction_report_maker.make_report(sanction)


class CompanySanctionReportMaker:

    def __init__(self, screening_profile: ScreeningProfile):
        self.screening_profile = screening_profile

    def make_report(
            self,
            sanction: ComplianceEntitySanction,
    ) -> CompanySanctionReport:
        severity = self._get_severity(sanction)
        return CompanySanctionReport(
            sanction_name=sanction.compliance_sanction.sanction_list_name,
            listed_since=sanction.start_date,
            listed_to=sanction.end_date,
            sanction_severity=severity,
        )

    def _get_severity(self, sanction: ComplianceEntitySanction) -> Severity:
        if not sanction.is_active:
            return Severity.OK

        return self.screening_profile.company_active_sanction_severity
