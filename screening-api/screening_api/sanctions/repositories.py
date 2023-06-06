"""Screening API sanctions repositories module"""
from screening_api.lib.alchemy.repositories import AlchemyRepository
from screening_api.blacklisted_sanctions.models import (
    BlacklistedSanctionListItem,
)
from screening_api.companies.models import SISCompany, SISComplianceAssociation
from screening_api.entities.models import ComplianceEntity
from screening_api.sanctions.models import (
    ComplianceEntitySanction, ComplianceSanction,
)
from screening_api.ships.enums import ShipAssociateType
from screening_api.ships.models import Ship


class ComplianceEntitySanctionsRepository(AlchemyRepository):

    model = ComplianceEntitySanction

    def find_sanctions(
            self, ship_id: int, associate_type: ShipAssociateType,
            blacklisted_sanction_list_id: int = None,
            **options,
    ):
        session = options.pop('session', None)
        if session is None:
            session = self.get_session()

        query = self._find_query(session=session, **options)

        ship_field_name = Ship.get_company_id_field_name(associate_type)
        ship_field = getattr(Ship, ship_field_name)

        query = query.join(
            ComplianceEntity,
            ComplianceEntity.id ==
            ComplianceEntitySanction.compliance_entity_id,
        ).outerjoin(
            SISComplianceAssociation,
            SISComplianceAssociation.compliance_entity_id ==
            ComplianceEntity.id,
        ).outerjoin(
            SISCompany,
            SISCompany.id == SISComplianceAssociation.sis_company_id,
        ).join(
            Ship, ship_field == SISCompany.id,
        ).filter_by(id=ship_id)

        if blacklisted_sanction_list_id is not None:
            query = query.join(
                ComplianceSanction,
                ComplianceSanction.id == self.model.compliance_sanction_id,
            )
            blacklisted_subquery = session.query(
                BlacklistedSanctionListItem.sanction_code,
            ).filter(
                BlacklistedSanctionListItem.blacklisted_sanction_list_id ==
                blacklisted_sanction_list_id,
            )
            query = query.filter(
                ~ComplianceSanction.code.in_(blacklisted_subquery),
            )

        return query.all()


class ComplianceSanctionsRepository(AlchemyRepository):

    model = ComplianceSanction

    def find_sanctions(
            self, ship_id: int, associate_type: ShipAssociateType,
            blacklisted_sanction_list_id: int = None,
    ):
        session = self.get_session()

        ship_field_name = Ship.get_company_id_field_name(associate_type)
        ship_field = getattr(Ship, ship_field_name)

        query = session.query(self.model).join(
            ComplianceEntitySanction,
            ComplianceEntitySanction.compliance_sanction_id == self.model.id,
        ).join(
            ComplianceEntity,
            ComplianceEntity.id ==
            ComplianceEntitySanction.compliance_entity_id,
        ).outerjoin(
            SISComplianceAssociation,
            SISComplianceAssociation.compliance_entity_id ==
            ComplianceEntity.id,
        ).outerjoin(
            SISCompany,
            SISCompany.id == SISComplianceAssociation.sis_company_id,
        ).join(
            Ship, ship_field == SISCompany.id,
        ).filter_by(id=ship_id)

        if blacklisted_sanction_list_id is not None:
            blacklisted_subquery = session.query(
                BlacklistedSanctionListItem.sanction_code,
            ).filter(
                BlacklistedSanctionListItem.blacklisted_sanction_list_id ==
                blacklisted_sanction_list_id,
            )
            query = query.filter(~self.model.code.in_(blacklisted_subquery))

        return query.all()
