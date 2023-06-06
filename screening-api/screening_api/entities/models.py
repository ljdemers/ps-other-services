"""Screening API entities models module"""
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.schema import Column
from sqlalchemy.types import Integer, String, Enum

from screening_api.models import BaseModel
from screening_api.companies.models import SISComplianceAssociation
from screening_api.entities.enums import EntityType


class ComplianceEntity(BaseModel):

    __tablename__ = 'compliance_entities'

    compliance_id = Column(Integer, nullable=False, unique=True)
    entity_type = Column(
        Enum(EntityType), default=EntityType.ORGANISATION,
        nullable=False,
    )
    name = Column(String)

    sis_company_ids = association_proxy(
        "associations", "sis_company_id",
        creator=lambda id: SISComplianceAssociation(sis_company_id=id))
