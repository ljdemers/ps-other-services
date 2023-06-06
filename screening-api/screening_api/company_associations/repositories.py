"""Screening API company associations repositories module"""
from typing import List

from sqlalchemy.orm import joinedload

from screening_api.lib.alchemy.repositories import AlchemyRepository
from screening_api.companies.models import (
    SISComplianceAssociation, SISCompany,
)
from screening_api.company_associations.models import CompanyAssociation
from screening_api.entities.models import ComplianceEntity
from screening_api.ships.enums import ShipAssociateType
from screening_api.ships.models import Ship


class CompanyAssociationsRepository(AlchemyRepository):

    model = CompanyAssociation

    def find_associations(
            self, ship_id: int, associate_type: ShipAssociateType, **kwargs):
        query = self._filter_query(**kwargs)

        ship_field_name = Ship.get_company_id_field_name(associate_type)
        ship_field = getattr(Ship, ship_field_name)

        query = query.join(
            ComplianceEntity,
            ComplianceEntity.id == self.model.src_id,
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

        return query.all()

    def find_all_associations(self, sis_company_ids: List[int], **kwargs):
        query = self._filter_query(**kwargs)

        query = query.distinct().join(
            self.model.src, aliased=True,
        ).join(
            self.model.dst, aliased=True, from_joinpoint=True,
        ).join(
            ComplianceEntity,
            ComplianceEntity.id == self.model.src_id,
        ).options(
            joinedload(self.model.src, innerjoin=True),
            joinedload(self.model.dst, innerjoin=True),
        ).outerjoin(
            SISComplianceAssociation,
            SISComplianceAssociation.compliance_entity_id ==
            ComplianceEntity.id,
        ).outerjoin(
            SISCompany,
            SISCompany.id == SISComplianceAssociation.sis_company_id,
        ).filter(SISCompany.id.in_(sis_company_ids))

        return query.all()
