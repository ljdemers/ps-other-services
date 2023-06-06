"""Screening Workers company sanctions checks module"""
from typing import List

from screening_api.screenings.models import Screening
from screening_api.screenings.repositories import ScreeningsRepository
from screening_api.screenings_reports.repositories import (
    ScreeningsReportsRepository,
)
from screening_api.ships.enums import ShipAssociateType
from screening_api.ships.models import Ship

from screening_workers.lib.screening.checks import ReportCheck
from screening_workers.lib.screening.providers import DataProvider
from screening_workers.lib.compliance_api.cache.collections import (
    CompanySanctionsCollection, CompanyAssociationsCollection,
)
from screening_workers.lib.sis_api.cache.collections import ShipsCollection
from screening_workers.company_sanctions.reports.makers import (
    ShipAssociatedCompanyReportMaker, ShipCompanyAssociatesReportMaker,
)
from screening_workers.company_sanctions.reports.models import (
    ShipAssociatedCompanyReport,
)


class BaseAssociateCompanyCheck(ReportCheck):

    associate_type = NotImplemented

    def __init__(
            self,
            screenings_repository: ScreeningsRepository,
            screenings_reports_repository: ScreeningsReportsRepository,
            ships_collection: ShipsCollection,
            company_sanctions_collection: CompanySanctionsCollection,
    ):
        super().__init__(screenings_repository, screenings_reports_repository)
        self.company_sanctions_collection = company_sanctions_collection
        self.ships_collection = ships_collection

    def get_data_provider(self, screening: Screening) -> DataProvider:
        data_provider = super(BaseAssociateCompanyCheck, self).\
            get_data_provider(screening)

        ship = self._get_ship(screening.ship_id)
        self.ships_collection.refresh(screening.ship_id)

        company = self._get_company(ship)
        if company:
            self.company_sanctions_collection.refresh(company.id)

        sanctions = self._find_sanctions(
            screening.ship_id,
            data_provider.screening_profile.blacklisted_sanction_list_id,
        )

        data_provider.update(
            ship=ship,
            company=company,
            sanctions=sanctions,
        )

        return data_provider

    def make_report(
            self, data_provider: DataProvider) -> ShipAssociatedCompanyReport:
        return ShipAssociatedCompanyReportMaker(
            data_provider.screening_profile, self.associate_type,
        ).make_report(data_provider)

    def _get_ship(self, ship_id: int) -> Ship:
        company_field = Ship.get_company_field_name(self.associate_type)
        return self.ships_collection.get(
            ship_id, joinedload_related=[company_field, ])

    def _get_company(self, ship: Ship):
        return ship.get_company(self.associate_type)

    def _find_sanctions(
            self, ship_id: int, blacklisted_sanction_list_id: int = None):
        return self.company_sanctions_collection.query(
            ship_id, self.associate_type, blacklisted_sanction_list_id,
        )


class ShipRegisteredOwnerCompanyCheck(BaseAssociateCompanyCheck):

    name = 'ship_registered_owner_company'
    associate_type = ShipAssociateType.REGISTERED_OWNER


class ShipOperatorCompanyCheck(BaseAssociateCompanyCheck):

    name = 'ship_operator_company'
    associate_type = ShipAssociateType.OPERATOR


class ShipBeneficialOwnerCompanyCheck(BaseAssociateCompanyCheck):

    name = 'ship_beneficial_owner_company'
    associate_type = ShipAssociateType.GROUP_BENEFICIAL_OWNER


class ShipManagerCompanyCheck(BaseAssociateCompanyCheck):

    name = 'ship_manager_company'
    associate_type = ShipAssociateType.SHIP_MANAGER


class ShipTechnicalManagerCompanyCheck(BaseAssociateCompanyCheck):

    name = 'ship_technical_manager_company'
    associate_type = ShipAssociateType.TECHNICAL_MANAGER


class ShipCompanyAssociatesCheck(ReportCheck):

    name = 'ship_company_associates'

    def __init__(
            self,
            screenings_repository: ScreeningsRepository,
            screenings_reports_repository: ScreeningsReportsRepository,
            ships_collection: ShipsCollection,
            company_associations_collection: CompanyAssociationsCollection,
    ):
        super().__init__(screenings_repository, screenings_reports_repository)
        self.company_associations_collection = company_associations_collection
        self.ships_collection = ships_collection

    def get_data_provider(self, screening: Screening) -> DataProvider:
        data_provider = super(ShipCompanyAssociatesCheck, self).\
            get_data_provider(screening)
        ship = self._get_ship(screening.ship_id)
        company_ids = ship.get_company_ids()

        company_ids_fitlered = list(filter(None, company_ids))

        associations = self._find_associations(company_ids_fitlered)

        data_provider.update(
            ship=ship,
            associations=associations,
        )

        return data_provider

    def make_report(
            self, data_provider: DataProvider) -> ShipAssociatedCompanyReport:
        return ShipCompanyAssociatesReportMaker(
            data_provider.screening_profile,
        ).make_report(data_provider)

    def _get_ship(self, ship_id: int):
        return self.ships_collection.get(ship_id)

    def _find_associations(self, company_ids: List[int]):
        return self.company_associations_collection.query(company_ids)
