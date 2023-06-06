"""Screening workers ships creators module"""
from typing import Tuple

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.scoping import scoped_session
from sqlalchemy.orm.session import Session

from screening_api.companies.models import SISCompany
from screening_api.companies.repositories import SISCompaniesRepository
from screening_api.ships.enums import ShipAssociateType
from screening_api.ships.models import Ship
from screening_api.ships.repositories import ShipsRepository

from screening_workers.lib.sis_api.models import Ship as SISShip
from screening_workers.ships.dataclasses import ShipData


class ShipsUpserter:

    def __init__(
            self,
            ships_repository: ShipsRepository,
            companies_repository: SISCompaniesRepository,
            session_factory: scoped_session):
        self.ships_repository = ships_repository
        self.companies_repository = companies_repository
        self.session_factory = session_factory

    def get_session(self) -> Session:
        return self.session_factory()

    def upsert(self, ship_data: SISShip, session: Session = None) -> Ship:
        if session is None:
            session = self.get_session()

        imo_id = int(ship_data.imo_id)

        data = ShipData({
            'imo': ship_data.imo_id,
            'mmsi': ship_data.mmsi,
            'type': ship_data.shiptype_level_5,
            'name': ship_data.ship_name,
            'country_id': ship_data.flag.iso_3166_1_alpha_2,
            'country_name': ship_data.flag.name,

            'country_effective_date': ship_data.country_effective_date,

            'call_sign': ship_data.call_sign,
            'status': ship_data.status,
            'port_of_registry': ship_data.port_of_registry,
            'classification_society': ship_data.classification_society,
            'deadweight': ship_data.deadweight,
            'breadth': ship_data.breadth,
            'displacement': ship_data.displacement,
            'draught': ship_data.draught,
            'build_country_name': ship_data.build_country_name,
            'build_year': ship_data.build_year,
            'shipbuilder': ship_data.shipbuilder,
            'pandi_club': ship_data.pandi_club,
            'weight': ship_data.weight,
            'length': ship_data.length,

            'safety_management_certificate_doc_company':
                ship_data.safety_management_certificate_doc_company,
            'safety_management_certificate_date_issued':
                ship_data.safety_management_certificate_date_issued,

            'registered_owner':
                ship_data.registered_owner,
            'registered_owner_company_code': ship_data.registered_owner_code,
            'registered_owner_country_of_domicile':
                ship_data.registered_owner_country_of_domicile,
            'registered_owner_country_of_control':
                ship_data.registered_owner_country_of_control,
            'registered_owner_country_of_registration':
                ship_data.registered_owner_country_of_registration,
            'operator':
                ship_data.operator,
            'operator_company_code': ship_data.operator_company_code,
            'operator_country_of_domicile':
                ship_data.operator_country_of_domicile_name,
            'operator_country_of_control':
                ship_data.operator_country_of_control,
            'operator_country_of_registration':
                ship_data.operator_country_of_registration,
            'group_beneficial_owner':
                ship_data.group_beneficial_owner,
            'group_beneficial_owner_company_code':
                ship_data.group_beneficial_owner_company_code,
            'group_beneficial_owner_country_of_domicile':
                ship_data.group_beneficial_owner_country_of_domicile,
            'group_beneficial_owner_country_of_control':
                ship_data.group_beneficial_owner_country_of_control,
            'group_beneficial_owner_country_of_registration':
                ship_data.group_beneficial_owner_country_of_registration,
            'ship_manager':
                ship_data.ship_manager,
            'ship_manager_company_code': ship_data.ship_manager_company_code,
            'ship_manager_country_of_domicile':
                ship_data.ship_manager_country_of_domicile_name,
            'ship_manager_country_of_control':
                ship_data.ship_manager_country_of_control,
            'ship_manager_country_of_registration':
                ship_data.ship_manager_country_of_registration,
            'technical_manager':
                ship_data.technical_manager,
            'technical_manager_company_code': ship_data.technical_manager_code,
            'technical_manager_country_of_domicile':
                ship_data.technical_manager_country_of_domicile,
            'technical_manager_country_of_control':
                ship_data.technical_manager_country_of_control,
            'technical_manager_country_of_registration':
                ship_data.technical_manager_country_of_registration,
        })

        for associate_type in ShipAssociateType.__members__.values():
            company_code = data.get_company_code(associate_type)
            company_name = data.get_company_name(associate_type)
            if not company_code:
                continue
            company, _ = self._get_or_create_company(
                company_code, company_name, session=session)
            data.set_company_id(associate_type, company.id)

        return self.ships_repository.update_or_create(
            imo_id, **data, session=session)

    def _get_or_create_company(
        self, sis_code: str, name: str, session: Session,
    ) -> Tuple[SISCompany, bool]:
        # we don't use optimistic pattern coz of used lock
        company = self.companies_repository.get_or_none(
            sis_code=sis_code, session=session)

        if company is not None:
            return company, False

        data = {
            'sis_code': sis_code,
            'name': name,
        }
        try:
            company = self.companies_repository.create(**data, session=session)
            return company, True
        # inspection already exists
        except IntegrityError:
            company = self.companies_repository.get_or_none(
                sis_code=sis_code, session=session)
            return company, False
